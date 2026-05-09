from __future__ import annotations

import asyncio

from app.smart_erp_mcp.server import build_mcp


def test_fastmcp_lists_core_tools() -> None:
    mcp = build_mcp()

    async def _list() -> set[str]:
        tools = await mcp.list_tools()
        return {t.name for t in tools}

    names = asyncio.run(_list())
    for required in (
        "intent_analyze",
        "rag_retrieve",
        "read_catalog_snapshot",
        "sql_propose_select",
        "sql_execute_read",
        "ui_build_form_spec",
        "ui_build_table_spec",
        "viz_build_chart_spec",
        "write_commit",
    ):
        assert required in names
