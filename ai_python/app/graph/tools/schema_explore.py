"""Harness tool adapter for schema exploration."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any

from app.graph.deps import GraphDeps
from app.graph.nodes.schema_explore import make_schema_explore_node
from app.graph.tools._state import build_tool_state
from app.harness.tool_registry import ToolManifest, ToolResult, TurnContext

logger = logging.getLogger(__name__)


class SchemaExploreTool:
    manifest = ToolManifest(
        name="schema_explore",
        description="Explore ERP database schema, relevant tables, columns, and join hints.",
        args_schema='{"topic": "string"}',
        capability="data_read",
        output_schema='{"schema": "string"}',
        when_to_use="Planner needs table/column names or join hints before composing a data query.",
        when_not_to_use="Actual data values are needed (use sql_query).",
        risk_level="low",
        side_effect_class="read_only",
        produces=("schema",),
        examples=("bảng nào chứa tồn kho", "cột nào là doanh thu"),
    )

    def __init__(self, deps: GraphDeps) -> None:
        self._deps = deps
        self._node_fn = make_schema_explore_node(deps)

    async def invoke(self, args: dict[str, Any], ctx: TurnContext) -> ToolResult:
        _invoke_start = time.monotonic()
        logger.info("tool_invoke_start tool=schema_explore topic=%s", args.get("topic", ""))
        topic = str(args.get("topic") or args.get("query") or "").strip()
        state = build_tool_state(topic, ctx, self._deps.settings)
        out = await asyncio.to_thread(self._node_fn, state)
        plan = out.get("schema_plan") if isinstance(out, dict) else None
        artifact = out.get("runtime_schema_artifact") if isinstance(out, dict) else None
        if isinstance(plan, dict):
            obs = f"Schema plan: {json.dumps(plan, ensure_ascii=False, default=str)[:800]}"
        elif isinstance(artifact, dict):
            obs = "Schema artifact loaded."
        else:
            obs = "Schema exploration did not return additional schema context."
        _latency_ms = (time.monotonic() - _invoke_start) * 1000
        result = ToolResult(ok=not bool(out.get("error_payload")), output=dict(out or {}), observation_text=obs)
        logger.info("tool_invoke_end tool=schema_explore ok=%s latency_ms=%.0f tables=%s",
                    result.ok, _latency_ms, len(result.output.get("schema", {}).get("tables", [])))
        return result
