"""Polymorphic reference_type → SQL join paths from financeledger."""

from __future__ import annotations

from dataclasses import dataclass

_LEDGER_ALIAS = "fl"


@dataclass(frozen=True)
class ReferenceJoinSpec:
    reference_type: str
    target_table: str
    join_sql: str
    description: str


_REFERENCE_JOINS: dict[str, ReferenceJoinSpec] = {
    "SalesOrder": ReferenceJoinSpec(
        reference_type="SalesOrder",
        target_table="salesorders",
        join_sql=(
            "JOIN salesorders so ON fl.reference_type = 'SalesOrder' "
            "AND fl.reference_id = so.id"
        ),
        description="Drill-down to sales order header (channel, customer, status).",
    ),
    "StockReceipt": ReferenceJoinSpec(
        reference_type="StockReceipt",
        target_table="stockreceipts",
        join_sql=(
            "JOIN stockreceipts sr ON fl.reference_type = 'StockReceipt' "
            "AND fl.reference_id = sr.id"
        ),
        description="Link purchase-cost postings to stock receipt.",
    ),
    "CashTransaction": ReferenceJoinSpec(
        reference_type="CashTransaction",
        target_table="cashtransactions",
        join_sql=(
            "JOIN cashtransactions ct ON fl.reference_type = 'CashTransaction' "
            "AND fl.reference_id = ct.id"
        ),
        description="Manual cash in/out linked to ledger row.",
    ),
}

_DIMENSION_TABLES: dict[str, list[str]] = {
    "order_channel": ["salesorders"],
    "customer": ["salesorders", "customers"],
    "product": ["salesorders", "orderdetails", "products"],
    "fund": ["cash_funds"],
}

_DIMENSION_EXTRA_JOINS: dict[str, list[str]] = {
    "customer": [
        "JOIN customers c ON so.customer_id = c.id",
    ],
    "product": [
        "JOIN orderdetails od ON so.id = od.order_id",
        "JOIN products p ON od.product_id = p.id",
    ],
    "fund": [
        "JOIN cash_funds cf ON fl.fund_id = cf.id",
    ],
}


def get_reference_join(reference_type: str) -> ReferenceJoinSpec | None:
    return _REFERENCE_JOINS.get(reference_type)


def tables_for_dimensions(dimensions: list[str]) -> list[str]:
    out = ["financeledger"]
    for dim in dimensions:
        for t in _DIMENSION_TABLES.get(dim, []):
            if t not in out:
                out.append(t)
    return out


def join_hints_for_plan(
    *,
    tables: list[str],
    dimensions: list[str],
    ledger_alias: str = _LEDGER_ALIAS,
) -> list[str]:
    """Human-readable join paths for prompts."""
    _ = ledger_alias
    hints: list[str] = []
    table_set = {t.lower() for t in tables}
    if "salesorders" in table_set:
        spec = _REFERENCE_JOINS["SalesOrder"]
        hints.append(spec.join_sql.replace("fl", _LEDGER_ALIAS))
    if "stockreceipts" in table_set:
        hints.append(_REFERENCE_JOINS["StockReceipt"].join_sql.replace("fl", _LEDGER_ALIAS))
    if "cashtransactions" in table_set:
        hints.append(_REFERENCE_JOINS["CashTransaction"].join_sql.replace("fl", _LEDGER_ALIAS))
    for dim in dimensions:
        for extra in _DIMENSION_EXTRA_JOINS.get(dim, []):
            if extra not in hints:
                hints.append(extra)
    return hints


def salesorders_join_requires_reference_type(sql: str) -> bool:
    """True if SQL uses salesorders without reference_type guard (policy hint)."""
    low = sql.lower()
    if "salesorders" not in low and " salesorders " not in f" {low} ":
        if "salesorders" not in low:
            return False
    if "financeledger" not in low:
        return False
    if "reference_type" in low and "salesorder" in low.replace(" ", ""):
        return False
    return True
