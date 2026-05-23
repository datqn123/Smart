"""sql_review structured retry hints and gen_sql retry rendering."""

from __future__ import annotations

from app.graph.feedback import append_feedback, empty_feedback, render_for_retry_prompt
from app.graph.sql_prompts import build_retry_rewrite_block
from app.graph.sql_review_hints import (
    compose_sql_review_fix_message,
    derive_deterministic_sql_fix_hint,
    infer_retry_extra_tables,
)
from app.llm.schemas import SqlReviewOutput


def test_derive_fix_hint_revenue_sources_chart() -> None:
    sql = (
        "SELECT transaction_type, SUM(amount) FROM financeledger "
        "WHERE transaction_type IN ('SalesRevenue','PurchaseCost') GROUP BY transaction_type"
    )
    hint = derive_deterministic_sql_fix_hint(
        user_q="Vẽ biểu đồ tròn các nguồn đem lại doanh thu",
        sql=sql,
        issues=["Wrong table", "Wrong column"],
        allowlist=["financeledger", "salesorders"],
        intent="system_data_chart",
    )
    assert "order_channel" in hint
    assert "SalesRevenue" in hint
    assert "transaction_type" not in hint.split("GROUP BY")[-1]


def test_infer_retry_extra_tables_adds_salesorders() -> None:
    tables = infer_retry_extra_tables(
        user_q="nguồn doanh thu theo kênh",
        sql="SELECT * FROM financeledger",
        issues=["Wrong table"],
        suggested_tables=[],
    )
    assert "salesorders" in tables


def test_compose_sql_review_fix_message_includes_mandatory_rewrite() -> None:
    review = SqlReviewOutput(
        ok=False,
        issues=["Wrong table"],
        retry_hint="Join salesorders on reference_id",
        suggested_tables=["salesorders"],
    )
    msg = compose_sql_review_fix_message(
        user_q="biểu đồ tròn nguồn doanh thu",
        sql="SELECT transaction_type FROM financeledger GROUP BY transaction_type",
        review=review,
        severe_issues=["Wrong table"],
        allowlist=["financeledger", "salesorders"],
        intent="system_data_chart",
    )
    assert "Fix (reviewer)" in msg
    assert "salesorders" in msg
    assert "rejected attempt" in msg.lower()


def test_render_for_retry_prompt_prioritizes_sql_fix() -> None:
    fb = empty_feedback()
    st: dict = {"validation_feedback": fb}
    fb = append_feedback(st, "sql_fix", "Use salesorders.order_channel")
    st["validation_feedback"] = fb
    fb = append_feedback(st, "intent_review", "old issue a")
    st["validation_feedback"] = fb
    fb = append_feedback(st, "intent_review", "latest issue")
    out = render_for_retry_prompt(fb)
    assert "[sql_fix" in out
    assert "salesorders.order_channel" in out
    assert "latest issue" in out
    assert "old issue a" not in out


def test_build_retry_rewrite_block_includes_rejected_sql() -> None:
    block = build_retry_rewrite_block(
        attempt=2,
        prior_sql="SELECT 1",
        feedback_render="[sql_fix] change tables",
        duplicate_warning=True,
    )
    assert "MANDATORY SQL REWRITE" in block
    assert "SELECT 1" in block
    assert "different tables" in block.lower()
