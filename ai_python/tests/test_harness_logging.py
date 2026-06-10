import logging

import pytest

from app.harness.eval_gate import EvalCase, evaluate_case, route_accuracy, v3_rollout_allowed
from app.harness.history_store import InMemoryIntentHistoryStore, build_history_event
from app.harness.memory_store import InMemoryConversationMemoryStore, MemoryTurnRecord
from app.harness.plan_graph import PlanGraph, PlanNode
from app.harness.plan_template_store import (
    PLANNER_GENERATED,
    InMemoryPlanTemplateStore,
    PlanTemplateRecord,
    plan_graph_hash,
)
from app.harness.observation import build_observation
from app.harness.tool_registry import ToolRegistry, ToolManifest
from app.harness.budget import TurnBudget, BudgetExceeded
from app.harness.cache import InMemorySemanticCache


def test_template_store_init_logs(caplog):
    with caplog.at_level(logging.INFO):
        InMemoryPlanTemplateStore()
    assert "template_store_init" in caplog.text
    assert "backend=memory" in caplog.text


def test_template_lookup_logs(caplog):
    store = InMemoryPlanTemplateStore()
    with caplog.at_level(logging.INFO):
        store.get("test_intent", role_scope="owner", manifest_version="mv1", policy_version="pv1", asset_versions={})
    assert "template_lookup" in caplog.text
    assert "found=False" in caplog.text


def test_k15_event_append_logs(caplog):
    store = InMemoryIntentHistoryStore()
    event = build_history_event(
        tenant_id="t1", intent_key="q1", plan_hash="h1",
        tools=["sql_query"], status="success", replan_count=0, hitl_count=0,
    )
    with caplog.at_level(logging.INFO):
        store.append(event)
    assert "k15_event_append" in caplog.text
    assert "status=success" in caplog.text


def test_k15_summary_logs(caplog):
    store = InMemoryIntentHistoryStore()
    event = build_history_event(
        tenant_id="t1", intent_key="q1", plan_hash="h1",
        tools=["sql_query"], status="success",
    )
    store.append(event)
    with caplog.at_level(logging.INFO):
        store.summary("q1")
    assert "k15_summary" in caplog.text
    assert "total=1" in caplog.text


def test_conv_memory_append_logs(caplog):
    store = InMemoryConversationMemoryStore()
    turn = MemoryTurnRecord(thread_id="t1", turn_index=1, user_message="hi", ai_answer="hello")
    with caplog.at_level(logging.INFO):
        store.append_turn("t1", turn)
    assert "conv_memory_append" in caplog.text
    assert "thread=t1" in caplog.text


def test_conv_memory_retrieve_logs(caplog):
    store = InMemoryConversationMemoryStore()
    turn = MemoryTurnRecord(thread_id="t1", turn_index=1, user_message="hi", ai_answer="hello")
    store.append_turn("t1", turn)
    with caplog.at_level(logging.INFO):
        store.get_context("t1")
    assert "conv_memory_retrieve" in caplog.text
    assert "turns=1" in caplog.text


def test_conv_memory_compact_logs(caplog):
    store = InMemoryConversationMemoryStore(max_turns=2)
    for i in range(5):
        store.append_turn("t1", MemoryTurnRecord(thread_id="t1", turn_index=i, user_message=f"m{i}", ai_answer=f"a{i}"))
    with caplog.at_level(logging.INFO):
        store.compact("t1", "summary text")
    assert "conv_memory_compact" in caplog.text
    assert "kept=2" in caplog.text


def test_conv_memory_delete_logs(caplog):
    store = InMemoryConversationMemoryStore()
    store.append_turn("t1", MemoryTurnRecord(thread_id="t1", turn_index=1, user_message="hi", ai_answer="hello"))
    with caplog.at_level(logging.INFO):
        store.delete_thread("t1")
    assert "conv_memory_delete" in caplog.text
    assert "turns_removed=1" in caplog.text


def test_eval_case_logs(caplog):
    case = EvalCase(case_id="c1", required_tools=("sql_query",))
    with caplog.at_level(logging.INFO):
        evaluate_case(case, ["sql_query"])
    assert "eval_case" in caplog.text
    assert "passed=True" in caplog.text


def test_eval_accuracy_logs(caplog):
    case = EvalCase(case_id="c1", required_tools=("sql_query",))
    result = evaluate_case(case, ["sql_query"])
    with caplog.at_level(logging.INFO):
        route_accuracy([result])
    assert "eval_accuracy" in caplog.text
    assert "accuracy=1.00" in caplog.text


