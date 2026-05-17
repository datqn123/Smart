"""Ledger-first metric definitions for schema planning and SQL prompts."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

LedgerMetricId = Literal[
    "ledger_revenue",
    "ledger_expense",
    "ledger_net_cashflow",
    "ledger_by_dimension",
]


@dataclass(frozen=True)
class LedgerMetricDef:
    id: LedgerMetricId
    fact_table: str
    transaction_types: tuple[str, ...]
    keywords: tuple[str, ...]
    requires_join: bool = False


METRICS: dict[LedgerMetricId, LedgerMetricDef] = {
    "ledger_revenue": LedgerMetricDef(
        id="ledger_revenue",
        fact_table="financeledger",
        transaction_types=("SalesRevenue",),
        keywords=(
            "doanh thu",
            "doanh số",
            "thu tiền",
            "thu nhập",
            "revenue",
            "sales revenue",
            "bán được",
            "tổng thu",
        ),
    ),
    "ledger_expense": LedgerMetricDef(
        id="ledger_expense",
        fact_table="financeledger",
        transaction_types=("PurchaseCost", "OperatingExpense"),
        keywords=(
            "chi phí",
            "chi tiền",
            "mua hàng",
            "expense",
            "cost",
            "operating",
            "tổng chi",
        ),
    ),
    "ledger_net_cashflow": LedgerMetricDef(
        id="ledger_net_cashflow",
        fact_table="financeledger",
        transaction_types=(),
        keywords=(
            "dòng tiền",
            "cashflow",
            "cash flow",
            "thu chi ròng",
            "ròng",
            "net cash",
        ),
    ),
    "ledger_by_dimension": LedgerMetricDef(
        id="ledger_by_dimension",
        fact_table="financeledger",
        transaction_types=(),
        keywords=(),
        requires_join=True,
    ),
}

_DIMENSION_KEYWORDS: dict[str, tuple[str, ...]] = {
    "order_channel": ("kênh", "retail", "wholesale", "bán lẻ", "bán buôn", "pos", "channel"),
    "customer": ("khách", "customer", "theo khách"),
    "product": ("sku", "sản phẩm", "mặt hàng", "product"),
    "fund": ("quỹ", "fund", "cash fund"),
}


def resolve_metric(user_q: str) -> LedgerMetricId:
    """Rule-based metric resolution from the user question."""
    q = user_q.lower()
    if _has_dimension_intent(q):
        if any(k in q for k in METRICS["ledger_revenue"].keywords):
            return "ledger_by_dimension"
        if any(k in q for k in METRICS["ledger_expense"].keywords):
            return "ledger_by_dimension"
    scores: list[tuple[float, LedgerMetricId]] = []
    for mid, mdef in METRICS.items():
        if mid == "ledger_by_dimension":
            continue
        score = 0.0
        for kw in mdef.keywords:
            if kw in q:
                score += float(len(kw))
        scores.append((score, mid))
    scores.sort(key=lambda x: -x[0])
    if scores and scores[0][0] > 0:
        return scores[0][1]
    return "ledger_revenue"


def _has_dimension_intent(q: str) -> bool:
    for kws in _DIMENSION_KEYWORDS.values():
        if any(k in q for k in kws):
            return True
    return bool(re.search(r"\btheo\b", q))


def detect_dimensions(user_q: str) -> list[str]:
    q = user_q.lower()
    out: list[str] = []
    for dim, kws in _DIMENSION_KEYWORDS.items():
        if any(k in q for k in kws):
            out.append(dim)
    return out


def ledger_sql_hints(metric_id: LedgerMetricId) -> list[str]:
    """Prompt lines for gen_sql."""
    mdef = METRICS[metric_id]
    lines = [
        f"Fact table (required): {mdef.fact_table}",
        "Use transaction_date for time filters (month/year), not salesorders.created_at unless user asks order creation date.",
    ]
    if mdef.transaction_types:
        types = ", ".join(f"'{t}'" for t in mdef.transaction_types)
        lines.append(f"Filter transaction_type IN ({types}) for this metric.")
    if metric_id == "ledger_net_cashflow":
        lines.append("Net cashflow: SUM(amount) on financeledger without restricting to SalesRevenue only.")
    if metric_id in ("ledger_by_dimension",) or mdef.requires_join:
        lines.append("Join dimension tables via reference_type/reference_id from financeledger (see join paths).")
    return lines


def default_tables_for_metric(metric_id: LedgerMetricId, dimensions: list[str]) -> list[str]:
    """Minimal table set before LLM refinement."""
    tables = ["financeledger"]
    if metric_id == "ledger_by_dimension" or dimensions:
        if "order_channel" in dimensions or metric_id == "ledger_by_dimension":
            if "salesorders" not in tables:
                tables.append("salesorders")
        if "customer" in dimensions:
            for t in ("salesorders", "customers"):
                if t not in tables:
                    tables.append(t)
        if "product" in dimensions:
            for t in ("salesorders", "orderdetails", "products"):
                if t not in tables:
                    tables.append(t)
        if "fund" in dimensions and "cash_funds" not in tables:
            tables.append("cash_funds")
    return tables
