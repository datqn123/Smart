import logging

import pytest

from app.harness.eval_gate import EvalCase, evaluate_case, route_accuracy, v3_rollout_allowed
from app.harness.history_store import InMemoryIntentHistoryStore, build_history_event
from app.harness.memory_store import InMemoryConversationMemoryStore, MemoryTurnRecord
from app.harness.plan_template_store import InMemoryPlanTemplateStore, PlanTemplateRecord


def test_template_store_init_logs(caplog):
    with caplog.at_level(logging.INFO):
        store = InMemoryPlanTemplateStore()
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
        result = evaluate_case(case, ["sql_query"])
    assert "eval_case" in caplog.text
    assert "passed=True" in caplog.text


def test_eval_accuracy_logs(caplog):
    case = EvalCase(case_id="c1", required_tools=("sql_query",))
    result = evaluate_case(case, ["sql_query"])
    with caplog.at_level(logging.INFO):
        accuracy = route_accuracy([result])
    assert "eval_accuracy" in caplog.text
    assert "accuracy=1.00" in caplog.text


def test_eval_rollout_logs(caplog):
    with caplog.at_level(logging.INFO):
        allowed = v3_rollout_allowed(0.9, 0.8)
    assert "eval_rollout" in caplog.text
    assert "allowed=True" in caplog.text
