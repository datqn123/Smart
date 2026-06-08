"""AGENTIC_V3_ENABLED is the single legacy->v3 switch (SRS-006 NFR-7, rollout)."""

from __future__ import annotations

from app.config.graph_settings import GraphSettings


def test_v3_off_does_not_force_dependent_flags_on():
    # With the master switch off, cascade must not turn anything on (legacy/rollback).
    s = GraphSettings(
        agentic_v3_enabled=False,
        harness_loop_enabled=False,
        agentic_plan_dag_enabled=False,
        agentic_intent_object_enabled=False,
    )
    assert s.agentic_v3_enabled is False
    assert s.harness_loop_enabled is False
    assert s.agentic_plan_dag_enabled is False
    assert s.agentic_intent_object_enabled is False


def test_v3_master_switch_cascades_dependent_flags():
    s = GraphSettings(agentic_v3_enabled=True)
    assert s.harness_loop_enabled is True
    assert s.agentic_plan_dag_enabled is True
    assert s.agentic_intent_object_enabled is True
    assert s.agentic_answer_composer_enabled is True
    assert s.agentic_data_validator_enabled is True
    assert s.agentic_capability_guard_enabled is True
    assert s.agentic_async_enabled is True
    assert s.agentic_v3_plan_template_enabled is True


def test_explicit_override_is_respected():
    s = GraphSettings(agentic_v3_enabled=True, agentic_async_enabled=False)
    assert s.agentic_async_enabled is False  # operator override wins
    assert s.agentic_plan_dag_enabled is True  # others still cascade


def test_string_truthy_master_switch_cascades():
    s = GraphSettings(agentic_v3_enabled="1")
    assert s.agentic_v3_enabled is True
    assert s.harness_loop_enabled is True
