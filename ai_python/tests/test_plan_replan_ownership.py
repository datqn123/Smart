"""Slice C — planner-owned replan (SRS-006 FR-6, AR-1/AR-2, QA TC-C)."""

from __future__ import annotations

import pytest

from app.harness.plan_graph import (
    PlanExecutor,
    PlanGraph,
    PlanNode,
    degraded_final_answer,
    run_planner_owned_plan,
)
from app.harness.policy import HarnessPolicy
from app.harness.runtime import AgentHarness
from app.harness.tool_registry import ToolManifest, ToolRegistry, ToolResult, TurnContext


def _ctx() -> TurnContext:
    return TurnContext(
        tenant_id="t1",
        user_id="u1",
        thread_id="th1",
        correlation_id="cid",
        bearer_token=None,
        schema_version=None,
    )


def _registry(name: str, tool, *, side_effect_class: str = "read_only") -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(
        ToolManifest(
            name=name,
            description=name,
            args_schema="{}",
            capability="data_read",
            side_effect_class=side_effect_class,
        ),
        tool,
    )
    return registry


def _executor(registry: ToolRegistry) -> PlanExecutor:
    return PlanExecutor(
        tool_registry=registry, policy=HarnessPolicy(), harness=AgentHarness(enabled=False)
    )


def _plan(tool: str = "a") -> PlanGraph:
    return PlanGraph(nodes=[PlanNode(id="n1", tool=tool, needs=[], input_spec={}, output_expect="rows")])


# --- TC-C-001: failed tool emits replan_required observation --------------

@pytest.mark.asyncio
async def test_failed_tool_emits_replan_required_observation():
    class Tool:
        async def invoke(self, args, ctx):  # noqa: ANN001
            return ToolResult(ok=False, output={}, observation_text="", error_message="boom")

    registry = _registry("a", Tool())

    async def planner_replan(observations, attempt):  # noqa: ANN001
        return None  # stop immediately — we only inspect observations

    outcome = await run_planner_owned_plan(
        _executor(registry), _plan(), _ctx(),
        registry=registry, planner_replan=planner_replan, max_replans=2,
    )
    assert outcome.observations[0].replan_required is True
    assert outcome.observations[0].ok is False


# --- TC-C-002: planner (not harness) chooses replacement plan -------------

@pytest.mark.asyncio
async def test_planner_owns_replan_decision():
    calls = {"planner": 0}

    class Tool:
        def __init__(self) -> None:
            self.n = 0

        async def invoke(self, args, ctx):  # noqa: ANN001
            self.n += 1
            if args.get("fix"):
                return ToolResult(ok=True, output={"rows": [{"id": 1}]}, observation_text="ok")
            return ToolResult(ok=False, output={}, observation_text="", error_message="boom")

    registry = _registry("a", Tool())

    async def planner_replan(observations, attempt):  # noqa: ANN001
        calls["planner"] += 1
        return PlanGraph(
            nodes=[PlanNode(id="n1", tool="a", needs=[], input_spec={"fix": True}, output_expect="rows")]
        )

    outcome = await run_planner_owned_plan(
        _executor(registry), _plan(), _ctx(),
        registry=registry, planner_replan=planner_replan, max_replans=2,
    )
    assert calls["planner"] == 1  # planner was consulted for the new plan
    assert outcome.stopped_reason == "ok"
    assert outcome.degraded is False
    assert outcome.replan_count == 1


# --- TC-C-003: duplicate failure fingerprint short-circuits ---------------

@pytest.mark.asyncio
async def test_duplicate_fingerprint_short_circuits():
    class Tool:
        async def invoke(self, args, ctx):  # noqa: ANN001
            return ToolResult(ok=False, output={}, observation_text="", error_message="same error")

    registry = _registry("a", Tool())
    planner_calls = {"n": 0}

    async def planner_replan(observations, attempt):  # noqa: ANN001
        planner_calls["n"] += 1
        return _plan()  # same plan -> same fingerprint

    outcome = await run_planner_owned_plan(
        _executor(registry), _plan(), _ctx(),
        registry=registry, planner_replan=planner_replan, max_replans=5,
    )
    assert outcome.stopped_reason == "duplicate"
    assert outcome.degraded is True
    # stopped on the repeat, well before exhausting max_replans=5
    assert outcome.replan_count == 1


# --- TC-C-004: replan count bounded -> degraded labeled answer -------------

@pytest.mark.asyncio
async def test_replan_count_bounded_then_degraded():
    class Tool:
        def __init__(self) -> None:
            self.n = 0

        async def invoke(self, args, ctx):  # noqa: ANN001
            self.n += 1
            # distinct error each time so dedup does not trigger before the cap
            return ToolResult(ok=False, output={}, observation_text="", error_message=f"err-{self.n}")

    registry = _registry("a", Tool())

    async def planner_replan(observations, attempt):  # noqa: ANN001
        # planner keeps trying a (distinctly-failing) plan
        return PlanGraph(
            nodes=[PlanNode(id=f"n{attempt}", tool="a", needs=[], input_spec={}, output_expect="rows")]
        )

    outcome = await run_planner_owned_plan(
        _executor(registry), _plan(), _ctx(),
        registry=registry, planner_replan=planner_replan, max_replans=2,
    )
    assert outcome.stopped_reason == "max_replans"
    assert outcome.replan_count == 2
    assert outcome.degraded is True
    label = degraded_final_answer(outcome.stopped_reason)
    assert "chưa đầy đủ" in label


# --- TC-C-005: non-idempotent write is not retried silently ---------------

@pytest.mark.asyncio
async def test_non_idempotent_write_not_retried():
    class Tool:
        def __init__(self) -> None:
            self.executions = 0

        async def invoke(self, args, ctx):  # noqa: ANN001
            self.executions += 1
            return ToolResult(ok=False, output={}, observation_text="", error_message="write failed")

    tool = Tool()
    registry = _registry("inventory_draft", tool, side_effect_class="non_idempotent_write")
    planner_calls = {"n": 0}

    async def planner_replan(observations, attempt):  # noqa: ANN001
        planner_calls["n"] += 1
        return _plan("inventory_draft")

    outcome = await run_planner_owned_plan(
        _executor(registry), _plan("inventory_draft"), _ctx(),
        registry=registry, planner_replan=planner_replan, max_replans=3,
    )
    assert outcome.stopped_reason == "non_idempotent_block"
    assert tool.executions == 1  # never silently re-run
    assert planner_calls["n"] == 0  # not auto-replanned
    assert outcome.degraded is True


# --- TC-C-006: failure detail hides raw SQL internals ---------------------

@pytest.mark.asyncio
async def test_failure_observation_hides_raw_sql():
    class Tool:
        async def invoke(self, args, ctx):  # noqa: ANN001
            return ToolResult(
                ok=False,
                output={},
                observation_text="",
                error_message="error running SELECT * FROM financeledger WHERE id=1",
            )

    registry = _registry("a", Tool())

    async def planner_replan(observations, attempt):  # noqa: ANN001
        return None

    outcome = await run_planner_owned_plan(
        _executor(registry), _plan(), _ctx(),
        registry=registry, planner_replan=planner_replan, max_replans=1,
    )
    obs = outcome.observations[0]
    assert "financeledger" not in obs.message
    assert "SELECT" not in obs.message.upper()
