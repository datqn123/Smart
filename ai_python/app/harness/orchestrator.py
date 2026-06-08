"""Harness-owned agentic loop."""

from __future__ import annotations

import hashlib
import json
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass, replace
from typing import Any

from langchain_core.messages import HumanMessage

from app.config.graph_settings import GraphSettings
from app.harness.budget import BudgetExceeded, TurnBudget
from app.harness.cache import InMemorySemanticCache
from app.harness.intent import IntentContextBuilder, IntentSubagent
from app.harness.memory import WorkingMemory
from app.harness.model_router import ModelRouter
from app.harness.eval_gate import v3_rollout_allowed
from app.harness.observability import TraceRecorder
from app.harness.history_store import (
    STATUS_CLARIFY_PENDING,
    STATUS_DEGRADED,
    STATUS_FAILURE,
    STATUS_HITL_PENDING,
    STATUS_SUCCESS,
    IntentHistoryStore,
    build_history_event,
)
from app.harness.observation import ObservationEnvelope
from app.harness.plan_graph import (
    NodeResult,
    PlanExecutor,
    PlanGraph,
    PlannerSubagent,
    degraded_final_answer,
    run_planner_owned_plan,
)
from app.harness.plan_template_store import (
    PLANNER_GENERATED,
    PlanTemplateRecord,
    PlanTemplateStore,
    build_intent_key,
    normalize_intent_key,
    plan_graph_hash,
)
from app.harness.result_store import InMemoryResultRefStore
from app.harness.policy import POLICY_VERSION, HarnessPolicy, HarnessPolicyError
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
class ClarifyEvent:
    questions: list[str]
    suggested_rewrite: str
    original_question: str


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
        plan_template_store: PlanTemplateStore | None = None,
        history_store: IntentHistoryStore | None = None,
    ) -> None:
        self._llm_registry = llm_registry
        self._tool_registry = tool_registry
        self._policy = policy
        self._settings = settings
        self._harness = harness
        self._plan_template_store = plan_template_store
        self._history_store = history_store
        self._budget = self._new_budget()
        self._last_budget_hit: str | None = None
        self._last_llm_tokens = 0
        self._last_llm_cost = 0.0
        # P7 — tiered routing + deterministic cache (gated by settings flags).
        self._model_router = ModelRouter(
            opt_escalate_replan_count=int(getattr(settings, "opt_escalate_replan_count", 2) or 2)
        )
        self._cache = InMemorySemanticCache()
        # P5 — working memory trimming (gated).
        self._working_memory = WorkingMemory(pairs=int(getattr(settings, "working_memory_pairs", 6) or 6))
        # P8 — last finalized metrics, exposed for observability/tests.
        self.last_metrics: Any = None
        self._replan_count = 0
        # Per-turn accounting for the K15 history event (FR-9.1/9.5).
        self._turn_tools: list[str] = []
        self._turn_plan: PlanGraph | None = None
        self._turn_degraded_reason: str = ""
        self._turn_hitl: int = 0
        # Semantic intent key for template lookup + K15 aggregation (LOW-4).
        self._turn_intent_key: str = ""

    async def run(
        self,
        scratchpad: TurnScratchpad,
        ctx: TurnContext,
    ) -> AsyncIterator[
        ProgressEvent | SsePayloadEvent | FinalAnswerEvent | PendingHitlEvent | ClarifyEvent | ErrorEvent
    ]:
        """Run a turn and append exactly one K15 history event for its outcome.

        Centralizing history here (instead of per-mode) satisfies FR-9.1 ("after
        every turn") and FR-9.5 (distinct success/degraded/failure/hitl_pending/
        clarify_pending statuses) across reactive, plan, and HITL-resume paths.
        """
        question = self._original_question(scratchpad)
        self._turn_tools = []
        self._turn_plan = None
        self._turn_degraded_reason = ""
        self._turn_hitl = 0
        # Default to the raw-question key; replaced with the semantic key once the
        # IntentObject is available (in _dispatch).
        self._turn_intent_key = normalize_intent_key(question)
        self._replan_count = 0
        self._last_budget_hit = None
        status = STATUS_FAILURE
        try:
            async for event in self._dispatch(scratchpad, ctx):
                if isinstance(event, FinalAnswerEvent):
                    status = (
                        STATUS_DEGRADED
                        if (self._turn_degraded_reason or self._last_budget_hit)
                        else STATUS_SUCCESS
                    )
                elif isinstance(event, ClarifyEvent):
                    status = STATUS_CLARIFY_PENDING
                elif isinstance(event, PendingHitlEvent):
                    status = STATUS_HITL_PENDING
                elif isinstance(event, ErrorEvent):
                    status = STATUS_FAILURE
                yield event
        finally:
            self._record_turn_history(
                ctx=ctx,
                status=status,
                failure_kind=(self._turn_degraded_reason or self._last_budget_hit) or None,
            )

    async def _dispatch(
        self,
        scratchpad: TurnScratchpad,
        ctx: TurnContext,
    ) -> AsyncIterator[
        ProgressEvent | SsePayloadEvent | FinalAnswerEvent | PendingHitlEvent | ClarifyEvent | ErrorEvent
    ]:
        # Draft HITL resume (catalog/inventory) carries a pending tool; a data_query
        # clarification reply has none and just re-runs the loop with the resolved
        # question already folded into the scratchpad messages.
        if ctx.clarification_response is not None and (
            (ctx.pending_hitl_tool or "").strip() or _is_hitl_resume(ctx.clarification_response)
        ):
            async for event in self._resume_hitl(scratchpad, ctx):
                yield event
            return

        self._budget = self._new_budget()
        self._budget.start()
        self._last_budget_hit = None
        self._replan_count = 0
        recorder = (
            TraceRecorder(intent="unknown")
            if bool(getattr(self._settings, "agentic_trace_enabled", True))
            else None
        )
        # P5 — trim conversation history to the last N pairs before reasoning.
        if bool(getattr(self._settings, "agentic_intent_object_enabled", False)) or bool(
            getattr(self._settings, "working_memory_pairs", 0)
        ):
            scratchpad.messages = self._working_memory.attach(scratchpad.messages)
        try:
            if bool(getattr(self._settings, "agentic_intent_object_enabled", False)):
                intent_agent = IntentSubagent(llm_registry=self._llm_registry, settings=self._settings)
                intent = await intent_agent.analyze(
                    self._effective_question(scratchpad),
                    intent_context=IntentContextBuilder().build(
                        schema_text=self._tool_registry.tools_manifest_text(),
                        history_text=self._observations_text(scratchpad),
                        memory_text=self._memory_text(scratchpad),
                    ),
                )
                # Semantic intent key drives template lookup + K15 aggregation (LOW-4).
                self._turn_intent_key = _intent_key_from(
                    intent, fallback=self._original_question(scratchpad)
                )
                if recorder is not None:
                    recorder._intent = intent.intent_type or "unknown"
                if intent.mode == "clarify":
                    if recorder is not None:
                        recorder.record_hitl()
                    yield ClarifyEvent(
                        questions=intent.clarify_questions,
                        suggested_rewrite="",
                        original_question=self._original_question(scratchpad),
                    )
                    return
                ctx = replace(
                    ctx,
                    intent_object=intent.model_dump(mode="json"),
                    assumptions=list(intent.assumptions),
                )
                # P2 — opt-in plan-driven DAG for read/report intents.
                if bool(getattr(self._settings, "agentic_plan_dag_enabled", False)) and (
                    intent.intent_type in {"data_query", "chart_report"}
                ):
                    async for event in self._run_plan_mode(intent, scratchpad, ctx, recorder):
                        yield event
                    return

            max_steps = self._budget.max_steps
            seen_tool_calls: set[str] = set()
            for step in range(max_steps):
                scratchpad.step = step
                try:
                    decision = await self._decide(scratchpad)
                    self._budget.add_usage(self._last_llm_tokens, self._last_llm_cost)
                    if recorder is not None:
                        recorder.record_step(
                            step=step + 1,
                            tool="decision",
                            ok=True,
                            tokens=self._last_llm_tokens,
                            cost_usd=self._last_llm_cost,
                            latency_ms=0.0,
                        )
                    self._budget.check(step)
                except BudgetExceeded as exc:
                    self._last_budget_hit = exc.kind
                    if recorder is not None:
                        recorder.record_budget_hit(exc.kind)
                    self._audit_warn(f"{exc.kind}_budget_exhausted", ctx)
                    yield FinalAnswerEvent(scratchpad.observation_summary())
                    return
                except Exception as exc:  # noqa: BLE001
                    logger.warning("harness decision failed", exc_info=True)
                    yield ErrorEvent("Không đọc được quyết định điều phối.", "HARNESS_DECISION_ERROR")
                    return

                yield ProgressEvent(f"Bước {step + 1}: {decision.action}")
                if decision.action == "final_answer":
                    yield FinalAnswerEvent(decision.final_answer or "")
                    return

                if decision.action == "clarify":
                    clar = decision.clarify
                    questions = [q for q in (clar.questions if clar else []) if str(q).strip()]
                    if not questions:
                        # Planner asked to clarify but gave no question — answer directly
                        # rather than emitting an empty bubble.
                        yield FinalAnswerEvent(decision.final_answer or "")
                        return
                    yield ClarifyEvent(
                        questions=questions,
                        suggested_rewrite=(clar.suggested_rewrite if clar else "") or "",
                        original_question=self._original_question(scratchpad),
                    )
                    return

                if decision.tool_call is None:
                    yield ErrorEvent("Decision missing tool_call.", "HARNESS_DECISION_INVALID")
                    return

                tool_name = decision.tool_call.tool_name
                args = dict(decision.tool_call.args or {})

                # Guard against the planner re-issuing an identical tool call: the result
                # is deterministic, so repeating it only burns the step budget. Stop and
                # answer from what we already observed instead of looping to exhaustion.
                signature = f"{tool_name}:{json.dumps(args, sort_keys=True, ensure_ascii=False, default=str)}"
                if signature in seen_tool_calls:
                    self._audit_warn("duplicate_tool_call_short_circuit", ctx)
                    self._turn_degraded_reason = "duplicate"
                    yield FinalAnswerEvent(scratchpad.observation_summary())
                    return
                seen_tool_calls.add(signature)

                try:
                    self._check_policy(tool_name, args, ctx)
                    self._turn_tools.append(tool_name)
                    result = await self._run_tool_cached(
                        ToolInput(tool_name=tool_name, args=args, context=ctx)
                    )
                    self._budget.check(step)
                except BudgetExceeded as exc:
                    self._last_budget_hit = exc.kind
                    if recorder is not None:
                        recorder.record_budget_hit(exc.kind)
                    self._audit_warn(f"{exc.kind}_budget_exhausted", ctx)
                    yield FinalAnswerEvent(scratchpad.observation_summary())
                    return
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
                    if recorder is not None:
                        recorder.record_hitl()
                    self._turn_hitl += 1
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
            self._turn_degraded_reason = self._turn_degraded_reason or "step_budget"
            yield FinalAnswerEvent(scratchpad.observation_summary())
        finally:
            if recorder is not None:
                self.last_metrics = recorder.finalize()
                logger.info(
                    "harness_turn_metrics intent=%s steps=%s replans=%s hitl=%s tokens=%s cost_usd=%.6f budget_hit=%s",
                    self.last_metrics.intent,
                    self.last_metrics.steps,
                    self.last_metrics.replans,
                    self.last_metrics.hitl,
                    self.last_metrics.tokens,
                    self.last_metrics.cost_usd,
                    self.last_metrics.budget_hit or "-",
                )

    async def _resume_hitl(
        self,
        scratchpad: TurnScratchpad,
        ctx: TurnContext,
    ) -> AsyncIterator[ProgressEvent | SsePayloadEvent | FinalAnswerEvent | ErrorEvent]:
        tool_name = (ctx.pending_hitl_tool or "").strip()
        if not tool_name:
            yield ErrorEvent(
                "Phiên xác nhận đã hết hạn hoặc server đã khởi động lại. Vui lòng tạo lại nháp.",
                "HITL_EXPIRED",
            )
            return
        if tool_name not in {"catalog_draft", "inventory_draft"}:
            yield ErrorEvent(f"Không hỗ trợ xác nhận HITL cho tool {tool_name}.", "HITL_UNSUPPORTED_TOOL")
            return

        yield ProgressEvent("Đang xác nhận nháp đã duyệt.")
        args = {"request": "confirm"}
        try:
            self._check_policy(tool_name, args, ctx)
            self._turn_tools.append(tool_name)
            result = await self._harness_run_tool_async(ToolInput(tool_name=tool_name, args=args, context=ctx))
        except HarnessPolicyError as exc:
            yield ErrorEvent(str(exc), "HARNESS_POLICY_BLOCK")
            return
        except Exception as exc:  # noqa: BLE001
            logger.warning("harness HITL resume failed tool=%s", tool_name, exc_info=True)
            yield ErrorEvent(str(exc), "HITL_CONFIRM_FAILED")
            return

        if not result.ok:
            yield ErrorEvent(result.error_message or result.observation_text, "HITL_CONFIRM_FAILED")
            return
        if result.sse_payload:
            event_name = str(result.sse_payload.get("_event") or "data")
            payload = {k: v for k, v in result.sse_payload.items() if k != "_event"}
            yield SsePayloadEvent(event_name, payload)
        scratchpad.add_observation(result, tool_name)
        yield FinalAnswerEvent(result.observation_text)

    @staticmethod
    def _original_question(scratchpad: TurnScratchpad) -> str:
        for msg in reversed(scratchpad.messages):
            if isinstance(msg, HumanMessage):
                return str(msg.content)
        return ""

    @staticmethod
    def _effective_question(scratchpad: TurnScratchpad) -> str:
        """Return the question to use for intent analysis.

        If the latest user message is very short (a follow-up refinement like "năm 2026"),
        prepend the most recent substantive user question so the intent LLM has full context.
        """
        messages = scratchpad.messages
        latest = ""
        latest_idx = -1
        for i, msg in enumerate(reversed(messages)):
            if isinstance(msg, HumanMessage):
                latest = str(msg.content).strip()
                latest_idx = len(messages) - 1 - i
                break
        if not latest:
            return ""
        # A substantive question has at least 4 words or 20 chars; short ones are follow-ups.
        if len(latest) > 20 or len(latest.split()) >= 4:
            return latest
        # Find the previous substantive user message.
        for msg in reversed(messages[:latest_idx]):
            if isinstance(msg, HumanMessage):
                prev = str(msg.content).strip()
                if len(prev) > 20:
                    return f"{prev} — {latest}"
                break
        return latest

    async def _decide(self, scratchpad: TurnScratchpad) -> DecisionSchema:
        role = str(getattr(self._settings, "harness_planner_role", "harness_planner") or "harness_planner")
        client = self._resolve_decision_client(role)
        messages = scratchpad.to_decision_prompt(self._tool_registry.tools_manifest_text())
        decision = await client.astructured_predict(messages, DecisionSchema)
        self._last_llm_tokens, self._last_llm_cost = self._usage_from_client(client)
        return decision

    def _resolve_decision_client(self, default_role: str) -> Any:
        """Pick the model tier for the next-action decision (P7) with safe fallback."""
        if bool(getattr(self._settings, "agentic_model_routing_enabled", False)):
            tier = self._model_router.pick("planner", replan_count=self._replan_count)
            try:
                return self._llm_registry.get(tier)
            except Exception:  # noqa: BLE001 — tier role not registered; fall back.
                logger.debug("model tier role %s not registered; using %s", tier, default_role)
        return self._llm_registry.get(default_role)

    async def _run_tool_cached(self, tool_input: ToolInput) -> ToolResult:
        """Wrap deterministic tool calls with a tenant-scoped semantic cache (P7)."""
        if bool(getattr(self._settings, "agentic_semantic_cache_enabled", False)) and self._cache.is_cacheable(
            tool_input.tool_name
        ):
            cached = self._cache.get(tool_input.tool_name, tool_input.args, tool_input.context.tenant_id)
            if self._cache.last_event == "cache_hit":
                self._audit_warn("cache_hit", tool_input.context)
                return cached
            result = await self._harness_run_tool_async(tool_input)
            if result.ok and result.pending_hitl is None and not result.error_message:
                self._cache.put(tool_input.tool_name, tool_input.args, tool_input.context.tenant_id, result)
            return result
        return await self._harness_run_tool_async(tool_input)

    def _plan_error_answer(self, scratchpad: TurnScratchpad, reason: str = "plan_error") -> str:
        """Labeled degraded fallback so caught plan errors are not logged as success.

        Sets the turn's degraded reason (so run() records K15 'degraded', not clean
        'success' — FR-9.5) and labels the answer as incomplete (FR-1.6).
        """
        self._turn_degraded_reason = self._turn_degraded_reason or reason
        summary = scratchpad.observation_summary()
        return f"{degraded_final_answer(reason)}\n\n{summary}".strip()

    async def _run_plan_mode(
        self,
        intent: Any,
        scratchpad: TurnScratchpad,
        ctx: TurnContext,
        recorder: TraceRecorder | None,
    ) -> AsyncIterator[ProgressEvent | SsePayloadEvent | FinalAnswerEvent | ErrorEvent]:
        planner = PlannerSubagent(llm_registry=self._llm_registry, settings=self._settings)
        intent_dump = intent.model_dump(mode="json")
        manifest = self._tool_registry.tools_manifest_text()
        executor = PlanExecutor(tool_registry=self._tool_registry, policy=self._policy, harness=self._harness)

        max_replans = int(getattr(self._settings, "plan_replan_max", 2) or 0)
        degraded_reason = ""
        plan: PlanGraph | None = None
        results: list[NodeResult] = []

        template_hit = False
        if bool(getattr(self._settings, "agentic_v3_enabled", False)) and bool(
            getattr(self._settings, "agentic_v3_plan_template_enabled", False)
        ):
            template = self._get_plan_template(ctx)
            if template is not None and self._plan_is_template_safe(template.plan_graph):
                template_hit = True
                plan = template.plan_graph
                yield ProgressEvent("Execution tier: template")
                try:
                    outcome = await self._execute_v3_plan(
                        executor,
                        planner,
                        plan,
                        ctx,
                        intent_dump=intent_dump,
                        manifest=manifest,
                        recorder=recorder,
                        max_replans=max_replans,
                    )
                except Exception:  # noqa: BLE001
                    logger.warning("template plan execution failed", exc_info=True)
                    self._record_plan_template_outcome(ctx, "failure")
                    outcome = None
                if outcome is None:
                    template_hit = False
                elif not outcome.degraded:
                    self._record_plan_template_outcome(ctx, "success")
                    results = outcome.results
                else:
                    self._record_plan_template_outcome(ctx, "degraded")
                    template_hit = False
                    degraded_reason = ""

        if not template_hit:
            try:
                plan = await planner.plan(intent_dump, "", manifest)
            except Exception:  # noqa: BLE001
                logger.warning("planner failed; falling back to reactive summary", exc_info=True)
                yield FinalAnswerEvent(self._plan_error_answer(scratchpad))
                return

        if results:
            pass
        elif bool(getattr(self._settings, "agentic_v3_enabled", False)):
            # v3: Planner owns the replan decision; Harness only signals
            # replan_required via observations and enforces bounds/dedup/safety.
            try:
                outcome = await self._execute_v3_plan(
                    executor,
                    planner,
                    plan,
                    ctx,
                    intent_dump=intent_dump,
                    manifest=manifest,
                    recorder=recorder,
                    max_replans=max_replans,
                )
            except Exception:  # noqa: BLE001
                logger.warning("plan execution failed", exc_info=True)
                yield FinalAnswerEvent(self._plan_error_answer(scratchpad))
                return
            results = outcome.results
            if outcome.degraded:
                degraded_reason = outcome.stopped_reason
                self._note_template_non_success(ctx)
            elif plan is not None:
                # Clean success of a planner-generated plan feeds template promotion.
                self._consider_template_promotion(plan, ctx)
        else:
            async def _replan(_current: PlanGraph, results: list[NodeResult], attempt: int) -> PlanGraph:
                self._replan_count = attempt
                if recorder is not None:
                    recorder.record_replan()
                failed = [r.model_dump(mode="json") for r in results if not (r.ok and r.output_meets_expect)]
                return await planner.plan({"intent": intent_dump, "failed_nodes": failed}, "", manifest)

            try:
                results, _replans = await executor.execute_with_replan(
                    plan,
                    ctx,
                    replan=_replan,
                    max_replans=max_replans,
                )
            except Exception:  # noqa: BLE001
                logger.warning("plan execution failed", exc_info=True)
                yield FinalAnswerEvent(self._plan_error_answer(scratchpad))
                return

        for result in results:
            yield ProgressEvent(f"Plan node {result.node_id}: {'ok' if result.ok else 'fail'}")
            sse = self._sse_from_output(result.tool_result)
            if sse:
                event_name = str(sse.get("_event") or "data")
                payload = {k: v for k, v in sse.items() if k != "_event"}
                yield SsePayloadEvent(event_name, payload)
            scratchpad.add_observation(
                ToolResult(ok=result.ok, output=result.tool_result, observation_text=result.observation_text),
                result.node_id,
            )

        final_text = await self._compose_plan_answer(results, ctx)
        if degraded_reason:
            # FR-1.6: degraded answers must be explicitly labeled as incomplete.
            final_text = f"{degraded_final_answer(degraded_reason)}\n\n{final_text}".strip()
        # Hand the plan + degraded reason to the turn-level K15 recorder in run().
        self._turn_plan = plan
        if degraded_reason:
            self._turn_degraded_reason = degraded_reason
        yield FinalAnswerEvent(final_text)

    async def _execute_v3_plan(
        self,
        executor: PlanExecutor,
        planner: PlannerSubagent,
        plan: PlanGraph,
        ctx: TurnContext,
        *,
        intent_dump: dict[str, Any],
        manifest: str,
        recorder: TraceRecorder | None,
        max_replans: int,
    ) -> Any:
        result_store = InMemoryResultRefStore()

        async def _planner_replan(
            observations: list[ObservationEnvelope], attempt: int
        ) -> PlanGraph | None:
            self._replan_count = attempt
            if recorder is not None:
                recorder.record_replan()
            failed = [o.model_dump(mode="json") for o in observations if o.replan_required]
            try:
                return await planner.plan({"intent": intent_dump, "failed_nodes": failed}, "", manifest)
            except Exception:  # noqa: BLE001
                return None

        return await run_planner_owned_plan(
            executor,
            plan,
            ctx,
            registry=self._tool_registry,
            planner_replan=_planner_replan,
            max_replans=max_replans,
            result_store=result_store,
        )

    async def _compose_plan_answer(self, results: list[NodeResult], ctx: TurnContext) -> str:
        # A planner that included an answer_composer node already produced the answer.
        for result in reversed(results):
            answer = result.tool_result.get("answer_markdown") if isinstance(result.tool_result, dict) else None
            if answer:
                return str(answer)
        if bool(getattr(self._settings, "agentic_answer_composer_enabled", False)) and self._has_tool(
            "answer_composer"
        ):
            observations = [
                (
                    r.observation.model_dump(mode="json")
                    if r.observation is not None
                    else {"rows": _rows_of(r.tool_result)}
                )
                for r in results
                if r.ok
            ]
            self._check_policy("answer_composer", {"observations": observations}, ctx)
            res = await self._harness_run_tool_async(
                ToolInput(
                    tool_name="answer_composer",
                    args={"observations": observations, "assumptions": list(ctx.assumptions or [])},
                    context=ctx,
                )
            )
            return res.observation_text
        summary = "\n".join(r.observation_text for r in results if r.observation_text)
        return summary or "Đã xử lý yêu cầu theo kế hoạch."

    def _has_tool(self, name: str) -> bool:
        try:
            self._tool_registry.get_impl(name)
            return True
        except KeyError:
            return False

    def _get_plan_template(self, ctx: TurnContext) -> Any | None:
        store = self._plan_template_store
        if store is None:
            return None
        return store.get(
            self._turn_intent_key,
            role_scope=_role_scope(ctx),
            manifest_version=self._tool_registry.manifest_version,
            policy_version=POLICY_VERSION,
            asset_versions=_v3_asset_versions(),
        )

    def _record_plan_template_outcome(self, ctx: TurnContext, status: str) -> None:
        store = self._plan_template_store
        if store is None:
            return
        store.record_outcome(self._turn_intent_key, role_scope=_role_scope(ctx), status=status)

    def _consider_template_promotion(self, plan: PlanGraph, ctx: TurnContext) -> None:
        """Feed a clean planner-generated success into the promotion streak (FR-11.3)."""
        store = self._plan_template_store
        if store is None or not hasattr(store, "consider_promotion"):
            return
        if not bool(getattr(self._settings, "agentic_v3_plan_template_enabled", False)):
            return
        # FR-11.7: only promote once K12 route accuracy has cleared the threshold.
        # Until the eval/CI step writes a measured accuracy, promotion stays off.
        if not v3_rollout_allowed(
            float(getattr(self._settings, "agentic_v3_measured_route_accuracy", 0.0) or 0.0),
            float(getattr(self._settings, "agentic_v3_route_accuracy_threshold", 0.8) or 0.8),
        ):
            return
        candidate = PlanTemplateRecord(
            normalized_intent_key=self._turn_intent_key,
            plan_graph_hash=plan_graph_hash(plan),
            plan_graph=plan,
            manifest_version=self._tool_registry.manifest_version,
            policy_version=POLICY_VERSION,
            asset_versions=_v3_asset_versions(),
            role_scope=_role_scope(ctx),
            source=PLANNER_GENERATED,
        )
        promote_after = int(getattr(self._settings, "agentic_v3_template_promote_after", 3) or 3)
        store.consider_promotion(candidate, promote_after=promote_after)

    def _note_template_non_success(self, ctx: TurnContext) -> None:
        store = self._plan_template_store
        if store is None or not hasattr(store, "note_non_success"):
            return
        store.note_non_success(self._turn_intent_key, role_scope=_role_scope(ctx))

    def _record_turn_history(
        self,
        *,
        ctx: TurnContext,
        status: str,
        failure_kind: str | None = None,
    ) -> None:
        """Append one K15 event for the turn (FR-9.1/9.2/9.5).

        Uses the executed plan when one ran (plan/template mode); otherwise derives
        a reactive plan hash from the sequence of tools the loop actually called.
        Aggregated under the semantic intent key (LOW-4).
        """
        store = self._history_store
        if store is None:
            return
        plan = self._turn_plan
        if plan is not None and plan.nodes:
            plan_hash = plan_graph_hash(plan)
            tools = [node.tool for node in plan.nodes]
        else:
            tools = list(self._turn_tools)
            plan_hash = "reactive:" + hashlib.sha256(",".join(tools).encode("utf-8")).hexdigest()[:12]
        event = build_history_event(
            tenant_id=ctx.tenant_id,
            intent_key=self._turn_intent_key,
            plan_hash=plan_hash,
            tools=tools,
            status=status,
            replan_count=self._replan_count,
            hitl_count=self._turn_hitl,
            cost_usd=float(self._last_llm_cost or 0.0),
            asset_versions=_v3_asset_versions(),
            failure_kind=failure_kind,
        )
        store.append(event)

    def _plan_is_template_safe(self, plan: PlanGraph) -> bool:
        for node in plan.nodes:
            manifest = self._tool_registry.get_manifest(node.tool)
            if manifest is None:
                return False
            if manifest.side_effect_class == "non_idempotent_write":
                return False
        return True

    def _check_policy(self, tool_name: str, args: dict[str, Any], ctx: TurnContext) -> None:
        manifest = self._tool_registry.get_manifest(tool_name)
        self._policy.check(
            tool_name,
            args,
            role=ctx.role,
            permissions=ctx.permissions,
            tenant_id=ctx.tenant_id,
            rbac_required=manifest.rbac_required if manifest else (),
            side_effect_class=manifest.side_effect_class if manifest else None,
        )

    @staticmethod
    def _sse_from_output(output: Any) -> dict[str, Any] | None:
        if not isinstance(output, dict):
            return None
        if output.get("chartType") or output.get("chart_type"):
            return {"_event": "chart", **output}
        table = output.get("query_table_sse")
        if isinstance(table, dict):
            return {"_event": "data_table", **table}
        return None

    @staticmethod
    def _memory_text(scratchpad: TurnScratchpad) -> str:
        parts = [str(getattr(m, "content", "")) for m in scratchpad.messages[-6:]]
        return "\n".join(p for p in parts if p)

    @staticmethod
    def _observations_text(scratchpad: TurnScratchpad) -> str:
        if not scratchpad.observations:
            return ""
        parts = [
            f"- {obs.tool_name}: {obs.observation_text}"
            for obs in scratchpad.observations[-5:]
            if obs.ok and obs.observation_text
        ]
        return "\n".join(parts)

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
        tool = self._tool_registry.get_impl(tool_input.tool_name)
        return await self._harness.arun_tool(
            tool_name=tool_input.tool_name,
            tool=lambda: tool.invoke(tool_input.args, tool_input.context),
            context=ctx,
        )

    def _audit_warn(self, code: str, ctx: TurnContext) -> None:
        logger.warning(
            "harness_warn code=%s correlation_id=%s tenant_id=%s thread_id=%s",
            code,
            ctx.correlation_id,
            ctx.tenant_id or "-",
            ctx.thread_id or "-",
        )

    def _new_budget(self) -> TurnBudget:
        return TurnBudget(
            max_steps=int(getattr(self._settings, "harness_max_steps", 6)),
            token_budget=int(getattr(self._settings, "harness_token_budget", 0) or 0),
            cost_budget_usd=float(getattr(self._settings, "harness_cost_budget_usd", 0.0) or 0.0),
            wallclock_timeout_s=float(getattr(self._settings, "harness_wallclock_timeout_s", 30.0) or 0.0),
        )

    @staticmethod
    def _usage_from_client(client: Any) -> tuple[int, float]:
        usage = getattr(client, "last_usage", None)
        if usage is None:
            return 0, 0.0
        prompt = int(getattr(usage, "prompt_tokens", 0) or 0)
        completion = int(getattr(usage, "completion_tokens", 0) or 0)
        total = int(getattr(usage, "total_tokens", prompt + completion) or 0)
        cost = float(getattr(usage, "cost_usd", 0.0) or 0.0)
        return total, cost


