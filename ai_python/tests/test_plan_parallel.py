from __future__ import annotations

import asyncio

import pytest


@pytest.mark.asyncio
async def test_independent_nodes_run_concurrently() -> None:
    from app.harness.plan_graph import PlanExecutor, PlanGraph, PlanNode
    from app.harness.policy import HarnessPolicy
    from app.harness.runtime import AgentHarness
    from app.harness.tool_registry import ToolManifest, ToolRegistry, ToolResult, TurnContext

    peak = {"current": 0, "max": 0}

    class Tool:
        async def invoke(self, args, ctx):  # noqa: ANN001
            peak["current"] += 1
            peak["max"] = max(peak["max"], peak["current"])
            await asyncio.sleep(0.01)
            peak["current"] -= 1
            return ToolResult(ok=True, output={"rows": [args["id"]]}, observation_text=args["id"])

    registry = ToolRegistry()
    registry.register(ToolManifest(name="sql_query", description="SQL", args_schema="{}"), Tool())
    plan = PlanGraph(
        nodes=[
            PlanNode(id="n1", tool="sql_query", needs=[], input_spec={"id": "n1"}, output_expect="rows"),
            PlanNode(id="n2", tool="sql_query", needs=[], input_spec={"id": "n2"}, output_expect="rows"),
        ]
    )
    ctx = TurnContext(
        tenant_id="t1",
        user_id="u1",
        thread_id="thread-1",
        correlation_id="corr-1",
        bearer_token=None,
        schema_version=None,
    )

    results = await PlanExecutor(
        tool_registry=registry,
        policy=HarnessPolicy(),
        harness=AgentHarness(enabled=False),
    ).execute(plan, ctx)

    assert {result.node_id for result in results} == {"n1", "n2"}
    assert peak["max"] >= 2
