"""Smart retry policy tests."""

from __future__ import annotations

from app.graph.retry_policy import (
    RetryAction,
    chart_degrade_eligible,
    chart_thin_data_sql_ok,
    decide_chart_readiness_retry,
    decide_sql_retry,
    sql_attempt_duplicate,
    sql_fingerprint,
)


def test_sql_fingerprint_normalizes() -> None:
    a = "SELECT 1 LIMIT 10;"
    b = "SELECT   1\nLIMIT 10"
    assert sql_fingerprint(a) == sql_fingerprint(b)


def test_sql_attempt_duplicate_detects() -> None:
    sql = "SELECT COUNT(*) FROM salesorders LIMIT 10"
    state = {
        "sql_attempt_history": [sql, sql],
        "sql_attempt_count": 2,
    }
    assert sql_attempt_duplicate(state)


def test_chart_thin_data_blocks_retry() -> None:
    sql = (
        "SELECT DATE_TRUNC('month', created_at) AS month, COUNT(*) n "
        "FROM salesorders GROUP BY DATE_TRUNC('month', created_at)"
    )
    state = {
        "intent": "system_data_chart",
        "generated_sql": sql,
        "query_result": {"rows": [{"month": "2026-05-01", "n": 7}]},
    }
    assert chart_thin_data_sql_ok(state)
    d = decide_chart_readiness_retry({**state, "chart_data_ok": False})
    assert d.action == RetryAction.CHART_DEGRADE


def test_duplicate_sql_degrades_chart_on_shape_retry() -> None:
    sql = "SELECT 1"
    state = {
        "intent": "system_data_chart",
        "sql_attempt_count": 2,
        "sql_attempt_history": [sql, sql],
        "query_result": {"rows": [{"x": 1}]},
        "validation_feedback": {
            "policy": [],
            "result": ["chart readiness: x"],
            "exec": [],
            "intent_review": [],
        },
    }
    d = decide_chart_readiness_retry({**state, "chart_data_ok": False})
    assert d.action == RetryAction.CHART_DEGRADE
    assert chart_degrade_eligible(state)


def test_policy_budget_blocks_regen() -> None:
    state = {
        "intent": "system_data_query",
        "sql_attempt_count": 1,
        "validation_feedback": {
            "policy": ["e1", "e2", "e3"],
            "result": [],
            "exec": [],
            "intent_review": [],
        },
    }
    d = decide_sql_retry(state, kind="policy")
    assert d.action == RetryAction.FAIL


def test_intent_review_many_issues_still_regen_by_attempt_count() -> None:
    """Multiple issues in one review round must not exhaust retry before MAX_SQL_ATTEMPTS."""
    state = {
        "intent": "system_data_query",
        "sql_attempt_count": 2,
        "validation_feedback": {
            "policy": [],
            "result": [],
            "exec": [],
            "intent_review": ["a", "b", "c", "d", "e"],
        },
    }
    d = decide_sql_retry(state, kind="intent_review")
    assert d.action == RetryAction.REGEN_SQL


def test_intent_review_budget_exhausted_at_max_attempts() -> None:
    state = {
        "intent": "system_data_query",
        "sql_attempt_count": 3,
        "validation_feedback": {"policy": [], "result": [], "exec": [], "intent_review": ["x"]},
    }
    d = decide_sql_retry(state, kind="intent_review")
    assert d.action == RetryAction.FAIL
