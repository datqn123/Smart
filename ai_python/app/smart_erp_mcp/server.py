from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from .handlers import (
    handle_intent_analyze,
    handle_rag_retrieve,
    handle_read_catalog_snapshot,
    handle_sql_execute_read,
    handle_sql_propose_select,
    handle_ui_build_form_spec,
    handle_ui_build_table_spec,
    handle_viz_build_chart_spec,
    handle_write_commit,
)

logger = logging.getLogger("smart_erp_mcp")


def build_mcp() -> FastMCP:
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO)
    mcp = FastMCP("smart-erp-ai")

    @mcp.tool()
    def intent_analyze(user_text: str, session_id: str = "") -> dict[str, Any]:
        """Phân loại intent User Smart ERP; gợi ý nhóm tool tiếp theo."""
        return handle_intent_analyze(user_text, session_id)

    @mcp.tool()
    def rag_retrieve(query: str, top_k: int = 5) -> dict[str, Any]:
        """RAG stub (Plane A): chunk schema/policy — không thay thế số live."""
        return handle_rag_retrieve(query, top_k)

    @mcp.tool()
    def read_catalog_snapshot() -> dict[str, Any]:
        """Catalog demo để grounding SQL (Plane B metadata)."""
        return handle_read_catalog_snapshot()

    @mcp.tool()
    def sql_propose_select(
        draft_sql: str,
        rag_table_hints: list[str] | None = None,
    ) -> dict[str, Any]:
        """Validate + chuẩn hoá SELECT; cảnh báo hint RAG thừa."""
        return handle_sql_propose_select(draft_sql, rag_table_hints)

    @mcp.tool()
    def sql_execute_read(sql: str) -> dict[str, Any]:
        """SELECT đã validate, chạy trên SQLite demo trong process."""
        return handle_sql_execute_read(sql)

    @mcp.tool()
    def ui_build_form_spec(
        title: str,
        fields: list[dict[str, Any]],
        defaults: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Sinh JSON FormSpec (fields/defaults) cho FE."""
        return handle_ui_build_form_spec(title, fields, defaults)

    @mcp.tool()
    def ui_build_table_spec(
        title: str,
        columns: list[str],
        rows: list[list[Any]],
    ) -> dict[str, Any]:
        """Sinh JSON TableSpec cho FE."""
        return handle_ui_build_table_spec(title, columns, rows)

    @mcp.tool()
    def viz_build_chart_spec(
        chart_type: str,
        labels: list[str],
        series: dict[str, list[float]],
    ) -> dict[str, Any]:
        """Sinh JSON ChartSpec (series đã aggregate từ read.*)."""
        return handle_viz_build_chart_spec(chart_type, labels, series)

    @mcp.tool()
    def write_commit(
        proposal_id: str,
        hitl_token: str,
        idempotency_key: str,
        payload_json: str,
    ) -> dict[str, Any]:
        """Cửa ghi duy nhất (stub): cần HITL token + idempotency + JSON payload."""
        out = handle_write_commit(proposal_id, hitl_token, idempotency_key, payload_json)
        if out.get("ok"):
            logger.info(
                "write_commit stub proposal_id=%s idempotency_key=%s",
                proposal_id,
                idempotency_key,
            )
        return out

    return mcp


def run_stdio() -> None:
    build_mcp().run(transport="stdio")
