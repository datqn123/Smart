"""Slice D — plan template store (SRS-006 FR-11, QA TC-D-001/002/003/006)."""

from __future__ import annotations

from app.harness.plan_graph import PlanGraph, PlanNode
from app.harness.plan_template_store import (
    PLANNER_GENERATED,
    InMemoryPlanTemplateStore,
    PlanTemplateRecord,
    SqlitePlanTemplateStore,
    build_intent_key,
    normalize_intent_key,
    plan_graph_hash,
)


# --- build_intent_key (LOW-4 semantic key) --------------------------------

def test_intent_key_stable_across_phrasing_when_intent_fields_match():
    a = build_intent_key(intent_type="data_query", goal="doanh thu tháng này", required_data=["revenue"])
    b = build_intent_key(intent_type="data_query", goal="Doanh thu   tháng này", required_data=["revenue"])
    assert a == b  # case + whitespace normalized


def test_intent_key_distinguishes_time_window():
    this_month = build_intent_key(intent_type="data_query", goal="doanh thu tháng này", required_data=["revenue"])
    last_month = build_intent_key(intent_type="data_query", goal="doanh thu tháng trước", required_data=["revenue"])
    assert this_month != last_month  # must NOT collapse different windows


def test_intent_key_distinguishes_required_data_and_entities():
    base = build_intent_key(intent_type="data_query", goal="tồn kho", required_data=["stock"])
    other_metric = build_intent_key(intent_type="data_query", goal="tồn kho", required_data=["revenue"])
    with_entity = build_intent_key(
        intent_type="data_query", goal="tồn kho", required_data=["stock"], entities=["Sản phẩm A"]
    )
    assert base != other_metric
    assert base != with_entity


def test_intent_key_falls_back_to_raw_question_without_intent_fields():
    assert build_intent_key(fallback="Doanh thu  tháng này") == normalize_intent_key("Doanh thu  tháng này")


def _plan() -> PlanGraph:
    return PlanGraph(nodes=[PlanNode(id="n1", tool="sql_query", needs=[], input_spec={}, output_expect="rows")])


