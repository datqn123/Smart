"""Task003 streaming orchestration: graph + MKP token synthesis."""

from __future__ import annotations

import json
import logging
import uuid
from collections.abc import AsyncIterator, Callable
from typing import Any

from ..contracts import DonePayload, McpToolError, UsagePayload
from ..contracts.sse_envelope import sse_error_message_for_mcp
from ..mcp.db_readonly_port import DbReadonlyMcpPort
from ..mcp.vector_rag_port import VectorRagMcpPort
from ..observability import rag_ingest_telemetry_best_effort
from .task003_graph import (
    Task003GraphState,
    build_sse_error_event,
    build_sse_token,
    compile_task003_graph,
    refuse_token_event,
    summarize_public_side_effect,
)

StreamFn = Callable[[str], AsyncIterator[str]]

logger = logging.getLogger(__name__)


def _mk_usage() -> DonePayload:
    return DonePayload(usage=UsagePayload(tokens_in=0, tokens_out=0, cost_usd=0.0))


def _sse_data_line(envelope: dict[str, Any]) -> str:
    raw = json.dumps(envelope, ensure_ascii=False)
    lines = raw.splitlines() or [""]
    parts = [f"data: {ln}" for ln in lines]
    return "\n".join(parts) + "\n\n"


def _build_prompt(state: Task003GraphState) -> str:
    directive = state.get("synthesis_directive") or "grounded"
    msg = state.get("user_message", "").strip()
    rag = state.get("rag_summary") or ""
    db = state.get("db_summary")

    if directive == "clarify":
        return (
            "Bạn là trợ lý Smart ERP (read-only). Người dùng cần làm rõ SKU vs đơn hàng. "
            "Trả lời bằng một đoạn tiếng Việt ngắn (<=3 câu). "
            f"Câu hỏi: {msg}\nRAG_summary: {rag}"
        )
    bullets = [f"RAG: {rag}"]
    if db:
        bullets.append(f"DB_READONLY_SUMMARY: {db}")
    bullet_txt = "\n".join(bullets)
    return (
        "Bạn là trợ lý Smart ERP (read-only). Chỉ dùng dữ liệu trong RAG/DB summary. "
        "Nếu không đủ dữ liệu, nói rõ không chắc. Trả lời tiếng Việt súc tích.\n"
        f"USER: {msg}\nFACTS:\n{bullet_txt}"
    )


class Task003Orchestrator:
    def __init__(
        self,
        *,
        rag: VectorRagMcpPort,
        db: DbReadonlyMcpPort | None,
        stream_fn: StreamFn,
        graph: object | None = None,
    ) -> None:
        self._rag = rag
        self._db = db
        self._stream_fn = stream_fn
        self._graph = graph or compile_task003_graph()

    async def stream_turn(
        self,
        *,
        message: str,
        correlation_id: str | None,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> AsyncIterator[str]:
        rag_ingest_telemetry_best_effort()
        corr = correlation_id or str(uuid.uuid4())

        init: Task003GraphState = {
            "user_message": message,
            "correlation_id": corr,
            "user_id": user_id,
            "session_id": session_id,
            "sse_out": [],
        }
        cfg = {"configurable": {"rag": self._rag, "db": self._db}}
        graph_out: Task003GraphState = await self._graph.ainvoke(init, cfg)  # type: ignore[union-attr]

        for envelope in graph_out.get("sse_out") or []:
            yield _sse_data_line(envelope)

        refusal = graph_out.get("refusal_code")
        if refusal:
            yield _sse_data_line(refuse_token_event(str(refusal)))
            yield _sse_data_line({"event": "done", "payload": _mk_usage().model_dump()})
            meta = summarize_public_side_effect(graph_out)
            logger.info("task003_turn", extra=meta)
            return

        if graph_out.get("rag_failed"):
            err = graph_out.get("last_mcp_error")
            if isinstance(err, McpToolError):
                code = err.code
                msg = err.message
            else:
                code = "RAG_UPSTREAM_ERROR"
                msg = ""
            yield _sse_data_line(
                build_sse_error_event(
                    code,
                    sse_error_message_for_mcp(code, msg),
                )
            )
            yield _sse_data_line(
                build_sse_token(
                    sse_error_message_for_mcp(code, "RAG lỗi trước khi tổng hợp câu trả lời.")
                )
            )
            yield _sse_data_line({"event": "done", "payload": _mk_usage().model_dump()})
            meta = summarize_public_side_effect(graph_out)
            logger.info("task003_turn", extra=meta)
            return

        err = graph_out.get("last_mcp_error")
        if isinstance(err, McpToolError) and not graph_out.get("rag_failed"):
            code = err.code
            yield _sse_data_line(
                build_sse_error_event(
                    code,
                    sse_error_message_for_mcp(code, err.message),
                )
            )
            yield _sse_data_line(build_sse_token(sse_error_message_for_mcp(code, err.message)))
            yield _sse_data_line({"event": "done", "payload": _mk_usage().model_dump()})
            meta = summarize_public_side_effect(graph_out)
            logger.info("task003_turn", extra=meta)
            return

        prompt = _build_prompt(graph_out)
        async for delta in self._stream_fn(prompt):
            yield _sse_data_line(build_sse_token(delta))

        meta = summarize_public_side_effect(graph_out)
        logger.info("task003_turn", extra=meta)

        yield _sse_data_line({"event": "done", "payload": _mk_usage().model_dump()})
