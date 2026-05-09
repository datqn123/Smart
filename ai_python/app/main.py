import os
from collections.abc import AsyncGenerator, AsyncIterator, Callable, Iterator
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse

from . import mkp_async
from .agents.orchestrator import Task003Orchestrator
from .api.task003_router import router as task003_router
from .mcp.in_memory_clients import ScriptedDbReadonlyMcp, ScriptedVectorRagMcp
from .mkp_client import stream_chat_deltas

load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=False)


def _mk_stream_fn() -> Callable[[str], AsyncGenerator[str, None]]:
    async def synth(prompt: str) -> AsyncGenerator[str, None]:
        stub = os.getenv("TASK003_SYNTH_STUB", "").strip().lower() in ("1", "true", "yes")
        if stub:
            yield "[task003-stub-response]"
            return
        async for d in mkp_async.stream_chat_deltas_async(prompt):
            yield d

    return synth


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    rag = ScriptedVectorRagMcp()
    db = ScriptedDbReadonlyMcp(reject=os.getenv("TASK003_DB_REJECT", "").lower() == "true")
    app.state.task003_orch = Task003Orchestrator(
        rag=rag,
        db=db,
        stream_fn=_mk_stream_fn(),
    )
    yield


app = FastAPI(title="ai_python", version="0.2.0", lifespan=lifespan)
app.include_router(task003_router)


def _sse_event(event: str, data: str) -> str:
    # SSE format: event + data + blank line
    # Note: data MUST NOT contain bare CR; split on newlines into multiple data: lines.
    lines = data.splitlines() or [""]
    payload = [f"event: {event}"]
    payload.extend([f"data: {line}" for line in lines])
    payload.append("")
    return "\n".join(payload) + "\n"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/chat/stream")
def chat_stream(q: str = Query(min_length=1, max_length=4000)) -> StreamingResponse:
    def gen() -> Iterator[str]:
        try:
            for delta in stream_chat_deltas(q):
                yield _sse_event("delta", delta)
            yield _sse_event("done", "[DONE]")
        except Exception as e:
            yield _sse_event("error", str(e))

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            # Nginx: disable proxy buffering (harmless if not behind nginx)
            "X-Accel-Buffering": "no",
        },
    )
