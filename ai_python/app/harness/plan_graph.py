"""PlanGraph contracts and async DAG executor for agentic harness flows."""

from __future__ import annotations

import asyncio
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field, replace
from typing import Any

from pydantic import BaseModel, Field

from app.harness.observation import ObservationEnvelope, build_observation
from app.harness.policy import HarnessPolicy
from app.harness.runtime import AgentHarness, ToolCallContext
from app.harness.tool_registry import (
    ToolInput,
    ToolRegistry,
    ToolResult,
    TurnContext,
    can_silent_retry,
)


class PlanNode(BaseModel):
    id: str
    tool: str
    needs: list[str] = Field(default_factory=list)
    input_spec: dict[str, Any] = Field(default_factory=dict)
    output_expect: str = ""


class PlanGraph(BaseModel):
    nodes: list[PlanNode] = Field(default_factory=list)


class PlanGraphOutput(PlanGraph):
    pass


class NodeResult(BaseModel):
    node_id: str
    ok: bool
    output_meets_expect: bool
    tool_result: dict[str, Any] = Field(default_factory=dict)
    observation_text: str = ""
    error: str = ""
    observation: ObservationEnvelope | None = None


_PLANNER_SYSTEM = (
    "You design an execution PlanGraph (a DAG) for a Smart ERP assistant.\n"
    "Output JSON: nodes=[{id, tool, needs, input_spec, output_expect}].\n"
    "Rules:\n"
    "- id: unique short string. tool: MUST be one of the listed tools.\n"
    "- needs: ids of nodes whose output this node depends on; independent nodes "
    "(empty needs) run in parallel, so only add a dependency when data must flow.\n"
    "- input_spec: arguments for the tool. To pass a parent node's output into a "
    "child, reference it as \"${parent_id.field}\" (e.g. {\"rows\": \"${rev.rows}\"} "
    "or {\"observations\": [{\"rows\": \"${rev.rows}\"}]}). Only reference ids listed "
    "in this node's needs.\n"
    "- output_expect: short phrase, use 'rows' for tabular data, 'answer' for the "
    "final composed answer.\n"
    "- Keep the plan minimal. End read/report plans with an answer_composer node "
    "(when available) that needs the data nodes."
)


class PlannerSubagent:
    def __init__(self, *, llm_registry: Any, settings: Any | None = None) -> None:
        self._llm_registry = llm_registry
        self._settings = settings

    async def plan(self, intent: Any, dictionary_text: str = "", tools_manifest: str = "") -> PlanGraph:
        _ = self._settings
        client = self._llm_registry.get("planner")
        user = f"Tools:\n{tools_manifest or '(none listed)'}\n\nintent={intent}\ndictionary={dictionary_text}"
        out = await client.astructured_predict(
            [
                {"role": "system", "content": _PLANNER_SYSTEM},
                {"role": "user", "content": user},
            ],
            PlanGraphOutput,
        )
        return PlanGraph(nodes=out.nodes)


