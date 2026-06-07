"""Harness tool adapter for schema exploration."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from app.graph.deps import GraphDeps
from app.graph.nodes.schema_explore import make_schema_explore_node
from app.graph.tools._state import build_tool_state
from app.harness.tool_registry import ToolManifest, ToolResult, TurnContext


class SchemaExploreTool:
    manifest = ToolManifest(
        name="schema_explore",
        description="Explore ERP database schema, relevant tables, columns, and join hints.",
        args_schema='{"topic": "string"}',
    )

    def __init__(self, deps: GraphDeps) -> None:
        self._deps = deps
        self._node_fn = make_schema_explore_node(deps)

    async def invoke(self, args: dict[str, Any], ctx: TurnContext) -> ToolResult:
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
        return ToolResult(ok=not bool(out.get("error_payload")), output=dict(out or {}), observation_text=obs)
