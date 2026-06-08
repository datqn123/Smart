"""Runtime wiring for SRS-006 plan-template execution tier."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from langchain_core.messages import HumanMessage

from app.harness.plan_graph import PlanGraph, PlanNode
from app.harness.plan_template_store import (
    PLANNER_GENERATED,
    InMemoryPlanTemplateStore,
    PlanTemplateRecord,
    build_intent_key,
    normalize_intent_key,
    plan_graph_hash,
)

# Semantic intent key the orchestrator derives for the seeded IntentObject
# (intent_type="data_query", goal="doanh thu tháng này", required_data=["revenue"]).
_DEMO_INTENT_KEY = build_intent_key(
    intent_type="data_query", goal="doanh thu tháng này", required_data=["revenue"]
)
from app.harness.policy import HarnessPolicy, POLICY_VERSION
from app.harness.runtime import AgentHarness
from app.harness.scratchpad import TurnScratchpad
from app.harness.tool_registry import ToolManifest, ToolRegistry, ToolResult, TurnContext


def _settings(**overrides):
    base = dict(
        harness_max_steps=4,
        harness_planner_role="harness_planner",
        harness_token_budget=0,
        harness_cost_budget_usd=0.05,
        harness_wallclock_timeout_s=30.0,
        agentic_trace_enabled=True,
        agentic_intent_object_enabled=True,
        working_memory_pairs=0,
        agentic_plan_dag_enabled=True,
        agentic_v3_enabled=True,
        agentic_v3_plan_template_enabled=True,
        agentic_answer_composer_enabled=False,
        plan_replan_max=1,
        agentic_model_routing_enabled=False,
        agentic_semantic_cache_enabled=False,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def _ctx() -> TurnContext:
    return TurnContext(
        tenant_id="t1",
        user_id="u1",
        thread_id="th1",
        correlation_id="cid",
        bearer_token=None,
        schema_version=None,
        role="owner",
        permissions=("data_read",),
    )


class _Client:
    def __init__(self) -> None:
        self.schemas: list[str] = []

    async def astructured_predict(self, messages, schema, **kwargs):  # noqa: ANN001
        self.schemas.append(schema.__name__)
        if schema.__name__ == "IntentAnalysisResult":
            return schema(goal="doanh thu tháng này", intent_type="data_query", required_data=["revenue"], confidence=0.95)
        if schema.__name__ == "PlanGraphOutput":
            raise AssertionError("template hit must not call planner PlanGraphOutput")
        if schema.__name__ == "DecisionSchema":
            return schema(action="final_answer", final_answer="fallback")
        raise AssertionError(schema.__name__)


class _LlmRegistry:
    def __init__(self, client: _Client) -> None:
        self.client = client

    def get(self, role: str):  # noqa: ANN001
        return self.client


class _SqlTool:
    def __init__(self) -> None:
        self.calls = 0

    async def invoke(self, args, ctx):  # noqa: ANN001
        self.calls += 1
        return ToolResult(ok=True, output={"rows": [{"revenue": 100}]}, observation_text="rows")


@pytest.mark.asyncio
async def test_v3_template_fast_path_executes_without_planner_plan_call() -> None:
    from app.harness.orchestrator import FinalAnswerEvent, HarnessOrchestrator

    registry = ToolRegistry()
    sql_tool = _SqlTool()
    registry.register(
        ToolManifest(
            name="sql_query",
            description="SQL",
            args_schema="{}",
            capability="data_read",
            produces=("rows",),
            result_ref_policy="result_ref",
        ),
        sql_tool,
    )
    plan = PlanGraph(
        nodes=[PlanNode(id="q1", tool="sql_query", input_spec={"query": "doanh thu"}, output_expect="rows")]
    )
    from app.harness.orchestrator import _role_scope

    store = InMemoryPlanTemplateStore()
    assert store.promote(
        PlanTemplateRecord(
            normalized_intent_key=_DEMO_INTENT_KEY,
            plan_graph_hash=plan_graph_hash(plan),
            plan_graph=plan,
            manifest_version=registry.manifest_version,
            policy_version=POLICY_VERSION,
            asset_versions={"K12": "1.0", "K15": "1.0"},
            role_scope=_role_scope(_ctx()),
            source=PLANNER_GENERATED,
        )
    )
    client = _Client()
    orchestrator = HarnessOrchestrator(
        llm_registry=_LlmRegistry(client),
        tool_registry=registry,
        policy=HarnessPolicy(),
        settings=_settings(),
        harness=AgentHarness(enabled=False),
        plan_template_store=store,
    )

    events = [
        e
        async for e in orchestrator.run(
            TurnScratchpad(messages=[HumanMessage(content="doanh thu tháng này")]),
            _ctx(),
        )
    ]

    assert sql_tool.calls == 1
    assert client.schemas == ["IntentAnalysisResult"]
    assert any(isinstance(e, FinalAnswerEvent) for e in events)


@pytest.mark.asyncio
async def test_v3_plan_mode_appends_k15_history_after_success() -> None:
    from app.harness.history_store import InMemoryIntentHistoryStore
    from app.harness.orchestrator import HarnessOrchestrator

    registry = ToolRegistry()
    sql_tool = _SqlTool()
    registry.register(
        ToolManifest(
            name="sql_query",
            description="SQL",
            args_schema="{}",
            capability="data_read",
            produces=("rows",),
            result_ref_policy="result_ref",
        ),
        sql_tool,
    )
    client = _Client()

    async def _predict(messages, schema, **kwargs):  # noqa: ANN001
        client.schemas.append(schema.__name__)
        if schema.__name__ == "IntentAnalysisResult":
            return schema(goal="doanh thu tháng này", intent_type="data_query", required_data=["revenue"], confidence=0.95)
        if schema.__name__ == "PlanGraphOutput":
            return schema(
                nodes=[
                    {
                        "id": "q1",
                        "tool": "sql_query",
                        "needs": [],
                        "input_spec": {"query": "doanh thu"},
                        "output_expect": "rows",
                    }
                ]
            )
        raise AssertionError(schema.__name__)

    client.astructured_predict = _predict
    history = InMemoryIntentHistoryStore()
    orchestrator = HarnessOrchestrator(
        llm_registry=_LlmRegistry(client),
        tool_registry=registry,
        policy=HarnessPolicy(),
        settings=_settings(agentic_v3_plan_template_enabled=False),
        harness=AgentHarness(enabled=False),
        history_store=history,
    )

    _ = [
        e
        async for e in orchestrator.run(
            TurnScratchpad(messages=[HumanMessage(content="doanh thu tháng này")]),
            _ctx(),
        )
    ]

    summary = history.summary(_DEMO_INTENT_KEY)
    assert summary.success == 1