class PlanExecutor:
    def __init__(
        self,
        *,
        tool_registry: ToolRegistry,
        policy: HarnessPolicy,
        harness: AgentHarness,
    ) -> None:
        self._tool_registry = tool_registry
        self._policy = policy
        self._harness = harness

    async def execute(
        self,
        plan: PlanGraph,
        ctx: TurnContext,
        *,
        result_store: Any | None = None,
    ) -> list[NodeResult]:
        pending = {node.id: node for node in plan.nodes}
        succeeded: set[str] = set()
        # hard_failed: ok=False — blocks all downstream nodes (FR-6 guardrail).
        # validation_failed: ok=True but output_meets_expect=False — triggers replan
        # but does NOT cascade-block dependents; the planner decides whether to retry.
        hard_failed: set[str] = set()
        validation_failed: set[str] = set()
        results: list[NodeResult] = []
        # Outputs of completed nodes, addressable by downstream input_spec refs
        # of the form ``${node_id.path}`` (data-flow binding between DAG nodes).
        outputs: dict[str, dict[str, Any]] = {}
        while pending:
            # FR-6 / guardrail (P1-1): a node whose dependency HARD-FAILED must never
            # run — otherwise a write/draft tool could execute after a failed lookup.
            # Validation failures (ok=True but unexpected output shape) only set
            # replan_required; they do not cascade-block downstream nodes.
            blocked = [
                node
                for node in plan.nodes
                if node.id in pending and any(dep in hard_failed for dep in node.needs)
            ]
            if blocked:
                for node in blocked:
                    results.append(
                        NodeResult(
                            node_id=node.id,
                            ok=False,
                            output_meets_expect=False,
                            error="skipped: dependency failed",
                        )
                    )
                    hard_failed.add(node.id)
                    pending.pop(node.id, None)
                continue

            ready = [
                node
                for node in plan.nodes
                if node.id in pending
                and all(dep in succeeded or dep in validation_failed for dep in node.needs)
            ]
            if not ready:
                for node_id in list(pending):
                    results.append(
                        NodeResult(
                            node_id=node_id,
                            ok=False,
                            output_meets_expect=False,
                            error="plan dependency cycle or missing dependency",
                        )
                    )
                    hard_failed.add(node_id)
                    pending.pop(node_id, None)
                break
            # Resolve each ready node's args against already-succeeded node outputs
            # BEFORE launching the layer (every dependency is guaranteed complete).
            layer = [(node, _resolve_refs(dict(node.input_spec or {}), outputs)) for node in ready]
            layer_results = await asyncio.gather(
                *(self._execute_node(node, args, ctx, result_store=result_store) for node, args in layer)
            )
            results.extend(layer_results)
            for result in layer_results:
                pending.pop(result.node_id, None)
                outputs[result.node_id] = result.tool_result if isinstance(result.tool_result, dict) else {}
                if result.ok and result.output_meets_expect:
                    succeeded.add(result.node_id)
                elif result.ok and not result.output_meets_expect:
                    validation_failed.add(result.node_id)
                else:
                    hard_failed.add(result.node_id)
        return results

    async def execute_with_replan(
        self,
        plan: PlanGraph,
        ctx: TurnContext,
        *,
        replan: Callable[[PlanGraph, list[NodeResult], int], Awaitable[PlanGraph]],
        max_replans: int,
    ) -> tuple[list[NodeResult], int]:
        replan_count = 0
        current = plan
        results = await self.execute(current, ctx)
        while self.needs_replan(results) and replan_count < max_replans:
            replan_count += 1
            current = await replan(current, results, replan_count)
            results = await self.execute(current, ctx)
        return results, replan_count

    def needs_replan(self, results: list[NodeResult]) -> bool:
        return any((not result.ok) or (not result.output_meets_expect) for result in results)

    async def _execute_node(
        self,
        node: PlanNode,
        args: dict[str, Any],
        ctx: TurnContext,
        *,
        result_store: Any | None = None,
    ) -> NodeResult:
        try:
            manifest = self._tool_registry.get_manifest(node.tool)
            self._policy.check(
                node.tool,
                args,
                role=ctx.role,
                permissions=ctx.permissions,
                tenant_id=ctx.tenant_id,
                rbac_required=manifest.rbac_required if manifest else (),
                side_effect_class=manifest.side_effect_class if manifest else None,
            )
            tool = self._tool_registry.get_impl(node.tool)
            result: ToolResult = await self._harness.arun_tool(
                tool_name=node.tool,
                tool=lambda: tool.invoke(args, ctx),
                context=ToolCallContext(
                    tool_name=node.tool,
                    correlation_id=ctx.correlation_id,
                    tenant_id=ctx.tenant_id,
                    thread_id=ctx.thread_id,
                ),
            )
            output_meets_expect = _output_meets_expect(result, node.output_expect)
            observation: ObservationEnvelope | None = None
            output = dict(result.output or {})
            if result_store is not None:
                observation = build_observation(
                    tool_name=node.tool,
                    tool_result=result,
                    ctx=ctx,
                    result_store=result_store,
                    output_meets_expect=output_meets_expect,
                )
                output = _planner_safe_output(output, observation)
            return NodeResult(
                node_id=node.id,
                ok=bool(result.ok),
                output_meets_expect=output_meets_expect,
                tool_result=output,
                observation_text=result.observation_text,
                # Carry the tool's failure detail so the v3 observation layer can
                # fingerprint it for dedup (sanitized before reaching the Planner).
                error="" if result.ok else (result.error_message or result.observation_text or ""),
                observation=observation,
            )
        except Exception as exc:  # noqa: BLE001
            return NodeResult(
                node_id=node.id,
                ok=False,
                output_meets_expect=False,
                error=str(exc),
            )


