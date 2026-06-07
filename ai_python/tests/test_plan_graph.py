from __future__ import annotations

import pytest


def _ctx():
    from app.harness.tool_registry import TurnContext

    return TurnContext(
        tenant_id="t1",
        user_id="u1",
        thread_id="thread-1",
        correlation_id="corr-1",
        bearer_token=None,
        schema_version=None,
    )


def _registry(tools):  # noqa: ANN001
    from app.harness.tool_registry import ToolManifest, ToolRegistry

    registry = ToolRegistry()
    for name, tool in tools.items():
        registry.register(ToolManifest(name=name, description=name, args_schema="{}"), tool)
    return registry


@pytest.mark.asyncio
async def test_plan_topo_order_respects_needs() -> None:
    from app.harness.plan_graph import PlanExecutor, PlanGraph, PlanNode
    from app.harness.policy import HarnessPolicy
    from app.harness.runtime import AgentHarness
    from app.harness.tool_registry import ToolResult

    order: list[str] = []

    class Tool:
        def __init__(self, name: str) -> None:
            self.name = name

        async def invoke(self, args, ctx):  # noqa: ANN001
            order.append(self.name)
            return ToolResult(ok=True, output={"rows": [self.name]}, observation_text=self.name)

    plan = PlanGraph(
        nodes=[
            PlanNode(id="n1", tool="a", needs=[], input_spec={}, output_expect="rows"),
            PlanNode(id="n2", tool="b", needs=["n1"], input_spec={}, output_expect="rows"),
        ]
    )
    executor = PlanExecutor(
        tool_registry=_registry({"a": Tool("a"), "b": Tool("b")}),
        policy=HarnessPolicy(),
        harness=AgentHarness(enabled=False),
    )

    results = await executor.execute(plan, _ctx())

    assert [result.node_id for result in results] == ["n1", "n2"]
    assert order == ["a", "b"]


@pytest.mark.asyncio
async def test_output_expect_fail_marks_node() -> None:
    from app.harness.plan_graph import PlanExecutor, PlanGraph, PlanNode
    from app.harness.policy import HarnessPolicy
    from app.harness.runtime import AgentHarness
    from app.harness.tool_registry import ToolResult

    class Tool:
        async def invoke(self, args, ctx):  # noqa: ANN001
            return ToolResult(ok=True, output={"value": 1}, observation_text="no rows")

    plan = PlanGraph(nodes=[PlanNode(id="n1", tool="a", needs=[], input_spec={}, output_expect="rows")])
    executor = PlanExecutor(
        tool_registry=_registry({"a": Tool()}),
        policy=HarnessPolicy(),
        harness=AgentHarness(enabled=False),
    )

    results = await executor.execute(plan, _ctx())

    assert results[0].ok is True
    assert results[0].output_meets_expect is False
    assert executor.needs_replan(results) is True


@pytest.mark.asyncio
async def test_replan_on_validator_fail() -> None:
    from app.harness.plan_graph import PlanExecutor, PlanGraph, PlanNode
    from app.harness.policy import HarnessPolicy
    from app.harness.runtime import AgentHarness
    from app.harness.tool_registry import ToolResult

    class Tool:
        async def invoke(self, args, ctx):  # noqa: ANN001
            if args.get("version") == 2:
                return ToolResult(ok=True, output={"rows": [1]}, observation_text="fixed")
            return ToolResult(ok=False, output={}, observation_text="fail")

    initial = PlanGraph(nodes=[PlanNode(id="n1", tool="a", needs=[], input_spec={}, output_expect="rows")])
    executor = PlanExecutor(
        tool_registry=_registry({"a": Tool()}),
        policy=HarnessPolicy(),
        harness=AgentHarness(enabled=False),
    )

    async def replan(plan, results, count):  # noqa: ANN001
        assert count == 1
        return PlanGraph(
            nodes=[PlanNode(id="n1", tool="a", needs=[], input_spec={"version": 2}, output_expect="rows")]
        )

    final_results, replan_count = await executor.execute_with_replan(
        initial,
        _ctx(),
        replan=replan,
        max_replans=2,
    )

    assert replan_count == 1
    assert final_results[0].output_meets_expect is True


@pytest.mark.asyncio
async def test_replan_cap_degrades() -> None:
    from app.harness.plan_graph import PlanExecutor, PlanGraph, PlanNode
    from app.harness.policy import HarnessPolicy
    from app.harness.runtime import AgentHarness
    from app.harness.tool_registry import ToolResult

    class Tool:
        async def invoke(self, args, ctx):  # noqa: ANN001
            return ToolResult(ok=False, output={}, observation_text="still fail")

    plan = PlanGraph(nodes=[PlanNode(id="n1", tool="a", needs=[], input_spec={}, output_expect="rows")])
    executor = PlanExecutor(
        tool_registry=_registry({"a": Tool()}),
        policy=HarnessPolicy(),
        harness=AgentHarness(enabled=False),
    )

    async def replan(plan, results, count):  # noqa: ANN001
        return plan

    results, replan_count = await executor.execute_with_replan(plan, _ctx(), replan=replan, max_replans=1)

    assert replan_count == 1
    assert executor.needs_replan(results) is True