def _record(**overrides) -> PlanTemplateRecord:
    plan = overrides.pop("plan_graph", _plan())
    base = dict(
        normalized_intent_key=normalize_intent_key("doanh thu tháng này"),
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


# --- TC-D-001: promotion requires planner provenance ----------------------

def test_promotion_requires_planner_provenance():
    store = InMemoryPlanTemplateStore()
    hand_authored = _record(source="hand_authored")
    assert store.promote(hand_authored) is False
    assert (
        store.get(
            "doanh thu tháng này",
            role_scope="owner",
            manifest_version="mv1",
            policy_version="pv1",
            asset_versions={"K12": "1.0"},
        )
        is None
    )


def test_planner_generated_template_promoted_and_retrievable():
    store = InMemoryPlanTemplateStore()
    assert store.promote(_record()) is True
    got = store.get(
        "doanh thu tháng này",
        role_scope="owner",
        manifest_version="mv1",
        policy_version="pv1",
        asset_versions={"K12": "1.0"},
    )
    assert got is not None
    assert got.plan_graph.nodes[0].tool == "sql_query"


# --- TC-D-002: template pins versions -------------------------------------

def test_template_pins_versions():
    store = InMemoryPlanTemplateStore()
    store.promote(_record())
    got = store.get(
        "doanh thu tháng này",
        role_scope="owner",
        manifest_version="mv1",
        policy_version="pv1",
        asset_versions={"K12": "1.0"},
    )
    assert got.manifest_version == "mv1"
    assert got.policy_version == "pv1"
    assert got.asset_versions == {"K12": "1.0"}


def test_plan_graph_hash_includes_input_spec():
    a = PlanGraph(
        nodes=[PlanNode(id="n1", tool="sql_query", needs=[], input_spec={"query": "a"}, output_expect="rows")]
    )
    b = PlanGraph(
        nodes=[PlanNode(id="n1", tool="sql_query", needs=[], input_spec={"query": "b"}, output_expect="rows")]
    )

    assert plan_graph_hash(a) != plan_graph_hash(b)


# --- TC-D-003: version mismatch invalidates -------------------------------

def test_manifest_version_mismatch_invalidates():
    store = InMemoryPlanTemplateStore()
    store.promote(_record())
    got = store.get(
        "doanh thu tháng này",
        role_scope="owner",
        manifest_version="mv2",  # drifted
        policy_version="pv1",
        asset_versions={"K12": "1.0"},
    )
    assert got is None


def test_policy_and_asset_version_mismatch_invalidates():
    store = InMemoryPlanTemplateStore()
    store.promote(_record())
    assert (
        store.get(
            "doanh thu tháng này",
            role_scope="owner",
            manifest_version="mv1",
            policy_version="pv2",
            asset_versions={"K12": "1.0"},
        )
        is None
    )
    assert (
        store.get(
            "doanh thu tháng này",
            role_scope="owner",
            manifest_version="mv1",
            policy_version="pv1",
            asset_versions={"K12": "2.0"},
        )
        is None
    )


def test_role_scope_isolation():
    store = InMemoryPlanTemplateStore()
    store.promote(_record(role_scope="owner"))
    assert (
        store.get(
            "doanh thu tháng này",
            role_scope="staff",
            manifest_version="mv1",
            policy_version="pv1",
            asset_versions={"K12": "1.0"},
        )
        is None
    )


# --- TC-D-006: degraded outcome demotes -----------------------------------

def test_degraded_outcome_demotes_template():
    store = InMemoryPlanTemplateStore()
    store.promote(_record())
    store.record_outcome("doanh thu tháng này", role_scope="owner", status="degraded")
    got = store.get(
        "doanh thu tháng này",
        role_scope="owner",
        manifest_version="mv1",
        policy_version="pv1",
        asset_versions={"K12": "1.0"},
    )
    assert got is None  # demoted, no longer preferred


def test_success_outcome_keeps_template():
    store = InMemoryPlanTemplateStore()
    store.promote(_record())
    store.record_outcome("doanh thu tháng này", role_scope="owner", status="success")
    got = store.get(
        "doanh thu tháng này",
        role_scope="owner",
        manifest_version="mv1",
        policy_version="pv1",
        asset_versions={"K12": "1.0"},
    )
    assert got is not None
    assert got.success_count == 1


# --- runtime promotion (FR-11.3/11.7) -------------------------------------

def _get(store):
    return store.get(
        "doanh thu tháng này",
        role_scope="owner",
        manifest_version="mv1",
        policy_version="pv1",
        asset_versions={"K12": "1.0"},
    )


def test_consider_promotion_promotes_after_threshold():
    store = InMemoryPlanTemplateStore()
    assert store.consider_promotion(_record(), promote_after=3) is False
    assert _get(store) is None  # not active after 1 success
    assert store.consider_promotion(_record(), promote_after=3) is False
    assert _get(store) is None  # not active after 2
    assert store.consider_promotion(_record(), promote_after=3) is True
    active = _get(store)
    assert active is not None
    assert active.plan_graph.nodes[0].tool == "sql_query"


def test_consider_promotion_rejects_non_planner_provenance():
    store = InMemoryPlanTemplateStore()
    assert store.consider_promotion(_record(source="hand_authored"), promote_after=1) is False
    assert _get(store) is None


def test_non_success_resets_promotion_streak():
    store = InMemoryPlanTemplateStore()
    store.consider_promotion(_record(), promote_after=2)  # streak = 1
    store.note_non_success("doanh thu tháng này", role_scope="owner")
    assert store.consider_promotion(_record(), promote_after=2) is False  # back to 1
    assert _get(store) is None


def test_version_change_restarts_streak():
    store = InMemoryPlanTemplateStore()
    store.consider_promotion(_record(), promote_after=2)  # mv1 streak = 1
    # a manifest change => different pinned version => fresh candidate, not promoted
    assert store.consider_promotion(_record(manifest_version="mv2"), promote_after=2) is False
    assert _get(store) is None


def test_sqlite_consider_promotion_survives_reload(tmp_path):
    db = str(tmp_path / "promo.db")
    store = SqlitePlanTemplateStore(path=db)
    try:
        assert store.consider_promotion(_record(), promote_after=2) is False
    finally:
        store.close()
    # reopen — candidate streak persisted; second success promotes
    store2 = SqlitePlanTemplateStore(path=db)
    try:
        assert store2.consider_promotion(_record(), promote_after=2) is True
        assert _get(store2) is not None
    finally:
        store2.close()


# --- SQLite roundtrip ------------------------------------------------------

def test_sqlite_store_roundtrip_and_invalidation(tmp_path):
    store = SqlitePlanTemplateStore(path=str(tmp_path / "tpl.db"))
    try:
        assert store.promote(_record()) is True
        got = store.get(
            "doanh thu tháng này",
            role_scope="owner",
            manifest_version="mv1",
            policy_version="pv1",
            asset_versions={"K12": "1.0"},
        )
        assert got is not None
        assert got.plan_graph.nodes[0].tool == "sql_query"
        # version drift invalidates
        assert (
            store.get(
                "doanh thu tháng này",
                role_scope="owner",
                manifest_version="DRIFT",
                policy_version="pv1",
                asset_versions={"K12": "1.0"},
            )
            is None
        )
        # degraded demotes across reload
        store.record_outcome("doanh thu tháng này", role_scope="owner", status="degraded")
        assert (
            store.get(
                "doanh thu tháng này",
                role_scope="owner",
                manifest_version="mv1",
                policy_version="pv1",
                asset_versions={"K12": "1.0"},
            )
            is None
        )
    finally:
        store.close()
