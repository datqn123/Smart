from __future__ import annotations

from app.graph.business_scope import (
    build_followup_detail_clarify_advice,
    build_last_data_answer_context,
    check_sql_against_scope,
    is_followup_detail_reconciled,
    merge_scope_reconcile_meta,
    reconcile_detail_rows_with_previous_total,
    render_business_scope_sql_block,
    render_last_data_answer_sql_block,
    resolve_business_scope,
    scope_effective_question,
)
from app.graph.nodes.summarize import _try_single_scalar_summary
from app.graph.sql_prompts import build_gen_sql_user_prompt


def test_resolve_scope_cash_in_defaults_completed_only() -> None:
    scope = resolve_business_scope(
        "Trong năm nay, tổng số tiền thu vào từ mọi nguồn là bao nhiêu?",
        intent="system_data_query",
        previous_scope=None,
    )
    assert scope is not None
    assert scope["metric"] == "cash_in"
    assert scope["status_scope"]["mode"] == "completed_only"
    assert scope["time_scope"]["kind"] == "current_year"


def test_follow_up_inherits_previous_scope() -> None:
    prev = resolve_business_scope(
        "Tổng tiền thu vào năm nay là bao nhiêu?",
        intent="system_data_query",
        previous_scope=None,
    )
    assert prev is not None
    now = resolve_business_scope(
        "liệt kê",
        intent="system_data_query",
        previous_scope=prev,
    )
    assert now is not None
    assert now["followup"]["inherits_previous_scope"] is True
    assert "Liệt kê chi tiết" in now["effective_question"]


def test_follow_up_inherits_scope_from_last_data_answer_when_scope_missing() -> None:
    prev_scope = resolve_business_scope(
        "Tổng tiền thu vào năm nay là bao nhiêu?",
        intent="system_data_query",
        previous_scope=None,
    )
    assert prev_scope is not None
    last_ctx = build_last_data_answer_context(
        intent="system_data_query",
        user_question="Tổng tiền thu vào năm nay là bao nhiêu?",
        effective_question=scope_effective_question(
            "Tổng tiền thu vào năm nay là bao nhiêu?",
            prev_scope,
        ),
        business_scope=prev_scope,
        query_result={"rows": [{"total_received_amount": 1103700}]},
        generated_sql="SELECT 1103700 AS total_received_amount LIMIT 1",
    )
    assert isinstance(last_ctx, dict)
    now = resolve_business_scope(
        "liệt kê đi",
        intent="system_data_query",
        previous_scope=None,
        previous_data_answer=last_ctx,
    )
    assert now is not None
    assert now["metric"] == "cash_in"
    assert now["followup"]["inherits_previous_scope"] is True
    assert now["followup"]["wants_detail_breakdown"] is True


def test_force_followup_inherit_for_clarification_rewrite_sentence() -> None:
    prev = resolve_business_scope(
        "Tổng tiền thu vào năm nay là bao nhiêu?",
        intent="system_data_query",
        previous_scope=None,
    )
    assert prev is not None
    now = resolve_business_scope(
        "Liệt kê theo phiếu thu theo cùng mốc thời gian",
        intent="system_data_query",
        previous_scope=prev,
        force_followup_inherit=True,
    )
    assert now is not None
    assert now["followup"]["inherits_previous_scope"] is True
    assert now["followup"]["wants_detail_breakdown"] is True


def test_scope_sql_policy_rejects_missing_completed_filter_on_cashtransactions() -> None:
    scope = resolve_business_scope(
        "Tổng tiền thu vào tháng này",
        intent="system_data_query",
        previous_scope=None,
    )
    assert scope is not None
    ok, detail = check_sql_against_scope(
        "SELECT COALESCE(SUM(amount), 0) AS total_received_amount FROM cashtransactions LIMIT 10",
        scope,
    )
    assert not ok
    assert detail is not None and "Completed" in detail


def test_scope_sql_policy_accepts_financeledger_salesrevenue() -> None:
    scope = resolve_business_scope(
        "Tổng tiền thu vào tháng này",
        intent="system_data_query",
        previous_scope=None,
    )
    assert scope is not None
    ok, _ = check_sql_against_scope(
        "SELECT COALESCE(SUM(amount), 0) AS total_revenue FROM financeledger "
        "WHERE transaction_type = 'SalesRevenue' LIMIT 10",
        scope,
    )
    assert ok


def test_scalar_summary_hides_raw_coalesce_label() -> None:
    scope = resolve_business_scope(
        "Trong năm nay, tổng số tiền thu vào từ mọi nguồn là bao nhiêu?",
        intent="system_data_query",
        previous_scope=None,
    )
    assert scope is not None
    ans = _try_single_scalar_summary(
        {"rows": [{"coalesce": 250000}]},
        "Trong năm nay, tổng số tiền thu vào từ mọi nguồn là bao nhiêu?",
        business_scope=scope,
    )
    assert ans
    assert "Coalesce" not in ans
    assert "tổng tiền thu đã hoàn thành" in ans.lower()
    assert "250.000" in ans


