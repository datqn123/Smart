"""SSE progress events — user-facing status text during graph execution."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)

# LangGraph node id → progress agent key (when different from node name).
_NODE_PROGRESS_AGENT: dict[str, str] = {
    "resolve_catalog_draft": "draft_resolve",
    "resolve_inventory_draft": "draft_resolve",
}

# Mapping: (agent, phase_keyword) → user-facing Vietnamese progress text
_PROGRESS_MAP: dict[tuple[str, str], str] = {
    ("domain_guard", ""): "Đang kiểm tra phạm vi câu hỏi...",
    ("context_compact", ""): "Đang tóm tắt lịch sử hội thoại...",
    ("classify_intent", ""): "Đang phân loại yêu cầu...",
    ("chat_normal", ""): "Đang soạn câu trả lời...",
    ("gen_sql", ""): "Đang tạo truy vấn SQL...",
    ("sql_review", ""): "Đang rà soát câu truy vấn...",
    ("validate_sql", ""): "Đang kiểm tra cú pháp SQL...",
    ("execute_sql", ""): "Đang truy vấn dữ liệu từ hệ thống...",
    ("validate_result", ""): "Đang kiểm tra kết quả truy vấn...",
    ("summarize_answer", ""): "Đang tóm tắt kết quả...",
    ("agent_idea", ""): "Đang phân tích dữ liệu cho biểu đồ...",
    ("agent_chart", ""): "Đang tạo biểu đồ...",
    ("agent_review", ""): "Đang hoàn thiện biểu đồ...",
    ("chart_readiness", ""): "Đang kiểm tra dữ liệu biểu đồ...",
    ("schema_explore", ""): "Đang khám phá cấu trúc database...",
    ("classify_catalog_entity", ""): "Đang xác định loại danh mục...",
    ("generate_catalog_draft", ""): "Đang tạo bảng danh mục...",
    ("persist_catalog_draft", ""): "Đang lưu bảng danh mục...",
    ("classify_inventory_doc", ""): "Đang xác định loại chứng từ...",
    ("generate_inventory_draft", ""): "Đang tạo phiếu kho...",
    ("persist_inventory_draft", ""): "Đang lưu phiếu kho...",
    ("emit_query_table", ""): "Đang chuẩn bị bảng kết quả...",
    ("chart_fail_message", ""): "Đang xử lý lỗi biểu đồ...",
    ("fail_max_attempts", ""): "Đang xử lý lỗi sau nhiều lần thử...",
    ("draft_resolve", ""): "Đang phân tích yêu cầu...",
}


def resolve_progress_text(agent: str, phase: str = "") -> str:
    """Return user-facing progress text for a given agent/phase."""
    key = (agent, "")
    if key in _PROGRESS_MAP:
        return _PROGRESS_MAP[key]
    # Fallback: generic message
    return f"Đang xử lý ({agent})..."


def stream_progress(agent: str, phase: str = "") -> None:
    """Push progress immediately via LangGraph custom stream (node entry, before LLM/SQL)."""
    text = resolve_progress_text(agent, phase)
    try:
        from langgraph.config import get_stream_writer

        get_stream_writer()({"progress_text": text})
        logger.info("[progress:stream] agent=%s text=%s", agent, text)
    except Exception:
        logger.debug("stream_progress skipped (no active stream)", exc_info=True)


def wrap_node_with_stream_progress(
    node_id: str,
    node_fn: Callable[[Any], dict],
    *,
    agent: str | None = None,
) -> Callable[[Any], dict]:
    """Call ``stream_progress`` when the node starts, then run the node body."""
    progress_agent = agent or _NODE_PROGRESS_AGENT.get(node_id, node_id)

    def wrapped(state: Any) -> dict:
        stream_progress(progress_agent)
        return node_fn(state)

    wrapped.__name__ = getattr(node_fn, "__name__", node_id)
    wrapped.__doc__ = node_fn.__doc__
    return wrapped


def emit_progress(state: dict[str, Any] | None, agent: str, phase: str = "") -> dict[str, Any]:
    """
    Return a state patch with `progress_text` for SSE streaming.

    Call at the start of each node to push a progress event to the frontend.
    Example:
        return {**emit_progress(state, "gen_sql"), **other_updates}
    """
    text = resolve_progress_text(agent, phase)
    logger.info("[progress] agent=%s text=%s", agent, text)
    return {"progress_text": text}
