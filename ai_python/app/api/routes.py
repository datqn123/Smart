"""Task004 API routes: invoke + SSE stream."""

from __future__ import annotations

import json
from typing import Any

import jwt
from fastapi import APIRouter, Depends, Header
from fastapi.responses import StreamingResponse

from app.api.auth import JwtValidator, get_jwt_validator
from app.api.errors import ApiError
from app.api.runtime import GraphRuntime, get_graph_runtime
from app.api.schemas import ChatRequest, ErrorEnvelope, ErrorObject, InvokeResponse, InvokeUsage, StreamEvent

router = APIRouter(prefix="/api/v1/ai/chat", tags=["ai-chat"])


def _sse_data(event: StreamEvent) -> str:
    payload = event.model_dump(exclude_none=True)
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _extract_partial_update(chunk: Any) -> dict[str, Any]:
    if isinstance(chunk, dict):
        flat: dict[str, Any] = {}
        for value in chunk.values():
            if isinstance(value, dict):
                flat.update(value)
        if flat:
            return flat
        return chunk
    return {"data": str(chunk)}


def _validate_auth(
    authorization: str | None = Header(default=None, alias="Authorization"),
    validator: JwtValidator = Depends(get_jwt_validator),
) -> dict[str, Any]:
    try:
        return validator.validate_authorization_header(authorization)
    except (ValueError, jwt.InvalidTokenError) as exc:
        raise ApiError(
            status_code=401,
            code="AI_AUTH_INVALID",
            message=str(exc),
        ) from exc


@router.post("/invoke", response_model=InvokeResponse)
def invoke_chat(
    request: ChatRequest,
    correlation_id: str = Header(alias="X-Correlation-Id"),
    _claims: dict[str, Any] = Depends(_validate_auth),
    runtime: GraphRuntime = Depends(get_graph_runtime),
) -> InvokeResponse:
    try:
        out = runtime.invoke(request, correlation_id=correlation_id)
    except Exception as exc:  # noqa: BLE001
        raise ApiError(
            status_code=500,
            code="AI_RUNTIME_ERROR",
            message="Graph invoke failed.",
            details={"error": str(exc)},
            correlation_id=correlation_id,
        ) from exc

    return InvokeResponse(
        correlation_id=correlation_id,
        thread_id=request.metadata.thread_id,
        intent=out.get("intent"),
        final_answer=out.get("final_answer"),
        usage=InvokeUsage(),
        error=None,
    )


@router.post("/stream")
async def stream_chat(
    request: ChatRequest,
    correlation_id: str = Header(alias="X-Correlation-Id"),
    _claims: dict[str, Any] = Depends(_validate_auth),
    runtime: GraphRuntime = Depends(get_graph_runtime),
) -> StreamingResponse:
    async def event_gen():
        final_answer: str | None = None
        final_error: dict[str, Any] | None = None
        try:
            for chunk in runtime.stream(request, correlation_id=correlation_id):
                update = _extract_partial_update(chunk)
                if "final_answer" in update and update["final_answer"]:
                    final_answer = str(update["final_answer"])
                if "error_payload" in update and isinstance(update["error_payload"], dict):
                    final_error = update["error_payload"]

                yield _sse_data(
                    StreamEvent(
                        correlation_id=correlation_id,
                        event_type="partial_answer",
                        data=update,
                        is_terminal=False,
                    ),
                )
        except Exception as exc:  # noqa: BLE001
            final_error = {"code": "AI_RUNTIME_ERROR", "message": str(exc)}

        if final_error:
            envelope = ErrorEnvelope(
                correlation_id=correlation_id,
                error=ErrorObject(
                    code=str(final_error.get("code") or final_error.get("error") or "AI_RUNTIME_ERROR"),
                    message=str(final_error.get("message") or "Stream execution failed."),
                    details=final_error,
                ),
            )
            yield _sse_data(
                StreamEvent(
                    correlation_id=correlation_id,
                    event_type="error",
                    data=envelope.model_dump(exclude_none=True),
                    is_terminal=True,
                ),
            )
            return

        yield _sse_data(
            StreamEvent(
                correlation_id=correlation_id,
                event_type="final_answer",
                data=final_answer or "",
                is_terminal=True,
            ),
        )

    return StreamingResponse(event_gen(), media_type="text/event-stream")