def test_sql_prompt_includes_business_scope_block() -> None:
    scope = resolve_business_scope(
        "Tổng tiền thu vào năm nay",
        intent="system_data_query",
        previous_scope=None,
    )
    assert scope is not None
    scope_block = render_business_scope_sql_block(scope)
    prompt = build_gen_sql_user_prompt(
        mode="explore",
        schema_block="- financeledger(id, amount, transaction_type, transaction_date)",
        feedback_render="(none)",
        user_q=scope_effective_question("Tổng tiền thu vào năm nay", scope),
        seed_sql=None,
        sql_limit_max=100,
        business_scope_block=scope_block,
    )
    assert "Business scope contract" in prompt
    assert "SalesRevenue" in prompt


def test_sql_prompt_includes_previous_data_context_block_for_detail_followup() -> None:
    prev_scope = resolve_business_scope(
        "Tổng tiền thu vào năm nay",
        intent="system_data_query",
        previous_scope=None,
    )
    assert prev_scope is not None
    last_ctx = build_last_data_answer_context(
        intent="system_data_query",
        user_question="Tổng tiền thu vào năm nay",
        effective_question=scope_effective_question("Tổng tiền thu vào năm nay", prev_scope),
        business_scope=prev_scope,
        query_result={"rows": [{"total_received_amount": 1103700}]},
        generated_sql="SELECT 1103700 AS total_received_amount LIMIT 1",
    )
    assert isinstance(last_ctx, dict)
    scope = resolve_business_scope(
        "liệt kê",
        intent="system_data_query",
        previous_scope=prev_scope,
        previous_data_answer=last_ctx,
    )
    assert scope is not None
    scope_block = render_business_scope_sql_block(scope)
    data_block = render_last_data_answer_sql_block(last_ctx, scope)
    prompt = build_gen_sql_user_prompt(
        mode="explore",
        schema_block="- cashtransactions(id, amount, status, transaction_date)",
        feedback_render="(none)",
        user_q=scope_effective_question("liệt kê", scope),
        seed_sql=None,
        sql_limit_max=100,
        business_scope_block=scope_block,
        data_context_block=data_block,
    )
    assert "Previous answer context" in prompt
    assert "previous_scalar_total" in prompt


def test_reconcile_detail_rows_detects_mismatch_against_previous_scalar_total() -> None:
    prev_scope = resolve_business_scope(
        "Tổng tiền thu vào năm nay",
        intent="system_data_query",
        previous_scope=None,
    )
    assert prev_scope is not None
    prev_ctx = build_last_data_answer_context(
        intent="system_data_query",
        user_question="Tổng tiền thu vào năm nay",
        effective_question=scope_effective_question("Tổng tiền thu vào năm nay", prev_scope),
        business_scope=prev_scope,
        query_result={"rows": [{"total_received_amount": 1103700}]},
        generated_sql="SELECT 1103700 AS total_received_amount LIMIT 1",
    )
    assert isinstance(prev_ctx, dict)
    follow = resolve_business_scope(
        "liệt kê đi",
        intent="system_data_query",
        previous_scope=prev_scope,
        previous_data_answer=prev_ctx,
    )
    assert follow is not None
    ok, detail, meta = reconcile_detail_rows_with_previous_total(
        scope=follow,
        previous_data_answer=prev_ctx,
        query_result={
            "rows": [
                {"receipt_code": "PT-2026-0002", "amount": 250000},
            ]
        },
    )
    assert not ok
    assert detail is not None and "reconcile mismatch" in detail
    assert meta["required"] is True
    merged_scope = merge_scope_reconcile_meta(follow, meta)
    assert not is_followup_detail_reconciled(merged_scope)


def test_build_followup_clarify_advice_for_ambiguous_detail_followup() -> None:
    prev_scope = resolve_business_scope(
        "Tổng tiền thu vào năm nay",
        intent="system_data_query",
        previous_scope=None,
    )
    assert prev_scope is not None
    prev_ctx = build_last_data_answer_context(
        intent="system_data_query",
        user_question="Tổng tiền thu vào năm nay",
        effective_question=scope_effective_question("Tổng tiền thu vào năm nay", prev_scope),
        business_scope=prev_scope,
        query_result={"rows": [{"total_received_amount": 1103700}]},
        generated_sql="SELECT 1103700 AS total_received_amount LIMIT 1",
    )
    assert isinstance(prev_ctx, dict)
    advice = build_followup_detail_clarify_advice(
        user_question="liệt kê điz",
        intent="system_data_query",
        previous_scope=prev_scope,
        previous_data_answer=prev_ctx,
    )
    assert advice is not None
    assert "phiếu" in str(advice.get("suggested_rewrite") or "").lower()
