"""Task004 API routes: invoke + SSE stream."""

from __future__ import annotations

import json
from typing import Any

import jwt
from fastapi import APIRouter, Depends, Header
from fastapi.responses import StreamingResponse

from app.api.auth import JwtValidator, derive_identity_context, get_jwt_validator
from app.api.errors import ApiError
from app.api.runtime import GraphRuntime, get_graph_runtime
from app.api.schemas import ChatRequest, InvokeResponse, InvokeUsage

router = APIRouter(prefix="/api/v1/ai/chat", tags=["ai-chat"])


def _sse_ui_event(name: str, data: str) -> str:
    """Named SSE for FE + Spring relay (event: delta | done | error)."""
    safe = data.replace("\r\n", "\n").replace("\r", "\n")
    lines = [f"event: {name}"]
    for part in safe.split("\n"):
        lines.append(f"data: {part}")
    lines.append("")
    return "\n".join(lines) + "\n"


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


def _enforce_identity_context(
    request: ChatRequest,
    claims: dict[str, Any],
    *,
    correlation_id: str,
) -> None:
    if claims.get("auth_dev_bypass"):
        return

    try:
        claim_user_id, claim_tenant_id = derive_identity_context(claims)
    except ValueError as exc:
        raise ApiError(
            status_code=401,
            code="AI_AUTH_INVALID",
            message=str(exc),
            correlation_id=correlation_id,
        ) from exc

    if (
        request.metadata.user_id != claim_user_id
        or request.metadata.tenant_id != claim_tenant_id
    ):
        raise ApiError(
            status_code=403,
            code="AI_AUTH_FORBIDDEN",
            message="JWT claims do not match request metadata.",
            details={
                "request_user_id": request.metadata.user_id,
                "request_tenant_id": request.metadata.tenant_id,
                "claim_user_id": claim_user_id,
                "claim_tenant_id": claim_tenant_id,
            },
            correlation_id=correlation_id,
        )

    request.metadata.user_id = claim_user_id
    request.metadata.tenant_id = claim_tenant_id


@router.post("/invoke", response_model=InvokeResponse)
def invoke_chat(
    request: ChatRequest,
    correlation_id: str = Header(alias="X-Correlation-Id"),
    claims: dict[str, Any] = Depends(_validate_auth),
    runtime: GraphRuntime = Depends(get_graph_runtime),
) -> InvokeResponse:
    _enforce_identity_context(request, claims, correlation_id=correlation_id)
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
        chart_spec=out.get("chart_spec_final"),
        usage=InvokeUsage(),
        error=None,
    )


def _sse_user_facing_error(final_error: dict[str, Any]) -> str:
    """Map graph error codes to end-user text (Vietnamese)."""
    code = final_error.get("error")
    if code == "max_sql_attempts":
        return (
            "Không thể hoàn tất truy vấn sau nhiều lần thử. "
            "Có thể do SQL không hợp lệ, dịch vụ thực thi SQL (Spring/DB) lỗi, hoặc dữ liệu không đủ. "
            "Xem log server Python (ai_python) để biết chi tiết."
        )
    if code == "schema_load_failed":
        return (
            "Không tải được mô tả schema từ cơ sở dữ liệu (registry + catalog). "
            "Kiểm tra DATABASE_URL_RO / DATABASE_URL_METADATA_RO, bảng ai_table_description, "
            "và log server Python (ai_python)."
        )
    msg = final_error.get("message")
    if msg is not None:
        return str(msg)
    if code is not None:
        return str(code)
    return "Stream execution failed."


@router.post("/stream")
async def stream_chat(
    request: ChatRequest,
    correlation_id: str = Header(alias="X-Correlation-Id"),
    authorization: str | None = Header(default=None, alias="Authorization"),
    claims: dict[str, Any] = Depends(_validate_auth),
    runtime: GraphRuntime = Depends(get_graph_runtime),
) -> StreamingResponse:
    _enforce_identity_context(request, claims, correlation_id=correlation_id)

    async def event_gen():
        prev_answer = ""
        chart_sent = False
        draft_sent = False
        bearer = authorization
        final_error: dict[str, Any] | None = None
        try:
            for chunk in runtime.stream(
                request,
                correlation_id=correlation_id,
                bearer_token=bearer,
            ):
                update = _extract_partial_update(chunk)
                spec = update.get("chart_spec_final")
                if not chart_sent and isinstance(spec, dict) and spec:
                    try:
                        payload = json.dumps(spec, ensure_ascii=False)
                    except (TypeError, ValueError):
                        payload = "{}"
                    yield _sse_ui_event("chart", payload)
                    chart_sent = True
                draft_spec = update.get("catalog_draft_sse")
                if not draft_sent and isinstance(draft_spec, dict) and draft_spec:
                    try:
                        draft_payload = json.dumps(draft_spec, ensure_ascii=False)
                    except (TypeError, ValueError):
                        draft_payload = "{}"
                    yield _sse_ui_event("draft", draft_payload)
                    draft_sent = True
                if "final_answer" in update and update["final_answer"]:
                    current = str(update["final_answer"])
                    if current.startswith(prev_answer) and len(current) > len(prev_answer):
                        delta = current[len(prev_answer) :]
                        if delta:
                            yield _sse_ui_event("delta", delta)
                        prev_answer = current
                    elif current != prev_answer:
                        yield _sse_ui_event("delta", current)
                        prev_answer = current
                if "error_payload" in update and isinstance(update["error_payload"], dict):
                    final_error = update["error_payload"]
        except Exception as exc:  # noqa: BLE001
            final_error = {
                "code": "AI_RUNTIME_ERROR",
                "message": str(exc) or f"{type(exc).__name__}",
            }

        if final_error:
            yield _sse_ui_event("error", _sse_user_facing_error(final_error))
            yield _sse_ui_event("done", "")
            return

        yield _sse_ui_event("done", "")

    return StreamingResponse(event_gen(), media_type="text/event-stream")
