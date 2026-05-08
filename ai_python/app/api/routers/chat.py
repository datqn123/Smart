from collections.abc import Iterator

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from app.core.sse import sse_event
from app.tools.stream_chat import stream_chat_tool

router = APIRouter(tags=["chat"])


@router.get("/v1/chat/stream")
def chat_stream(q: str = Query(min_length=1, max_length=4000)) -> StreamingResponse:
    def gen() -> Iterator[str]:
        try:
            for delta in stream_chat_tool(q):
                yield sse_event("delta", delta)
            yield sse_event("done", "[DONE]")
        except Exception as e:
            yield sse_event("error", str(e))

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
