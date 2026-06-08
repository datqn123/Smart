"""Runtime promotion of plan templates (SRS-006 FR-11.3/11.7, OQ-6).

A planner-generated plan that succeeds cleanly enough times for an intent is
auto-promoted to a fast-path template; the next turn runs it without a planner
PlanGraph LLM call, while still passing the Harness policy gate.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from langchain_core.messages import HumanMessage

from app.harness.plan_template_store import InMemoryPlanTemplateStore
from app.harness.policy import HarnessPolicy
from app.harness.runtime import AgentHarness
from app.harness.scratchpad import TurnScratchpad
from app.harness.tool_registry import ToolManifest, ToolRegistry, ToolResult, TurnContext


def _settings(**overrides):
    base = dict(
        harness_max_steps=4,
        harness_planner_role="harness_planner",
        harness_token_budget=0,
        harness_cost_budget_usd=0.0,
        harness_wallclock_timeout_s=0.0,
        agentic_trace_enabled=False,
        agentic_intent_object_enabled=True,
        agentic_plan_dag_enabled=True,
        agentic_v3_enabled=True,
        agentic_v3_plan_template_enabled=True,
        agentic_v3_template_promote_after=2,
        agentic_v3_route_accuracy_threshold=0.8,
        agentic_v3_measured_route_accuracy=0.95,  # eval cleared (FR-11.7)
        working_memory_pairs=0,
        plan_replan_max=1,
        agentic_model_routing_enabled=False,
        agentic_semantic_cache_enabled=False,
        agentic_answer_composer_enabled=False,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def _ctx():
    return TurnContext(
        tenant_id="t1", user_id="u1", thread_id="th1", correlation_id="cid",
        bearer_token=None, schema_version=None, role="owner", permissions=("data_read",),
    )


class _Client:
    def __init__(self) -> None:
        self.plan_calls = 0
        self.intent_calls = 0

    async def astructured_predict(self, messages, schema, **kwargs):  # noqa: ANN001
        name = schema.__name__
        if name == "IntentAnalysisResult":
            self.intent_calls += 1
            return schema(
                goal="doanh thu tháng này", intent_type="data_query",
                required_data=["revenue"], confidence=0.95,
            )
        if name == "PlanGraphOutput":
            self.plan_calls += 1
            return schema(nodes=[{
                "id": "q1", "tool": "sql_query", "needs": [],
                "input_spec": {"query": "doanh thu"}, "output_expect": "rows",
            }])
        raise AssertionError(name)


class _Registry:
    def __init__(self, client):
        self.client = client

    def get(self, role):  # noqa: ANN001
        return self.client


class _SqlTool:
    def __init__(self) -> None:
        self.calls = 0

    async def invoke(self, args, ctx):  # noqa: ANN001
        self.calls += 1
        return ToolResult(ok=True, output={"rows": [{"revenue": 100}]}, observation_text="rows")


@pytest.mark.asyncio
async def test_plan_promoted_after_threshold_then_served_without_planner():
    from app.harness.orchestrator import FinalAnswerEvent, HarnessOrchestrator

    registry = ToolRegistry()
    sql_tool = _SqlTool()
    registry.register(
        ToolManifest(
            name="sql_query", description="SQL", args_schema="{}",
            capability="data_read", produces=("rows",), result_ref_policy="result_ref",
        ),
        sql_tool,
    )
    client = _Client()
    orchestrator = HarnessOrchestrator(
        llm_registry=_Registry(client),
        tool_registry=registry,
        policy=HarnessPolicy(),
        settings=_settings(),
        harness=AgentHarness(enabled=False),
        plan_template_store=InMemoryPlanTemplateStore(),
    )

    async def _run_turn():
        return [
            e async for e in orchestrator.run(
                TurnScratchpad(messages=[HumanMessage(content="doanh thu tháng này")]), _ctx()
            )
        ]

    # promote_after=2: turns 1 & 2 use the planner; turn 3 hits the promoted template.
    await _run_turn()
    await _run_turn()
    events3 = await _run_turn()

    assert client.plan_calls == 2  # planner NOT called on the 3rd (template) turn
    assert client.intent_calls == 3  # intent still analyzed every turn
    assert sql_tool.calls == 3  # the plan ran each turn
    assert any(isinstance(e, FinalAnswerEvent) for e in events3)


def test_role_scope_separates_by_live_permissions():
    """P2-2: same role + different live permissions => different template scope."""
    from app.harness.orchestrator import _role_scope

    owner_full = TurnContext(
        tenant_id="t1", user_id="u1", thread_id="th1", correlation_id="c", bearer_token=None,
        schema_version=None, role="owner", permissions=("data_read", "draft_create"),
    )
    owner_read = TurnContext(
        tenant_id="t1", user_id="u2", thread_id="th2", correlation_id="c", bearer_token=None,
        schema_version=None, role="owner", permissions=("data_read",),
    )
    assert _role_scope(owner_full) != _role_scope(owner_read)
    # deterministic + permission-order independent
    owner_read_b = TurnContext(
        tenant_id="t1", user_id="u2", thread_id="th2", correlation_id="c", bearer_token=None,
        schema_version=None, role="owner", permissions=("data_read",),
    )
    assert _role_scope(owner_read) == _role_scope(owner_read_b)


@pytest.mark.asyncio
async def test_planner_failure_records_degraded_not_success():
    """P1-3: a caught plan-mode error is K15 'degraded' and labeled, not clean success."""
    from app.harness.history_store import InMemoryIntentHistoryStore
    from app.harness.orchestrator import FinalAnswerEvent, HarnessOrchestrator
    from app.harness.plan_template_store import build_intent_key

    registry = ToolRegistry()
    registry.register(
        ToolManifest(name="sql_query", description="SQL", args_schema="{}", capability="data_read"),
        _SqlTool(),
    )

    class _BadClient:
        async def astructured_predict(self, messages, schema, **kwargs):  # noqa: ANN001
            if schema.__name__ == "IntentAnalysisResult":
                return schema(
                    goal="doanh thu tháng này", intent_type="data_query",
                    required_data=["revenue"], confidence=0.95,
                )
            if schema.__name__ == "PlanGraphOutput":
                raise RuntimeError("planner boom")
            raise AssertionError(schema.__name__)

    history = InMemoryIntentHistoryStore()
    orchestrator = HarnessOrchestrator(
        llm_registry=_Registry(_BadClient()),
        tool_registry=registry,
        policy=HarnessPolicy(),
        settings=_settings(agentic_v3_plan_template_enabled=False),
        harness=AgentHarness(enabled=False),
        history_store=history,
    )

    events = [
        e async for e in orchestrator.run(
            TurnScratchpad(messages=[HumanMessage(content="doanh thu tháng này")]), _ctx()
        )
    ]

    finals = [e for e in events if isinstance(e, FinalAnswerEvent)]
    assert finals and "chưa đầy đủ" in finals[0].text  # FR-1.6 labeled
    summary = history.summary(
        build_intent_key(intent_type="data_query", goal="doanh thu tháng này", required_data=["revenue"])
    )
    assert summary.degraded == 1
    assert summary.success == 0  # FR-9.5: not a clean success


@pytest.mark.asyncio
async def test_no_promotion_until_k12_eval_cleared():
    """FR-11.7: clean successes must NOT promote while K12 accuracy is below threshold."""
    from app.harness.orchestrator import HarnessOrchestrator

    registry = ToolRegistry()
    sql_tool = _SqlTool()
    registry.register(
        ToolManifest(
            name="sql_query", description="SQL", args_schema="{}",
            capability="data_read", produces=("rows",), result_ref_policy="result_ref",
        ),
        sql_tool,
    )
    client = _Client()
    store = InMemoryPlanTemplateStore()
    orchestrator = HarnessOrchestrator(
        llm_registry=_Registry(client),
        tool_registry=registry,
        policy=HarnessPolicy(),
        settings=_settings(agentic_v3_measured_route_accuracy=0.0),  # eval NOT cleared
        harness=AgentHarness(enabled=False),
        plan_template_store=store,
    )

    for _ in range(4):
        _ = [
            e async for e in orchestrator.run(
                TurnScratchpad(messages=[HumanMessage(content="doanh thu tháng này")]), _ctx()
            )
        ]

    # planner ran every turn (no template promoted)
    assert client.plan_calls == 4


@pytest.mark.asyncio
async def test_degraded_run_does_not_promote():
    from app.harness.orchestrator import HarnessOrchestrator

    registry = ToolRegistry()

    class FailingSql:
        async def invoke(self, args, ctx):  # noqa: ANN001
            return ToolResult(ok=False, output={}, observation_text="", error_message="boom")

    registry.register(
        ToolManifest(name="sql_query", description="SQL", args_schema="{}", capability="data_read"),
        FailingSql(),
    )
    client = _Client()
    store = InMemoryPlanTemplateStore()
    orchestrator = HarnessOrchestrator(
        llm_registry=_Registry(client),
        tool_registry=registry,
        policy=HarnessPolicy(),
        settings=_settings(),
        harness=AgentHarness(enabled=False),
        plan_template_store=store,
    )

    for _ in range(4):
        _ = [
            e async for e in orchestrator.run(
                TurnScratchpad(messages=[HumanMessage(content="doanh thu tháng này")]), _ctx()
            )
        ]

    # never promoted because runs degraded/failed
    got = store.get(
        "data_query|doanh thu tháng này|revenue",
        role_scope="owner",
        manifest_version=registry.manifest_version,
        policy_version=__import__("app.harness.policy", fromlist=["POLICY_VERSION"]).POLICY_VERSION,
        asset_versions={"K12": "1.0", "K15": "1.0"},
    )
    assert got is None
