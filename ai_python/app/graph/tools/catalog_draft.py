"""Harness tool adapter for catalog draft HITL flow."""

from __future__ import annotations

import asyncio
from typing import Any

from app.graph.catalog_draft_subgraph import build_catalog_draft_subgraph
from app.graph.deps import GraphDeps
from app.graph.tools._state import build_tool_config, build_tool_state
from app.harness.tool_registry import HitlSpec, ToolManifest, ToolResult, TurnContext


class CatalogDraftTool:
    manifest = ToolManifest(
        name="catalog_draft",
        description="Create a catalog/product/category draft and stop for human confirmation.",
        args_schema='{"request": "string"}',
        has_hitl=True,
    )

    def __init__(self, deps: GraphDeps, compiled: Any | None = None) -> None:
        self._deps = deps
        self._compiled = compiled or build_catalog_draft_subgraph(deps).compile()

    async def invoke(self, args: dict[str, Any], ctx: TurnContext) -> ToolResult:
        request = str(args.get("request") or args.get("query") or "").strip()
        out = await asyncio.to_thread(
            self._compiled.invoke,
            build_tool_state(request, ctx, self._deps.settings),
            build_tool_config(ctx),
        )
        draft_sse = out.get("catalog_draft_sse") if isinstance(out, dict) else None
        if isinstance(draft_sse, dict) and draft_sse:
            resume = ctx.thread_id or ctx.correlation_id
            return ToolResult(
                ok=True,
                output=dict(out or {}),
                observation_text="Catalog draft ready; awaiting user confirmation.",
                sse_payload=draft_sse,
                pending_hitl=HitlSpec(event_name="draft", payload=draft_sse, resume_token=resume),
            )
        msg = "Catalog draft failed."
        error = out.get("error_payload") if isinstance(out, dict) else None
        if isinstance(error, dict) and error.get("message"):
            msg = str(error["message"])
        return ToolResult(ok=False, output=dict(out or {}), observation_text=msg, error_message=msg)
