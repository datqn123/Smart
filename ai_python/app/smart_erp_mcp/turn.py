from __future__ import annotations

import os
from typing import Any, Protocol

from mcp.client.session import ClientSession

from .handlers import (
    handle_intent_analyze,
    handle_rag_retrieve,
    handle_read_catalog_snapshot,
    handle_sql_execute_read,
    handle_ui_build_form_spec,
    handle_viz_build_chart_spec,
)
from .mcp_stdio import call_tool_stdio, mcp_client_session


class ToolInvoker(Protocol):
    async def call(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]: ...


class _InlineInvoker:
    async def call(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name == "intent_analyze":
            return handle_intent_analyze(
                str(arguments["user_text"]),
                str(arguments.get("session_id", "")),
            )
        if name == "rag_retrieve":
            return handle_rag_retrieve(str(arguments["query"]), int(arguments.get("top_k", 5)))
        if name == "read_catalog_snapshot":
            return handle_read_catalog_snapshot()
        if name == "sql_execute_read":
            return handle_sql_execute_read(str(arguments["sql"]))
        if name == "ui_build_form_spec":
            return handle_ui_build_form_spec(
                str(arguments["title"]),
                list(arguments["fields"]),
                arguments.get("defaults"),
            )
        if name == "viz_build_chart_spec":
            return handle_viz_build_chart_spec(
                str(arguments["chart_type"]),
                list(arguments["labels"]),
                dict(arguments["series"]),
            )
        return {"ok": False, "error": {"code": "UNKNOWN_TOOL", "message": name}}


class _StdioInvoker:
    def __init__(self, session: ClientSession) -> None:
        self._session = session

    async def call(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        return await call_tool_stdio(self._session, name, arguments)


def use_stdio_mcp() -> bool:
    if os.getenv("SMART_ERP_MCP_INLINE", "").lower() in ("1", "true", "yes"):
        return False
    return os.getenv("SMART_ERP_MCP_STDIO", "").lower() in ("1", "true", "yes")


async def run_smart_erp_turn(
    user_text: str,
    session_id: str = "",
    sql: str | None = None,
) -> dict[str, Any]:
    """
    intent_analyze → gọi thêm tool theo ``primary_intent`` (demo routing).

    - ``SMART_ERP_MCP_STDIO=1`` (mặc định): một phiên MCP stdio, gọi tool qua protocol.
    - ``SMART_ERP_MCP_INLINE=1``: gọi handler in-process (pytest / khi không spawn được process).
    """
    steps: list[dict[str, Any]] = []

    if use_stdio_mcp():
        async with mcp_client_session() as session:
            invoker: ToolInvoker = _StdioInvoker(session)
            intent = await invoker.call(
                "intent_analyze",
                {"user_text": user_text, "session_id": session_id},
            )
            steps.append({"tool": "intent_analyze", "result": intent})
            steps.extend(await _dispatch(invoker, intent, user_text, sql))
            return {"mode": "stdio", "steps": steps}

    invoker = _InlineInvoker()
    intent = await invoker.call(
        "intent_analyze",
        {"user_text": user_text, "session_id": session_id},
    )
    steps.append({"tool": "intent_analyze", "result": intent})
    steps.extend(await _dispatch(invoker, intent, user_text, sql))
    return {"mode": "inline", "steps": steps}


async def _dispatch(
    invoker: ToolInvoker,
    intent: dict[str, Any],
    user_text: str,
    sql: str | None,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not intent.get("ok", True):
        return out
    primary = intent.get("primary_intent")
    if primary == "refusal":
        return out
    if primary == "rag_qa":
        r = await invoker.call("rag_retrieve", {"query": user_text, "top_k": 5})
        out.append({"tool": "rag_retrieve", "result": r})
        return out
    if primary == "data_query":
        out.append(
            {
                "tool": "read_catalog_snapshot",
                "result": await invoker.call("read_catalog_snapshot", {}),
            }
        )
        q = sql or "SELECT id, sku, qty FROM products ORDER BY id LIMIT 10"
        out.append(
            {
                "tool": "sql_execute_read",
                "result": await invoker.call("sql_execute_read", {"sql": q}),
            }
        )
        return out
    if primary == "visualization":
        out.append(
            {
                "tool": "read_catalog_snapshot",
                "result": await invoker.call("read_catalog_snapshot", {}),
            }
        )
        q = sql or "SELECT d, amount FROM revenue_daily ORDER BY d"
        sql_res = await invoker.call("sql_execute_read", {"sql": q})
        out.append({"tool": "sql_execute_read", "result": sql_res})
        labels: list[str] = []
        series_vals: list[float] = []
        if sql_res.get("ok") and sql_res.get("rows"):
            for row in sql_res["rows"]:
                if len(row) >= 2:
                    labels.append(str(row[0]))
                    series_vals.append(float(row[1]))
        viz = await invoker.call(
            "viz_build_chart_spec",
            {
                "chart_type": "line",
                "labels": labels or ["a", "b"],
                "series": {"amount": series_vals or [0.0, 0.0]},
            },
        )
        out.append({"tool": "viz_build_chart_spec", "result": viz})
        return out
    if primary == "transactional_update":
        out.append(
            {
                "tool": "read_catalog_snapshot",
                "result": await invoker.call("read_catalog_snapshot", {}),
            }
        )
        q = sql or "SELECT id, sku, qty FROM products ORDER BY id LIMIT 10"
        snap = await invoker.call("sql_execute_read", {"sql": q})
        out.append({"tool": "sql_execute_read", "result": snap})
        fields = [
            {"name": "sku", "type": "string", "required": True},
            {"name": "qty", "type": "number", "required": True},
        ]
        defaults: dict[str, Any] = {}
        if snap.get("ok") and snap.get("rows") and snap["rows"]:
            r0 = snap["rows"][0]
            if len(r0) >= 3:
                defaults = {"sku": r0[1], "qty": r0[2]}
        form = await invoker.call(
            "ui_build_form_spec",
            {
                "title": "Xác nhận cập nhật (demo)",
                "fields": fields,
                "defaults": defaults,
            },
        )
        out.append({"tool": "ui_build_form_spec", "result": form})
        return out
    # conversation / help: chỉ intent
    return out
