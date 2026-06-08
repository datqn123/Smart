"""P1-1 + P2-1: dependency-failure gating and empty-result flow in PlanExecutor."""

from __future__ import annotations

import pytest

from app.harness.observation import build_observation
from app.harness.plan_graph import PlanExecutor, PlanGraph, PlanNode
from app.harness.policy import HarnessPolicy
from app.harness.result_store import InMemoryResultRefStore
from app.harness.runtime import AgentHarness
from app.harness.tool_registry import ToolManifest, ToolRegistry, ToolResult, TurnContext


def _ctx(store=None):
    return TurnContext(
        tenant_id="t1", user_id="u1", thread_id="th1", correlation_id="cid",
        bearer_token=None, schema_version=None, role="owner", permissions=("data_read", "draft_create"),
        result_store=store,
    )


def _executor(registry):
    return PlanExecutor(tool_registry=registry, policy=HarnessPolicy(), harness=AgentHarness(enabled=False))


# --- P1-1: a child must not run after its dependency fails -----------------

@pytest.mark.asyncio
async def test_downstream_write_skipped_when_dependency_fails():
    ran = {"draft": 0}

    class FailingLookup:
        async def invoke(self, args, ctx):  # noqa: ANN001
            return ToolResult(ok=False, output={}, observation_text="", error_message="lookup boom")

    class DraftTool:
        async def invoke(self, args, ctx):  # noqa: ANN001
            ran["draft"] += 1
            return ToolResult(ok=True, output={"draft": {"id": 1}}, observation_text="created")

    registry = ToolRegistry()
    registry.register(
        ToolManifest(name="sql_query", description="d", args_schema="{}", capability="data_read"),
        FailingLookup(),
    )
    registry.register(
        ToolManifest(
            name="inventory_draft", description="d", args_schema="{}",
            capability="draft_create", side_effect_class="non_idempotent_write",
        ),
        DraftTool(),
    )
    plan = PlanGraph(nodes=[
        PlanNode(id="lk", tool="sql_query", input_spec={"query": "x"}, output_expect="rows"),
        PlanNode(id="dr", tool="inventory_draft", needs=["lk"], input_spec={"r": "${lk.rows}"}, output_expect=""),
    ])

    results = await _executor(registry).execute(plan, _ctx())

    by_id = {r.node_id: r for r in results}
    assert by_id["lk"].ok is False
    assert by_id["dr"].ok is False
    assert "skipped" in by_id["dr"].error
    assert ran["draft"] == 0  # the write tool never executed


@pytest.mark.asyncio
async def test_validation_failed_does_not_block_dependent() -> None:
    """ok=True but output_meets_expect=False must NOT cascade-block downstream nodes."""
    ran: dict[str, int] = {"b": 0}

    class ShapeMismatch:
        """Returns ok=True but without a 'rows' key, triggering output_meets_expect=False."""
        async def invoke(self, args, ctx):  # noqa: ANN001
            return ToolResult(ok=True, output={"answer_markdown": "something"}, observation_text="ok")

    class OkTool:
        async def invoke(self, args, ctx):  # noqa: ANN001
            ran["b"] += 1
            return ToolResult(ok=True, output={"rows": [{"x": 1}]}, observation_text="ok")

    registry = ToolRegistry()
    registry.register(
        ToolManifest(name="node_a", description="d", args_schema="{}", capability="data_read"),
        ShapeMismatch(),
    )
    registry.register(
        ToolManifest(name="node_b", description="d", args_schema="{}", capability="data_read"),
        OkTool(),
    )
    plan = PlanGraph(nodes=[
        PlanNode(id="a", tool="node_a", input_spec={}, output_expect="rows"),
        PlanNode(id="b", tool="node_b", needs=["a"], input_spec={}, output_expect="rows"),
    ])

    results = await _executor(registry).execute(plan, _ctx())
    by_id = {r.node_id: r for r in results}

    assert ran["b"] == 1, "node_b should run even though node_a had output_meets_expect=False"
    assert by_id["a"].ok is True
    assert by_id["a"].output_meets_expect is False
    assert by_id["b"].ok is True