_REF_FULL = re.compile(r"^\$\{([^}]+)\}$")
_REF_EMBED = re.compile(r"\$\{([^}]+)\}")


def _resolve_refs(value: Any, outputs: dict[str, dict[str, Any]]) -> Any:
    """Resolve ``${node_id.path}`` references in a node's input_spec against the
    outputs of already-completed nodes. Non-reference values pass through unchanged,
    so a static input_spec keeps working exactly as before.
    """
    if isinstance(value, str):
        full = _REF_FULL.match(value.strip())
        if full:
            return _lookup(full.group(1), outputs)
        if "${" in value:
            return _REF_EMBED.sub(lambda m: str(_lookup(m.group(1), outputs) or ""), value)
        return value
    if isinstance(value, dict):
        return {key: _resolve_refs(item, outputs) for key, item in value.items()}
    if isinstance(value, list):
        return [_resolve_refs(item, outputs) for item in value]
    return value


def _lookup(path: str, outputs: dict[str, dict[str, Any]]) -> Any:
    parts = [p for p in path.split(".") if p]
    if not parts:
        return None
    current: Any = outputs.get(parts[0])
    for part in parts[1:]:
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


def _planner_safe_output(output: dict[str, Any], observation: ObservationEnvelope) -> dict[str, Any]:
    """Planner/downstream-safe node output for v3 result_ref data-flow.

    Full row sets and raw SQL internals stay in ``ResultRefStore``. Child nodes
    bind to ``result_ref`` and resolve through Harness-scoped context.
    """
    if observation.result_ref:
        safe: dict[str, Any] = {
            "result_ref": observation.result_ref,
            "row_count": observation.row_count,
            "schema_fields": list(observation.schema_fields),
            "aggregate_stats": dict(observation.aggregate_stats),
            "sample_rows": list(observation.sample_rows),
            "truncated": observation.truncated,
            "masked": observation.masked,
        }
        if observation.artifact_refs:
            safe["artifact_refs"] = list(observation.artifact_refs)
        return safe

    blocked = {"rows", "query_result", "generated_sql", "sql"}
    return {key: value for key, value in output.items() if key not in blocked}


# ---------------------------------------------------------------------------
# v3 (SRS-006) planner-owned replan
#
# The Harness only signals ``replan_required`` via sanitized observations and
# enforces bounds/dedup/side-effect safety. The Planner — through the
# ``planner_replan`` callback — owns the decision to replan, stop, or degrade.
# The executor never synthesizes the next plan itself (FR-6.1, AR-1/AR-2).
# ---------------------------------------------------------------------------

# Planner callback: given the current observations and the next attempt index,
# return a new PlanGraph to try, or None to stop (planner chose to give up/degrade).
PlannerReplan = Callable[[list[ObservationEnvelope], int], Awaitable["PlanGraph | None"]]


@dataclass
class ReplanOutcome:
    results: list[NodeResult]
    observations: list[ObservationEnvelope] = field(default_factory=list)
    replan_count: int = 0
    stopped_reason: str = "ok"  # ok|max_replans|duplicate|non_idempotent_block|planner_stop
    degraded: bool = False


def _node_tool_map(plan: PlanGraph) -> dict[str, str]:
    return {node.id: node.tool for node in plan.nodes}


def _results_to_observations(
    results: list[NodeResult],
    *,
    node_tool: dict[str, str],
    ctx: TurnContext,
    registry: ToolRegistry,
    result_store: Any | None,
) -> list[ObservationEnvelope]:
    observations: list[ObservationEnvelope] = []
    for r in results:
        if r.observation is not None:
            observations.append(r.observation)
            continue
        tool_name = node_tool.get(r.node_id, r.node_id)
        adapted = ToolResult(
            ok=bool(r.ok),
            output=dict(r.tool_result or {}),
            observation_text=r.observation_text,
            error_message=r.error or None,
        )
        observations.append(
            build_observation(
                tool_name=tool_name,
                tool_result=adapted,
                ctx=ctx,
                result_store=result_store,
                output_meets_expect=bool(r.output_meets_expect),
            )
        )
    return observations


