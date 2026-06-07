"""Task004 API routes: invoke + SSE stream."""

from __future__ import annotations

import json
import logging
from typing import Any

import jwt
from fastapi import APIRouter, Depends, File, Form, Header, UploadFile
from fastapi.responses import Response, StreamingResponse

from app.api.auth import JwtValidator, derive_identity_context, get_jwt_validator
from app.api.errors import ApiError
from app.api.runtime import GraphRuntime, get_graph_runtime
from app.graph.correlation import set_correlation_id
from app.api.schemas import (
    ChatRequest,
    InvokeResponse,
    InvokeUsage,
    SynthesizeRequest,
    TranscribeResponse,
)
from app.stt.service import SttService, get_stt_service
from app.tts.service import TtsService, get_tts_service

router = APIRouter(prefix="/api/v1/ai/chat", tags=["ai-chat"])
logger = logging.getLogger(__name__)


def _sse_ui_event(name: str, data: str) -> str:
    """Named SSE for FE + Spring relay (event: delta | done | error)."""
    safe = data.replace("\r\n", "\n").replace("\r", "\n")
    lines = [f"event: {name}"]
    for part in safe.split("\n"):
        lines.append(f"data: {part}")
    lines.append("")
    return "\n".join(lines) + "\n"


def _progress_from_custom_chunk(chunk: Any) -> str | None:
    if not isinstance(chunk, tuple) or len(chunk) != 2:
        return None
    mode, payload = chunk
    if mode != "custom" or not isinstance(payload, dict):
        return None
    raw = payload.get("progress_text") or payload.get("progress")
    return raw if isinstance(raw, str) and raw.strip() else None


def _extract_partial_update(chunk: Any) -> dict[str, Any]:
    if isinstance(chunk, tuple) and len(chunk) == 2:
        mode, payload = chunk
        if mode != "updates":
            return {}
        chunk = payload
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


def should_emit_stream_error(
    final_error: dict[str, Any] | None,
    *,
    streamed_answer: str,
    clarify_sent: bool,
) -> bool:
    """Skip SSE ``error`` when the graph already streamed a user-facing ``final_answer``."""
    if not final_error or clarify_sent:
        return False
    if final_error.get("code") == "AI_RUNTIME_ERROR":
        return True
    if streamed_answer.strip():
        return False
    return True


def _sse_user_facing_error(final_error: dict[str, Any]) -> str:
    """Map graph error codes to end-user text (Vietnamese). Fallback when no final_answer was streamed."""
    code = final_error.get("error") or final_error.get("code")
    if code == "max_sql_attempts":
        from app.graph.answer_fallbacks import SQL_ERROR_VI

        return SQL_ERROR_VI
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