def test_eval_rollout_logs(caplog):
    with caplog.at_level(logging.INFO):
        v3_rollout_allowed(0.9, 0.8)
    assert "eval_rollout" in caplog.text
    assert "allowed=True" in caplog.text


def _make_plan() -> PlanGraph:
    return PlanGraph(nodes=[PlanNode(id="n1", tool="sql_query", needs=[], input_spec={}, output_expect="rows")])


def _make_record(**overrides) -> PlanTemplateRecord:
    plan = overrides.pop("plan_graph", _make_plan())
    base = dict(
        normalized_intent_key="test intent",
        plan_graph_hash=plan_graph_hash(plan),
        plan_graph=plan,
        manifest_version="mv1",
        policy_version="pv1",
        asset_versions={"K12": "1.0"},
        role_scope="owner",
        source=PLANNER_GENERATED,
    )
    base.update(overrides)
    return PlanTemplateRecord(**base)


def test_template_promoted_logs(caplog):
    store = InMemoryPlanTemplateStore()
    record = _make_record()
    with caplog.at_level(logging.INFO):
        store.promote(record)
    assert "template_promoted" in caplog.text
    assert "intent=test intent" in caplog.text
    assert "role=owner" in caplog.text


def test_template_promotion_blocked_logs(caplog):
    store = InMemoryPlanTemplateStore()
    record = _make_record()
    with caplog.at_level(logging.INFO):
        store.consider_promotion(record, promote_after=3)
    assert "template_promotion_blocked" in caplog.text
    assert "accuracy=0.33" in caplog.text
    assert "below_threshold=1.00" in caplog.text


def test_template_candidate_streak_logs(caplog):
    store = InMemoryPlanTemplateStore()
    record = _make_record()
    with caplog.at_level(logging.INFO):
        store.consider_promotion(record, promote_after=3)
    assert "template_candidate_streak" in caplog.text
    assert "success_count=1/3" in caplog.text


def test_template_streak_broken_logs(caplog):
    store = InMemoryPlanTemplateStore()
    record = _make_record()
    store.promote(record)
    with caplog.at_level(logging.WARNING):
        store.record_outcome("test intent", role_scope="owner", status="failure")
    assert "template_streak_broken" in caplog.text
    assert "status=failure" in caplog.text


def test_template_demoted_logs(caplog):
    store = InMemoryPlanTemplateStore()
    record = _make_record()
    store.promote(record)
    with caplog.at_level(logging.WARNING):
        store.record_outcome("test intent", role_scope="owner", status="degraded")
    assert "template_demoted" in caplog.text
    assert "status=degraded" in caplog.text


class MockToolResult:
    def __init__(self, ok=True, output=None, error_message=""):
        self.ok = ok
        self.output = output or {}
        self.error_message = error_message


def test_observation_built_logs(caplog):
    result = MockToolResult(ok=True, output={"rows": [{"id": 1}]})
    with caplog.at_level(logging.INFO):
        build_observation(tool_name="test", tool_result=result, ctx=None)
    assert "observation_built" in caplog.text
    assert "tool=test" in caplog.text


def test_observation_error_logs(caplog):
    result = MockToolResult(ok=False, error_message="permission denied")
    with caplog.at_level(logging.WARNING):
        build_observation(tool_name="test", tool_result=result, ctx=None)
    assert "observation_error" in caplog.text
    assert "kind=policy_blocked" in caplog.text


def test_tool_registered_logs(caplog):
    registry = ToolRegistry()
    manifest = ToolManifest(name="test_tool", description="test", args_schema="{}")
    with caplog.at_level(logging.INFO):
        registry.register(manifest, None)
    assert "tool_registered" in caplog.text
    assert "name=test_tool" in caplog.text


def test_budget_exceeded_logs(caplog):
    budget = TurnBudget(max_steps=10, token_budget=100)
    budget.start()
    budget.add_usage(tokens=150, cost_usd=0.0)
    with caplog.at_level(logging.WARNING):
        with pytest.raises(BudgetExceeded):
            budget.check(step=1)
    assert "budget_exceeded" in caplog.text
    assert "kind=token" in caplog.text


def test_cache_hit_logs(caplog):
    cache = InMemorySemanticCache()
    cache.put("sql_query", {"q": "test"}, "t1", {"rows": []})
    with caplog.at_level(logging.INFO):
        cache.get("sql_query", {"q": "test"}, "t1")
    assert "harness_cache" in caplog.text
    assert "hit=True" in caplog.text
