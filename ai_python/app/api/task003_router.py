from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
from starlette.responses import StreamingResponse

router = APIRouter(tags=["task003"])


class Task003TurnBody(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    correlation_id: str | None = Field(default=None)


@router.post("/v1/task003/stream")
async def task003_stream_sse(request: Request, body: Task003TurnBody) -> StreamingResponse:
    orch = request.app.state.task003_orch

    async def gen() -> AsyncIterator[str]:
        async for chunk in orch.stream_turn(
            message=body.message, correlation_id=body.correlation_id
        ):
            yield chunk

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
