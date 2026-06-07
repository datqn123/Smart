"""Slice G — K15 intent history (SRS-006 FR-9, QA TC-G-001..004)."""

from __future__ import annotations

from app.harness.history_store import (
    STATUS_CLARIFY_PENDING,
    STATUS_DEGRADED,
    STATUS_HITL_PENDING,
    STATUS_SUCCESS,
    InMemoryIntentHistoryStore,
    SqliteIntentHistoryStore,
    build_history_event,
)


# --- TC-G-001: clean success appended -------------------------------------

def test_clean_success_event_appended():
    store = InMemoryIntentHistoryStore()
    event = build_history_event(
        tenant_id="t1",
        intent_key="doanh thu tháng này",
        plan_hash="ph1",
        tools=["sql_query", "answer_composer"],
        status=STATUS_SUCCESS,
        cost_usd=0.01,
        asset_versions={"K12": "1.0"},
    )
    store.append(event)
    summary = store.summary("doanh thu tháng này")
    assert summary.total == 1
    assert summary.success == 1
    assert event.plan["plan_hash"] == "ph1"
    assert event.plan["tools"] == ["sql_query", "answer_composer"]
    assert event.asset_versions == {"K12": "1.0"}


# --- TC-G-002: degraded distinct from success -----------------------------

def test_degraded_distinct_from_success():
    store = InMemoryIntentHistoryStore()
    store.append(build_history_event(
        tenant_id="t1", intent_key="x", plan_hash="p", tools=[], status=STATUS_DEGRADED,
    ))
    summary = store.summary("x")
    assert summary.degraded == 1
    assert summary.success == 0
    assert summary.clean_success_rate == 0.0


# --- TC-G-003: hitl / clarify pending distinct statuses -------------------

def test_hitl_and_clarify_pending_distinct():
    store = InMemoryIntentHistoryStore()
    store.append(build_history_event(
        tenant_id="t1", intent_key="x", plan_hash="p", tools=[], status=STATUS_HITL_PENDING,
    ))
    store.append(build_history_event(
        tenant_id="t1", intent_key="x", plan_hash="p", tools=[], status=STATUS_CLARIFY_PENDING,
    ))
    summary = store.summary("x")
    assert summary.hitl_pending == 1
    assert summary.clarify_pending == 1
    assert summary.success == 0


# --- TC-G-004: privacy — no raw tenant/user/question/SQL/PII --------------

def test_event_stores_no_raw_pii_or_sql():
    event = build_history_event(
        tenant_id="tenant-secret-42",
        intent_key="khách 0901234567 email a@b.com SELECT * FROM users",
        plan_hash="ph",
        tools=["sql_query"],
        status=STATUS_SUCCESS,
    )
    blob = event.model_dump_json()
    assert "tenant-secret-42" not in blob
    assert "0901234567" not in blob
    assert "a@b.com" not in blob
    assert "SELECT" not in blob.upper()
    # but a tenant hash IS present
    assert event.context["tenant_hash"]
    assert "tenant_hash" in blob


def test_summary_down_weights_degraded_vs_success():
    store = InMemoryIntentHistoryStore()
    for _ in range(3):
        store.append(build_history_event(
            tenant_id="t", intent_key="k", plan_hash="p", tools=[], status=STATUS_SUCCESS,
        ))
    store.append(build_history_event(
        tenant_id="t", intent_key="k", plan_hash="p", tools=[], status=STATUS_DEGRADED,
    ))
    s = store.summary("k")
    assert s.total == 4
    assert s.success == 3
    assert s.degraded == 1
    assert 0.0 < s.clean_success_rate < 1.0


def test_sqlite_history_roundtrip(tmp_path):
    store = SqliteIntentHistoryStore(path=str(tmp_path / "k15.db"))
    try:
        store.append(build_history_event(
            tenant_id="t1", intent_key="k", plan_hash="p", tools=["sql_query"], status=STATUS_SUCCESS,
        ))
        store.append(build_history_event(
            tenant_id="t1", intent_key="k", plan_hash="p", tools=["sql_query"], status=STATUS_DEGRADED,
        ))
        s = store.summary("k")
        assert s.total == 2
        assert s.success == 1
        assert s.degraded == 1
    finally:
        store.close()
