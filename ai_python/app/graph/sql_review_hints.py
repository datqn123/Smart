"""Structured SQL review feedback and deterministic retry hints for gen_sql."""

from __future__ import annotations

import re

from app.graph.ledger_metrics import detect_dimensions
from app.llm.schemas import SqlReviewOutput

_REVENUE_PHRASES = ("doanh thu", "doanh so", "revenue", "sales revenue")
_SOURCE_PHRASES = ("nguồn", "nguon", "source", "kênh", "kenh", "channel")
_WRONG_TABLE = re.compile(r"wrong\s+table", re.IGNORECASE)
_WRONG_COLUMN = re.compile(r"wrong\s+column", re.IGNORECASE)


def derive_deterministic_sql_fix_hint(
    *,
    user_q: str,
    sql: str,
    issues: list[str],
    allowlist: list[str] | None = None,
    intent: str | None = None,
) -> str:
    """Rule-based fix when LLM review issues are vague (Wrong table/column)."""
    q = user_q.lower()
    sql_low = sql.lower()
    issue_blob = " ".join(issues).lower()
    allow = {t.lower() for t in (allowlist or [])}
    hints: list[str] = []

    revenue_q = any(p in q for p in _REVENUE_PHRASES)
    source_q = any(p in q for p in _SOURCE_PHRASES)
    dims = detect_dimensions(user_q)
    is_chart = intent == "system_data_chart"

    if revenue_q and (source_q or "order_channel" in dims):
        if "financeledger" in sql_low and "salesorders" not in sql_low:
            hints.append(
                "Revenue by source/channel: join financeledger fl to salesorders so "
                "(fl.reference_type = 'SalesOrder' AND fl.reference_id = so.id), "
                "filter fl.transaction_type = 'SalesRevenue', "
                "GROUP BY so.order_channel (alias columns for pie chart). "
                "Do NOT GROUP BY fl.transaction_type for a revenue-sources chart."
            )
        elif "salesorders" in sql_low and "group by" in sql_low and "transaction_type" in sql_low:
            hints.append(
                "Use so.order_channel as the breakdown dimension, not transaction_type."
            )

    if is_chart and revenue_q and "group by" in sql_low and "transaction_type" in sql_low:
        if "purchasecost" in sql_low or "operatingexpense" in sql_low:
            hints.append(
                "Pie chart for revenue sources: include only SalesRevenue rows "
                "(WHERE transaction_type = 'SalesRevenue'), not expense/refund types."
            )

    if _WRONG_TABLE.search(issue_blob) and revenue_q and source_q:
        if "salesorders" in allow or not allow:
            hints.append(
                "Fact/dimension for «nguồn doanh thu»: salesorders.order_channel "
                "(optionally via financeledger SalesRevenue join as above)."
            )

    if _WRONG_COLUMN.search(issue_blob) and "transaction_type" in sql_low and revenue_q:
        hints.append(
            "Replace transaction_type in SELECT/GROUP BY with a business dimension "
            "(e.g. order_channel) unless the user asked for ledger entry types."
        )

    return " ".join(hints).strip()


def infer_retry_extra_tables(
    *,
    user_q: str,
    sql: str,
    issues: list[str],
    suggested_tables: list[str] | None = None,
) -> list[str]:
    """Tables to merge into schema allowlist on gen_sql retry."""
    out: list[str] = []
    for t in suggested_tables or []:
        key = t.strip().lower()
        if key and key not in {x.lower() for x in out}:
            out.append(t.strip())

    q = user_q.lower()
    sql_low = sql.lower()
    issue_blob = " ".join(issues).lower()

    def add(name: str) -> None:
        if name.lower() not in {x.lower() for x in out}:
            out.append(name)

    if any(p in q for p in _SOURCE_PHRASES) and any(p in q for p in _REVENUE_PHRASES):
        add("salesorders")
    if "order_channel" in detect_dimensions(user_q):
        add("salesorders")
    if _WRONG_TABLE.search(issue_blob) and "financeledger" in sql_low:
        if any(p in q for p in _SOURCE_PHRASES + ("kênh", "kenh")):
            add("salesorders")
    if "customer" in detect_dimensions(user_q):
        add("customers")
    if "product" in detect_dimensions(user_q):
        add("orderdetails")
        add("products")

    return out


def compose_sql_review_fix_message(
    *,
    user_q: str,
    sql: str,
    review: SqlReviewOutput,
    severe_issues: list[str],
    allowlist: list[str] | None = None,
    intent: str | None = None,
) -> str:
    """Single actionable block for gen_sql retry (stored in validation_feedback.sql_fix)."""
    llm_hint = (review.retry_hint or "").strip()
    det = derive_deterministic_sql_fix_hint(
        user_q=user_q,
        sql=sql,
        issues=severe_issues,
        allowlist=allowlist,
        intent=intent,
    )
    extra_tables = infer_retry_extra_tables(
        user_q=user_q,
        sql=sql,
        issues=severe_issues,
        suggested_tables=list(review.suggested_tables or []),
    )

    parts: list[str] = []
    if severe_issues:
        parts.append("Problems: " + "; ".join(severe_issues[:6]))
    if llm_hint:
        parts.append(f"Fix (reviewer): {llm_hint}")
    if det:
        parts.append(f"Fix (rules): {det}")
    if extra_tables:
        parts.append("Required allowlist tables for next attempt: " + ", ".join(extra_tables))
    parts.append(
        "Rewrite the SELECT: change FROM/JOIN, GROUP BY, and/or WHERE — "
        "do not return the same SQL as the rejected attempt."
    )
    return "\n".join(parts)
