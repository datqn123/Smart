"""Slice G — K12 route accuracy gate (SRS-006 ER-1/NFR-11, QA TC-G-005/006)."""

from __future__ import annotations

from app.harness.eval_gate import (
    EvalCase,
    evaluate_case,
    route_accuracy,
    v3_rollout_allowed,
)


# --- TC-G-005: required / must-not tools enforced -------------------------

def test_required_tools_must_all_be_called():
    case = EvalCase(case_id="eval_001", required_tools=("sql_query", "answer_composer"))
    ok = evaluate_case(case, ["sql_query", "answer_composer"])
    assert ok.passed is True

    missing = evaluate_case(case, ["sql_query"])
    assert missing.passed is False
    assert "answer_composer" in missing.missing_required


def test_forbidden_tools_must_not_be_called():
    case = EvalCase(
        case_id="eval_002",
        required_tools=("answer_composer",),
        must_not_tools=("inventory_draft",),
    )
    leaked = evaluate_case(case, ["answer_composer", "inventory_draft"])
    assert leaked.passed is False
    assert "inventory_draft" in leaked.called_forbidden


def test_permission_denied_case_does_not_call_protected_tool():
    # staff finance request: must not reach sql_query on financeledger path
    case = EvalCase(case_id="eval_003", required_tools=(), must_not_tools=("sql_query",))
    blocked = evaluate_case(case, [])  # tool was blocked before execution
    assert blocked.passed is True


# --- TC-G-006: route accuracy threshold blocks rollout --------------------

def test_route_accuracy_and_rollout_gate():
    cases = [
        (EvalCase("e1", required_tools=("sql_query",)), ["sql_query"]),
        (EvalCase("e2", required_tools=("sql_query", "answer_composer")), ["sql_query"]),  # fail
        (EvalCase("e3", required_tools=("answer_composer",)), ["answer_composer"]),
        (EvalCase("e4", must_not_tools=("inventory_draft",)), ["inventory_draft"]),  # fail
    ]
    results = [evaluate_case(c, called) for c, called in cases]
    acc = route_accuracy(results)
    assert acc == 0.5  # 2 of 4 pass

    # below threshold -> rollout blocked
    assert v3_rollout_allowed(acc, threshold=0.8) is False
    # meets threshold -> rollout allowed
    assert v3_rollout_allowed(0.9, threshold=0.8) is True


def test_perfect_route_accuracy_allows_rollout():
    cases = [
        (EvalCase("e1", required_tools=("sql_query",)), ["sql_query"]),
        (EvalCase("e2", required_tools=("answer_composer",)), ["answer_composer"]),
    ]
    results = [evaluate_case(c, called) for c, called in cases]
    assert route_accuracy(results) == 1.0
    assert v3_rollout_allowed(route_accuracy(results), threshold=0.8) is True


def test_empty_eval_set_blocks_rollout():
    assert route_accuracy([]) == 0.0
    assert v3_rollout_allowed(0.0, threshold=0.8) is False