_SSE_STREAM_HEADERS = {
    "Cache-Control": "no-cache, no-transform",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


def _iter_chat_sse_events(
    runtime: GraphRuntime,
    request: ChatRequest,
    *,
    correlation_id: str,
    bearer_token: str | None,
):
    """Sync generator — tránh block event loop (async gen + graph sync = buffer tới khi xong)."""
    prev_answer = ""
    chart_sent = False
    draft_sent = False
    inventory_draft_sent = False
    data_table_sent = False
    clarify_sent = False
    progress_sent = ""
    final_error: dict[str, Any] | None = None
    had_stream_payload = False
    had_custom_payload = False
    suppress_done = False
    set_correlation_id(correlation_id)
    try:
        for chunk in runtime.stream(
            request,
            correlation_id=correlation_id,
            bearer_token=bearer_token,
        ):
            if isinstance(chunk, tuple) and len(chunk) == 2:
                mode, payload = chunk
                if mode == "harness_control" and isinstance(payload, dict):
                    suppress_done = suppress_done or bool(payload.get("suppress_done"))
                    continue
            custom_progress = _progress_from_custom_chunk(chunk)
            if custom_progress and custom_progress != progress_sent:
                yield _sse_ui_event("progress", custom_progress)
                progress_sent = custom_progress
                had_stream_payload = True
                continue
            update = _extract_partial_update(chunk)
            progress = update.get("progress_text")
            if isinstance(progress, str) and progress and progress != progress_sent:
                yield _sse_ui_event("progress", progress)
                progress_sent = progress
                had_stream_payload = True
            clarify_spec = update.get("domain_clarify_sse")
            if not clarify_sent and isinstance(clarify_spec, dict) and clarify_spec:
                try:
                    clarify_payload = json.dumps(clarify_spec, ensure_ascii=False)
                except (TypeError, ValueError):
                    clarify_payload = "{}"
                yield _sse_ui_event("clarify", clarify_payload)
                clarify_sent = True
                had_stream_payload = True
            spec = update.get("chart_spec_final")
            if not chart_sent and isinstance(spec, dict) and spec:
                try:
                    payload = json.dumps(spec, ensure_ascii=False)
                except (TypeError, ValueError):
                    payload = "{}"
                yield _sse_ui_event("chart", payload)
                chart_sent = True
                had_stream_payload = True
            draft_spec = update.get("catalog_draft_sse")
            if not draft_sent and isinstance(draft_spec, dict) and draft_spec:
                try:
                    draft_payload = json.dumps(draft_spec, ensure_ascii=False)
                except (TypeError, ValueError):
                    draft_payload = "{}"
                yield _sse_ui_event("draft", draft_payload)
                draft_sent = True
                had_stream_payload = True
            inv_draft_spec = update.get("inventory_draft_sse")
            if not inventory_draft_sent and isinstance(inv_draft_spec, dict) and inv_draft_spec:
                try:
                    inv_payload = json.dumps(inv_draft_spec, ensure_ascii=False)
                except (TypeError, ValueError):
                    inv_payload = "{}"
                yield _sse_ui_event("inventory_draft", inv_payload)
                inventory_draft_sent = True
                had_stream_payload = True
            table_spec = update.get("query_table_sse")
            if not data_table_sent and isinstance(table_spec, dict) and table_spec:
                try:
                    table_payload = json.dumps(table_spec, ensure_ascii=False)
                except (TypeError, ValueError):
                    table_payload = "{}"
                yield _sse_ui_event("data_table", table_payload)
                data_table_sent = True
                had_stream_payload = True
            if isinstance(chunk, tuple) and len(chunk) == 2:
                mode, payload = chunk
                if mode == "custom" and isinstance(payload, dict) and "final_answer" in payload:
                    had_custom_payload = True
                    current = str(payload["final_answer"])
                    yield _sse_ui_event("delta_full", current)
                    had_stream_payload = True
                    if current.startswith(prev_answer) and len(current) > len(prev_answer):
                        delta = current[len(prev_answer) :]
                        if delta:
                            yield _sse_ui_event("delta", delta)
                            had_stream_payload = True
                        prev_answer = current
                    elif current != prev_answer:
                        yield _sse_ui_event("delta", current)
                        had_stream_payload = True
                        prev_answer = current
                    continue
            if "final_answer" in update and update["final_answer"] and not had_custom_payload:
                current = str(update["final_answer"])
                yield _sse_ui_event("delta_full", current)
                had_stream_payload = True
                if current.startswith(prev_answer) and len(current) > len(prev_answer):
                    delta = current[len(prev_answer) :]
                    if delta:
                        yield _sse_ui_event("delta", delta)
                        had_stream_payload = True
                    prev_answer = current
                elif current != prev_answer:
                    yield _sse_ui_event("delta", current)
                    had_stream_payload = True
                    prev_answer = current
            if "error_payload" in update and isinstance(update["error_payload"], dict):
                final_error = update["error_payload"]
    except Exception as exc:  # noqa: BLE001
        if had_stream_payload:
            logger.warning(
                "stream ended with exception after partial output: %s",
                exc,
                exc_info=True,
            )
        else:
            final_error = {
                "code": "AI_RUNTIME_ERROR",
                "message": str(exc) or f"{type(exc).__name__}",
            }

    if should_emit_stream_error(
        final_error,
        streamed_answer=prev_answer,
        clarify_sent=clarify_sent,
    ):
        yield _sse_ui_event("error", _sse_user_facing_error(final_error))
    if not suppress_done or final_error is not None:
        yield _sse_ui_event("done", "")


@router.post("/stream")
async def stream_chat(
    request: ChatRequest,
    correlation_id: str = Header(alias="X-Correlation-Id"),
    authorization: str | None = Header(default=None, alias="Authorization"),
    claims: dict[str, Any] = Depends(_validate_auth),
    runtime: GraphRuntime = Depends(get_graph_runtime),
) -> StreamingResponse:
    _enforce_identity_context(request, claims, correlation_id=correlation_id)

    return StreamingResponse(
        _iter_chat_sse_events(
            runtime,
            request,
            correlation_id=correlation_id,
            bearer_token=authorization,
        ),
        media_type="text/event-stream",
        headers=_SSE_STREAM_HEADERS,
    )


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str | None = Form(default=None),
    correlation_id: str = Header(alias="X-Correlation-Id"),
    claims: dict[str, Any] = Depends(_validate_auth),  # noqa: ARG001
    stt: SttService = Depends(get_stt_service),
) -> TranscribeResponse:
    if not stt.available:
        raise ApiError(
            status_code=503,
            code="AI_STT_UNAVAILABLE",
            message="Dịch vụ chuyển giọng thành văn bản tạm thời không khả dụng.",
            correlation_id=correlation_id,
        )

    filename = (file.filename or "recording.wav").strip() or "recording.wav"
    audio_bytes = await file.read()
    lang = (language or "").strip() or None

    try:
        transcript = stt.transcribe(
            audio_bytes,
            filename=filename,
            content_type=file.content_type,
            language=lang,
        )
    except ValueError as exc:
        raise ApiError(
            status_code=400,
            code="AI_STT_VALIDATION",
            message=str(exc),
            correlation_id=correlation_id,
        ) from exc
    except RuntimeError as exc:
        raise ApiError(
            status_code=502,
            code="AI_STT_GATEWAY_ERROR",
            message="Dịch vụ chuyển giọng thành văn bản tạm thời không khả dụng.",
            details={"error": str(exc)},
            correlation_id=correlation_id,
        ) from exc

    return TranscribeResponse(
        correlation_id=correlation_id,
        transcript=transcript,
        language=lang or stt.default_language,
        error=None,
    )


