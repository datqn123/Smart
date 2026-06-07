"""Harness-owned agentic loop."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

from app.config.graph_settings import GraphSettings
from app.harness.policy import HarnessPolicy, HarnessPolicyError
from app.harness.runtime import AgentHarness, ToolCallContext
from app.harness.scratchpad import TurnScratchpad
from app.harness.tool_registry import (
    DecisionSchema,
    HitlSpec,
    ToolInput,
    ToolRegistry,
    ToolResult,
    TurnContext,
)
from app.llm.registry import LlmRegistry

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProgressEvent:
    text: str


@dataclass(frozen=True)
class SsePayloadEvent:
    event_name: str
    payload: dict[str, Any]


@dataclass(frozen=True)
class FinalAnswerEvent:
    text: str


@dataclass(frozen=True)
class PendingHitlEvent:
    spec: HitlSpec


@dataclass(frozen=True)
class ErrorEvent:
    message: str
    code: str


class HarnessOrchestrator:
    def __init__(
        self,
        *,
        llm_registry: LlmRegistry,
        tool_registry: ToolRegistry,
        policy: HarnessPolicy,
        settings: GraphSettings,
        harness: AgentHarness,
    ) -> None:
        self._llm_registry = llm_registry
        self._tool_registry = tool_registry
        self._policy = policy
        self._settings = settings
        self._harness = harness

    async def run(
        self,
        scratchpad: TurnScratchpad,
        ctx: TurnContext,
    ) -> AsyncIterator[ProgressEvent | SsePayloadEvent | FinalAnswerEvent | PendingHitlEvent | ErrorEvent]:
        max_steps = int(getattr(self._settings, "harness_max_steps", 6))
        for step in range(max_steps):
            scratchpad.step = step
            try:
                decision = await self._decide(scratchpad)
            except Exception as exc:  # noqa: BLE001
                logger.warning("harness decision failed", exc_info=True)
                yield ErrorEvent("Không đọc được quyết định điều phối.", "HARNESS_DECISION_ERROR")
                return

            yield ProgressEvent(f"Bước {step + 1}: {decision.action}")
            if decision.action == "final_answer":
                yield FinalAnswerEvent(decision.final_answer or "")
                return

            if decision.tool_call is None:
                yield ErrorEvent("Decision missing tool_call.", "HARNESS_DECISION_INVALID")
                return

            tool_name = decision.tool_call.tool_name
            args = dict(decision.tool_call.args or {})
            try:
                self._policy.check(tool_name, args)
                result = await self._harness_run_tool_async(
                    ToolInput(tool_name=tool_name, args=args, context=ctx)
                )
            except HarnessPolicyError as exc:
                yield ErrorEvent(str(exc), "HARNESS_POLICY_BLOCK")
                return
            except Exception as exc:  # noqa: BLE001
                logger.warning("harness tool failed tool=%s", tool_name, exc_info=True)
                result = ToolResult(
                    ok=False,
                    output={},
                    observation_text=f"Tool {tool_name} failed.",
                    error_message=str(exc),
                )

            if result.pending_hitl:
                if result.sse_payload:
                    yield SsePayloadEvent(result.pending_hitl.event_name, result.sse_payload)
                yield PendingHitlEvent(result.pending_hitl)
                return

            if result.sse_payload:
                event_name = str(result.sse_payload.get("_event") or "data")
                payload = {k: v for k, v in result.sse_payload.items() if k != "_event"}
                yield SsePayloadEvent(event_name, payload)

            scratchpad.add_observation(result, tool_name)

        self._audit_warn("step_budget_exhausted", ctx)
        yield FinalAnswerEvent(scratchpad.observation_summary())

    async def _decide(self, scratchpad: TurnScratchpad) -> DecisionSchema:
        role = str(getattr(self._settings, "harness_planner_role", "harness_planner") or "harness_planner")
        client = self._llm_registry.get(role)
        messages = scratchpad.to_decision_prompt(self._tool_registry.tools_manifest_text())
        return await client.astructured_predict(messages, DecisionSchema)

    async def _harness_run_tool_async(self, tool_input: ToolInput) -> ToolResult:
        ctx = ToolCallContext(
            tool_name=tool_input.tool_name,
            correlation_id=tool_input.context.correlation_id,
            tenant_id=tool_input.context.tenant_id,
            thread_id=tool_input.context.thread_id,
        )
        if not getattr(self._harness, "_enabled", True):
            tool = self._tool_registry.get_impl(tool_input.tool_name)
            return await tool.invoke(tool_input.args, tool_input.context)
        self._harness._before_tool_call(ctx)
        try:
            tool = self._tool_registry.get_impl(tool_input.tool_name)
            result = await tool.invoke(tool_input.args, tool_input.context)
        except Exception as exc:
            self._harness._after_tool_call(ctx, ok=False, error=str(exc))
            raise
        self._harness._after_tool_call(ctx, ok=result.ok, result=result.output)
        return result

    def _audit_warn(self, code: str, ctx: TurnContext) -> None:
        logger.warning(
            "harness_warn code=%s correlation_id=%s tenant_id=%s thread_id=%s",
            code,
            ctx.correlation_id,
            ctx.tenant_id or "-",
            ctx.thread_id or "-",
        )