@pytest.mark.asyncio
async def test_hard_failed_still_blocks_dependent() -> None:
    """ok=False (hard failure) must still cascade-block all downstream nodes (FR-6)."""
    ran: dict[str, int] = {"b": 0}

    class HardFail:
        async def invoke(self, args, ctx):  # noqa: ANN001
            return ToolResult(ok=False, output={}, observation_text="", error_message="boom")

    class OkTool:
        async def invoke(self, args, ctx):  # noqa: ANN001
            ran["b"] += 1
            return ToolResult(ok=True, output={"rows": []}, observation_text="ok")

    registry = ToolRegistry()
    registry.register(
        ToolManifest(name="node_a", description="d", args_schema="{}", capability="data_read"),
        HardFail(),
    )
    registry.register(
        ToolManifest(name="node_b", description="d", args_schema="{}", capability="data_read"),
        OkTool(),
    )
    plan = PlanGraph(nodes=[
        PlanNode(id="a", tool="node_a", input_spec={}, output_expect="rows"),
        PlanNode(id="b", tool="node_b", needs=["a"], input_spec={}, output_expect="rows"),
    ])

    results = await _executor(registry).execute(plan, _ctx())
    by_id = {r.node_id: r for r in results}

    assert ran["b"] == 0, "node_b must NOT run after node_a hard-failed"
    assert by_id["b"].ok is False
    assert "skipped" in by_id["b"].error


@pytest.mark.asyncio
async def test_independent_node_still_runs_when_sibling_fails():
    ran = {"b": 0}

    class Fail:
        async def invoke(self, args, ctx):  # noqa: ANN001
            return ToolResult(ok=False, output={}, observation_text="", error_message="boom")

    class Ok:
        async def invoke(self, args, ctx):  # noqa: ANN001
            ran["b"] += 1
            return ToolResult(ok=True, output={"rows": [{"x": 1}]}, observation_text="ok")

    registry = ToolRegistry()
    registry.register(ToolManifest(name="a", description="d", args_schema="{}", capability="data_read"), Fail())
    registry.register(ToolManifest(name="b", description="d", args_schema="{}", capability="data_read"), Ok())
    plan = PlanGraph(nodes=[
        PlanNode(id="n1", tool="a", input_spec={}, output_expect="rows"),
        PlanNode(id="n2", tool="b", input_spec={}, output_expect="rows"),  # independent
    ])

    results = await _executor(registry).execute(plan, _ctx())
    assert ran["b"] == 1  # independent node not blocked by the sibling failure


# --- P2-1: empty result is valid and flows to a table builder --------------

def test_empty_ok_result_gets_result_ref_and_meets_expect():
    store = InMemoryResultRefStore()
    obs = build_observation(
        tool_name="sql_query",
        tool_result=ToolResult(ok=True, output={"rows": []}, observation_text="0 rows"),
        ctx=_ctx(store),
        result_store=store,
    )
    assert obs.ok is True
    assert obs.row_count == 0
    assert obs.truncated is False
    assert obs.result_ref is not None  # zero-row data still addressable
    assert obs.replan_required is False  # empty is a valid answer, not a failure


@pytest.mark.asyncio
async def test_empty_query_flows_to_zero_row_table():
    from app.graph.tools.data_table_builder import DataTableBuilderTool

    class EmptySql:
        async def invoke(self, args, ctx):  # noqa: ANN001
            return ToolResult(ok=True, output={"rows": []}, observation_text="0 rows")

    registry = ToolRegistry()
    registry.register(
        ToolManifest(
            name="sql_query", description="d", args_schema="{}",
            capability="data_read", result_ref_policy="result_ref",
        ),
        EmptySql(),
    )
    registry.register(DataTableBuilderTool.manifest, DataTableBuilderTool())
    store = InMemoryResultRefStore()
    plan = PlanGraph(nodes=[
        PlanNode(id="q", tool="sql_query", input_spec={"query": "x"}, output_expect="rows"),
        PlanNode(id="t", tool="data_table_builder", needs=["q"],
                 input_spec={"result_ref": "${q.result_ref}"}, output_expect="data_table"),
    ])

    results = await _executor(registry).execute(plan, _ctx(store), result_store=store)
    by_id = {r.node_id: r for r in results}
    assert by_id["q"].ok is True
    assert by_id["t"].ok is True  # table builder ran on the empty result
    assert by_id["t"].tool_result["query_table_sse"]["row_count"] == 0
