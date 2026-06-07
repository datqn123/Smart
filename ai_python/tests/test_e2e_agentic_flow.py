from __future__ import annotations

from types import SimpleNamespace

import pytest


class _FinalClient:
    def __init__(self) -> None:
        from app.llm.openai_compatible import InvokeUsage

        self.last_usage = InvokeUsage(prompt_tokens=10, completion_tokens=5, cost_usd=0.001)

    async def astructured_predict(self, messages, schema, **kwargs):  # noqa: ANN001
        return schema(action="final_answer", final_answer="Đã xử lý yêu cầu.")


class _Registry:
    def __init__(self, client) -> None:  # noqa: ANN001
        self.client = client

    def get(self, role: str):  # noqa: ANN001
        return self.client


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


@pytest.mark.asyncio
async def test_p0_simple_loop_final_answer_has_usage_budget_accounting() -> None:
    from app.harness.orchestrator import FinalAnswerEvent, HarnessOrchestrator
    from app.harness.policy import HarnessPolicy
    from app.harness.runtime import AgentHarness
    from app.harness.scratchpad import TurnScratchpad
    from app.harness.tool_registry import ToolRegistry

    orchestrator = HarnessOrchestrator(
        llm_registry=_Registry(_FinalClient()),
        tool_registry=ToolRegistry(),
        policy=HarnessPolicy(),
        settings=SimpleNamespace(
            harness_max_steps=3,
            harness_planner_role="harness_planner",
            harness_token_budget=1000,
            harness_cost_budget_usd=0.05,
            harness_wallclock_timeout_s=30.0,
        ),
        harness=AgentHarness(enabled=False),
    )

    events = [event async for event in orchestrator.run(TurnScratchpad(messages=[]), _ctx())]

    finals = [event for event in events if isinstance(event, FinalAnswerEvent)]
    assert finals and finals[0].text == "Đã xử lý yêu cầu."
    assert orchestrator._budget.used_tokens == 15
    assert orchestrator._budget.used_cost_usd == 0.001


@pytest.mark.asyncio
async def test_p2_plan_executor_runs_parallel_sql_nodes() -> None:
    from app.harness.plan_graph import PlanExecutor, PlanGraph, PlanNode
    from app.harness.policy import HarnessPolicy
    from app.harness.runtime import AgentHarness
    from app.harness.tool_registry import ToolManifest, ToolRegistry, ToolResult

    calls: list[str] = []

    class SqlTool:
        async def invoke(self, args, ctx):  # noqa: ANN001
            calls.append(args["metric"])
            return ToolResult(ok=True, output={"rows": [{"metric": args["metric"]}]}, observation_text=args["metric"])

    registry = ToolRegistry()
    registry.register(ToolManifest(name="sql_query", description="SQL", args_schema="{}"), SqlTool())
    plan = PlanGraph(
        nodes=[
            PlanNode(id="revenue", tool="sql_query", needs=[], input_spec={"metric": "revenue"}, output_expect="rows"),
            PlanNode(id="inventory", tool="sql_query", needs=[], input_spec={"metric": "inventory"}, output_expect="rows"),
        ]
    )

    results = await PlanExecutor(
        tool_registry=registry,
        policy=HarnessPolicy(),
        harness=AgentHarness(enabled=False),
    ).execute(plan, _ctx())

    assert {result.node_id for result in results} == {"revenue", "inventory"}
    assert set(calls) == {"revenue", "inventory"}


@pytest.mark.asyncio
async def test_p4_chart_then_answer_composer_flow() -> None:
    from app.graph.tools.answer_composer import AnswerComposerTool
    from app.graph.tools.build_chart import BuildChartTool

    rows = [{"month": "2026-01", "revenue": 100}, {"month": "2026-02", "revenue": 120}]
    chart = await BuildChartTool().invoke({"rows": rows}, _ctx())
    answer = await AnswerComposerTool().invoke(
        {"observations": [{"rows": rows, "chart": chart.output}], "assumptions": []},
        _ctx(),
    )

    assert chart.sse_payload and chart.sse_payload["_event"] == "chart"
    assert answer.sse_payload and answer.sse_payload["_event"] == "delta_full"
    assert answer.output["follow_ups"]


def test_p6_staff_masked_vs_owner_full() -> None:
    from app.harness.capability import CapabilityMatrix

    rows = [{"product_name": "Áo", "cost_price": 100, "sale_price": 150}]
    matrix = CapabilityMatrix()

    assert "cost_price" not in matrix.mask_columns("staff", rows)[0]
    assert matrix.mask_columns("owner", rows)[0]["cost_price"] == 100


def test_p5_working_memory_second_turn_keeps_context() -> None:
    from app.harness.memory import WorkingMemory
    from langchain_core.messages import AIMessage, HumanMessage

    messages = [
        HumanMessage(content="Doanh thu tháng này"),
        AIMessage(content="100 triệu"),
        HumanMessage(content="So với tháng trước?"),
    ]

    kept = WorkingMemory(pairs=6).attach(messages)

    assert [msg.content for msg in kept] == ["Doanh thu tháng này", "100 triệu", "So với tháng trước?"]


def test_p7_cache_is_tenant_scoped() -> None:
    from app.harness.cache import InMemorySemanticCache

    cache = InMemorySemanticCache()
    cache.put("sql_query", {"query": "doanh thu"}, "tenant-a", {"rows": [1]})

    assert cache.get("sql_query", {"query": "doanh thu"}, "tenant-b") is None


def test_p8_trace_records_cost_latency() -> None:
    from app.harness.observability import TraceRecorder

    recorder = TraceRecorder(intent="chart_report")
    recorder.record_step(step=1, tool="build_chart", ok=True, tokens=20, cost_usd=0.002, latency_ms=5)

    metrics = recorder.finalize()

    assert metrics.intent == "chart_report"
    assert metrics.cost_usd == 0.002