@router.post("/synthesize")
async def synthesize_speech(
    body: SynthesizeRequest,
    correlation_id: str = Header(alias="X-Correlation-Id"),
    claims: dict[str, Any] = Depends(_validate_auth),  # noqa: ARG001
    tts: TtsService = Depends(get_tts_service),
) -> Response:
    if not tts.available:
        raise ApiError(
            status_code=503,
            code="AI_TTS_UNAVAILABLE",
            message="Dịch vụ đọc văn bản tạm thời không khả dụng.",
            correlation_id=correlation_id,
        )

    voice = (body.voice or "").strip() or None
    try:
        audio_bytes = tts.synthesize(body.text, voice=voice)
    except ValueError as exc:
        raise ApiError(
            status_code=400,
            code="AI_TTS_VALIDATION",
            message=str(exc),
            correlation_id=correlation_id,
        ) from exc
    except RuntimeError as exc:
        raise ApiError(
            status_code=502,
            code="AI_TTS_GATEWAY_ERROR",
            message="Dịch vụ đọc văn bản tạm thời không khả dụng.",
            details={"error": str(exc)},
            correlation_id=correlation_id,
        ) from exc

    if not audio_bytes:
        raise ApiError(
            status_code=502,
            code="AI_TTS_EMPTY_AUDIO",
            message="Dịch vụ đọc văn bản trả về dữ liệu rỗng.",
            correlation_id=correlation_id,
        )

    return Response(
        content=audio_bytes,
        media_type="audio/wav",
        headers={"X-Correlation-Id": correlation_id},
    )