def _rows_of(output: Any) -> list[dict[str, Any]]:
    if not isinstance(output, dict):
        return []
    rows = output.get("rows")
    if isinstance(rows, list):
        return [r for r in rows if isinstance(r, dict)]
    query_result = output.get("query_result")
    if isinstance(query_result, dict) and isinstance(query_result.get("rows"), list):
        return [r for r in query_result["rows"] if isinstance(r, dict)]
    return []


def _role_scope(ctx: TurnContext) -> str:
    """Template scope = role + a fingerprint of live permissions (P2-2).

    Two users with the same role but different live JWT permissions get distinct
    scopes, so one cannot poison/demote the other's template history even though
    policy is also re-checked per call (FR-5.4/AC-17).
    """
    role = str(ctx.role or "default").strip() or "default"
    perms = sorted(str(p).strip().lower() for p in (getattr(ctx, "permissions", ()) or ()) if str(p).strip())
    if not perms:
        return role
    digest = hashlib.sha256(",".join(perms).encode("utf-8")).hexdigest()[:8]
    return f"{role}#{digest}"


def _intent_key_from(intent: Any, *, fallback: str) -> str:
    """Build the semantic intent key from an IntentObject, or fall back to raw."""
    if intent is None:
        return normalize_intent_key(fallback)
    entities = [
        getattr(e, "matched", "") for e in (getattr(intent, "resolved_entities", None) or [])
    ]
    return build_intent_key(
        intent_type=getattr(intent, "intent_type", "") or "",
        goal=getattr(intent, "goal", "") or "",
        required_data=getattr(intent, "required_data", None) or [],
        entities=entities,
        fallback=fallback,
    )


def _v3_asset_versions() -> dict[str, str]:
    return {"K12": "1.0", "K15": "1.0"}


def _is_hitl_resume(clarification_response: dict[str, Any] | None) -> bool:
    if not isinstance(clarification_response, dict):
        return False
    kind = clarification_response.get("clarify_kind") or clarification_response.get("clarifyKind")
    return kind == "hitl_resume"
