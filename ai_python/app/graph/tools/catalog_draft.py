"""Harness tool adapter for catalog draft HITL flow."""

from __future__ import annotations

import asyncio
from typing import Any

from app.graph.catalog_draft_subgraph import build_catalog_draft_subgraph
from app.graph.deps import GraphDeps
from app.graph.spring_catalog_draft_client import commit_catalog_draft
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
        if ctx.clarification_response is not None:
            return await self._confirm(ctx)

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

    async def _confirm(self, ctx: TurnContext) -> ToolResult:
        draft_id = _draft_id_from_context(ctx)
        if not draft_id:
            msg = "Không tìm thấy nháp catalog đang chờ xác nhận. Vui lòng tạo lại nháp."
            return ToolResult(ok=False, output={"code": "HITL_DRAFT_MISSING"}, observation_text=msg, error_message=msg)
        try:
            committed = await asyncio.to_thread(
                commit_catalog_draft,
                self._deps.settings,
                bearer_token=ctx.bearer_token,
                draft_id=draft_id,
            )
        except Exception as exc:  # noqa: BLE001
            msg = f"Không xác nhận được nháp catalog: {exc}"
            return ToolResult(ok=False, output={"draft_id": draft_id}, observation_text=msg, error_message=msg)
        failed = int(committed.get("failedCount") or 0) if isinstance(committed, dict) else 0
        ok = failed == 0
        committed_count = committed.get("committedCount") if isinstance(committed, dict) else None
        msg = f"Đã xác nhận nháp catalog {draft_id}."
        if committed_count is not None:
            msg = f"Đã xác nhận nháp catalog {draft_id}: {committed_count} dòng được ghi."
        if not ok:
            msg = f"Nháp catalog {draft_id} còn {failed} dòng lỗi sau khi xác nhận."
        return ToolResult(
            ok=ok,
            output={"draft_id": draft_id, "commit_result": dict(committed or {})},
            observation_text=msg,
            error_message=None if ok else msg,
        )


def _draft_id_from_context(ctx: TurnContext) -> str | None:
    clarification = ctx.clarification_response if isinstance(ctx.clarification_response, dict) else {}
    continuation = clarification.get("continuation_context")
    if isinstance(continuation, dict):
        for key in ("draftId", "draft_id", "id"):
            raw = continuation.get(key)
            if raw:
                return str(raw)
    pending = ctx.pending_hitl_payload if isinstance(ctx.pending_hitl_payload, dict) else {}
    for key in ("draftId", "draft_id", "id"):
        raw = pending.get(key)
        if raw:
            return str(raw)
    return None
