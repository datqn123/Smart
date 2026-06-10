"""Harness tool adapter for schema exploration."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from app.graph.deps import GraphDeps
from app.graph.pg_schema_context import build_schema_artifact_from_postgres
from app.graph.sql_prompts import format_schema_block
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

    async def invoke(self, args: dict[str, Any], ctx: TurnContext) -> ToolResult:
        _invoke_start = time.monotonic()
        logger.info("tool_invoke_start tool=schema_explore topic=%s", args.get("topic", ""))
        topic = str(args.get("topic") or args.get("query") or "").strip()
        artifact, err = await asyncio.to_thread(
            build_schema_artifact_from_postgres, self._deps.settings, topic
        )
        if err:
            _latency_ms = (time.monotonic() - _invoke_start) * 1000
            logger.info("tool_invoke_end tool=schema_explore ok=False latency_ms=%.0f", _latency_ms)
            return ToolResult(
                ok=False,
                output={"schema": {}},
                observation_text=f"Schema load failed: {err}",
                error_message=str(err),
            )
        schema_block = format_schema_block(artifact, selected_tables=None, enriched=True)
        schema = artifact.model_dump(mode="json") if hasattr(artifact, "model_dump") else {}
        obs = f"Schema artifact loaded. {len(schema.get('tables', []))} tables."
        _latency_ms = (time.monotonic() - _invoke_start) * 1000
        result = ToolResult(ok=True, output={"schema": schema, "schema_text": schema_block}, observation_text=obs)
        logger.info("tool_invoke_end tool=schema_explore ok=%s latency_ms=%.0f tables=%s",
                    result.ok, _latency_ms, len(schema.get("tables", [])))
        return result