def _has_non_idempotent_failure(
    results: list[NodeResult], node_tool: dict[str, str], registry: ToolRegistry
) -> bool:
    for r in results:
        if r.ok and r.output_meets_expect:
            continue
        manifest = registry.get_manifest(node_tool.get(r.node_id, ""))
        side_effect = manifest.side_effect_class if manifest else "read_only"
        if not can_silent_retry(side_effect):
            return True
    return False


async def run_planner_owned_plan(
    executor: "PlanExecutor",
    plan: PlanGraph,
    ctx: TurnContext,
    *,
    registry: ToolRegistry,
    planner_replan: PlannerReplan,
    max_replans: int,
    result_store: Any | None = None,
) -> ReplanOutcome:
    """Execute a plan, surfacing failures to the Planner for the replan decision.

    Guarantees:
    - Harness emits ``replan_required`` observations, never picks the next plan.
    - Replan count is bounded (FR-6.4).
    - Duplicate failure fingerprints short-circuit (FR-6.5).
    - ``non_idempotent_write`` failures are never silently retried (FR-6.6).
    """
    max_replans = max(0, int(max_replans))
    exec_ctx = replace(ctx, result_store=result_store) if result_store is not None else ctx
    seen_fingerprints: set[str] = set()
    replan_count = 0
    current = plan
    node_tool = _node_tool_map(current)
    results = await executor.execute(current, exec_ctx, result_store=result_store)

    while True:
        node_tool = _node_tool_map(current)
        observations = _results_to_observations(
            results, node_tool=node_tool, ctx=exec_ctx, registry=registry, result_store=result_store
        )
        failing = [o for o in observations if o.replan_required]
        if not failing:
            return ReplanOutcome(results, observations, replan_count, "ok", False)

        # FR-6.6: a non-idempotent write must not be silently retried.
        if _has_non_idempotent_failure(results, node_tool, registry):
            return ReplanOutcome(results, observations, replan_count, "non_idempotent_block", True)

        # FR-6.5: identical failure fingerprint(s) => stop instead of looping.
        fps = {o.failure_fingerprint for o in failing if o.failure_fingerprint}
        if fps and fps <= seen_fingerprints:
            return ReplanOutcome(results, observations, replan_count, "duplicate", True)
        seen_fingerprints |= fps

        # FR-6.4: bounded replans.
        if replan_count >= max_replans:
            return ReplanOutcome(results, observations, replan_count, "max_replans", True)

        # Planner — not Harness — chooses the next plan (or stops).
        next_plan = await planner_replan(observations, replan_count + 1)
        if next_plan is None or not next_plan.nodes:
            return ReplanOutcome(results, observations, replan_count, "planner_stop", True)
        replan_count += 1
        current = next_plan
        results = await executor.execute(current, exec_ctx, result_store=result_store)


def degraded_final_answer(reason: str = "", missing: str = "") -> str:
    """Vietnamese incomplete-answer label for degraded outcomes (FR-1.6)."""
    detail = {
        "max_replans": "hệ thống đã thử lại nhiều lần nhưng chưa lấy đủ dữ liệu",
        "duplicate": "kế hoạch lặp lại cùng một lỗi nên đã dừng",
        "non_idempotent_block": "thao tác ghi không thể tự thử lại an toàn",
        "planner_stop": "chưa tìm được cách hoàn thành an toàn",
        "plan_error": "gặp lỗi khi lập hoặc chạy kế hoạch",
        "step_budget": "đã đạt giới hạn số bước xử lý",
    }.get(reason, "chưa lấy đủ dữ liệu cần thiết")
    text = f"⚠️ Câu trả lời chưa đầy đủ: {detail}."
    if missing:
        text += f" Thiếu: {missing}."
    return text


def _output_meets_expect(result: ToolResult, output_expect: str) -> bool:
    expect = (output_expect or "").casefold()
    if not expect:
        return True
    output = result.output or {}
    if "rows" in expect:
        # A present rows key satisfies the expectation even when empty: an explicit
        # zero-row result is a valid answer for a list/table request (P2-1). The
        # sql tool already does its own empty-retry before returning here.
        rows = output.get("rows")
        if isinstance(rows, list):
            return True
        query_result = output.get("query_result")
        if isinstance(query_result, dict):
            return isinstance(query_result.get("rows"), list)
        return False
    if "answer" in expect:
        return bool(output.get("answer_markdown") or result.observation_text)
    return bool(result.ok)
