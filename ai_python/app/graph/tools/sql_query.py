"""Harness tool adapter for the SQL subgraph."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from app.graph.deps import GraphDeps
from app.graph.sql_subgraph import build_sql_subgraph
from app.graph.tools._state import build_tool_config, build_tool_state
from app.harness.tool_registry import ToolManifest, ToolResult, TurnContext


def _format_rows_observation(rows: list[Any]) -> str:
    if not rows:
        return "SQL query returned no rows."
    head = rows[:5]
    suffix = f" ... {len(rows)} rows total" if len(rows) > 5 else ""
    return f"SQL rows: {json.dumps(head, ensure_ascii=False, default=str)}{suffix}"


class SqlQueryTool:
    manifest = ToolManifest(
        name="sql_query",
        description="Read ERP data using the SQL subgraph. Input can be a natural-language data question.",
        args_schema='{"query": "string"}',
    )

    def __init__(self, deps: GraphDeps, compiled: Any | None = None) -> None:
        self._deps = deps
        self._compiled = compiled or build_sql_subgraph(deps).compile()

    async def invoke(self, args: dict[str, Any], ctx: TurnContext) -> ToolResult:
        query = str(args.get("query") or args.get("sql") or "").strip()
        state = build_tool_state(query, ctx, self._deps.settings)
        out = await asyncio.to_thread(self._compiled.invoke, state, build_tool_config(ctx))
        result = out.get("query_result") if isinstance(out, dict) else None
        rows = result.get("rows", []) if isinstance(result, dict) else []
        sse = out.get("query_table_sse") if isinstance(out, dict) else None
        if isinstance(sse, dict):
            sse = {"_event": "data_table", **sse}
        return ToolResult(
            ok=bool(out.get("result_ok")) if isinstance(out, dict) else False,
            output=dict(out or {}),
            observation_text=_format_rows_observation(rows if isinstance(rows, list) else []),
            sse_payload=sse if isinstance(sse, dict) else None,
        )
