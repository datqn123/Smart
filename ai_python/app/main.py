from collections.abc import AsyncIterator

from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse

from .smart_erp_mcp.agent_turn import stream_final_answer

app = FastAPI(title="ai_python", version="0.1.0")


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
async def chat_stream(q: str = Query(min_length=1, max_length=4000)) -> StreamingResponse:
    async def gen() -> AsyncIterator[str]:
        try:
            async for delta in stream_final_answer(q):
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
