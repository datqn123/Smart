"""Harness tool adapter for inventory draft HITL flow."""

from __future__ import annotations

import asyncio
from typing import Any

from app.graph.deps import GraphDeps
from app.graph.inventory_draft_subgraph import build_inventory_draft_subgraph
from app.graph.spring_inventory_draft_client import commit_inventory_draft
from app.graph.tools._state import build_tool_config, build_tool_state
from app.harness.tool_registry import HitlSpec, ToolManifest, ToolResult, TurnContext


class InventoryDraftTool:
    manifest = ToolManifest(
        name="inventory_draft",
        description="Create an inventory document draft and stop for human confirmation.",
        args_schema='{"request": "string"}',
        has_hitl=True,
        capability="draft_create",
        output_schema='{"draft": "dict"}',
        output_artifact_types=("inventory_draft",),
        when_to_use="User asks to create an inventory receipt/issue document.",
        when_not_to_use="User only wants to read or list inventory data (use sql_query).",
        risk_level="high",
        rbac_required=("draft_create",),
        side_effect_class="non_idempotent_write",
        produces=("inventory_draft",),
        examples=("tạo phiếu nhập kho", "lập phiếu xuất hàng"),
    )

    def __init__(self, deps: GraphDeps, compiled: Any | None = None) -> None:
        self._deps = deps
        self._compiled = compiled or build_inventory_draft_subgraph(deps).compile()

    async def invoke(self, args: dict[str, Any], ctx: TurnContext) -> ToolResult:
        if ctx.clarification_response is not None:
            return await self._confirm(ctx)

        request = str(args.get("request") or args.get("query") or "").strip()
        out = await asyncio.to_thread(
            self._compiled.invoke,
            build_tool_state(request, ctx, self._deps.settings),
            build_tool_config(ctx),
        )
        draft_sse = out.get("inventory_draft_sse") if isinstance(out, dict) else None
        if isinstance(draft_sse, dict) and draft_sse:
            resume = ctx.thread_id or ctx.correlation_id
            return ToolResult(
                ok=True,
                output=dict(out or {}),
                observation_text="Inventory draft ready; awaiting user confirmation.",
                sse_payload=draft_sse,
                pending_hitl=HitlSpec(event_name="inventory_draft", payload=draft_sse, resume_token=resume),
            )
        msg = "Inventory draft failed."
        error = out.get("error_payload") if isinstance(out, dict) else None
        if isinstance(error, dict) and error.get("message"):
            msg = str(error["message"])
        return ToolResult(ok=False, output=dict(out or {}), observation_text=msg, error_message=msg)

    async def _confirm(self, ctx: TurnContext) -> ToolResult:
        draft_id = _draft_id_from_context(ctx)
        if not draft_id:
            msg = "Không tìm thấy nháp kho đang chờ xác nhận. Vui lòng tạo lại nháp."
            return ToolResult(ok=False, output={"code": "HITL_DRAFT_MISSING"}, observation_text=msg, error_message=msg)
        try:
            committed = await asyncio.to_thread(
                commit_inventory_draft,
                self._deps.settings,
                bearer_token=ctx.bearer_token,
                draft_id=draft_id,
            )
        except Exception as exc:  # noqa: BLE001
            msg = f"Không xác nhận được nháp kho: {exc}"
            return ToolResult(ok=False, output={"draft_id": draft_id}, observation_text=msg, error_message=msg)
        ok = bool(committed.get("ok", True)) if isinstance(committed, dict) else True
        msg = str(committed.get("message") or f"Đã xác nhận nháp kho {draft_id}.") if isinstance(committed, dict) else f"Đã xác nhận nháp kho {draft_id}."
        if ok and "Đã xác nhận" not in msg:
            msg = f"Đã xác nhận nháp kho {draft_id}. {msg}"
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
