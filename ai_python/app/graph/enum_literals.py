"""Canonical ERP enum string literals (PostgreSQL case-sensitive)."""

from __future__ import annotations

import re

# Columns that commonly appear in AI-generated WHERE clauses.
_ENUM_FILTER_COLUMNS = (
    "status",
    "payment_status",
    "order_channel",
    "direction",
    "partner_type",
    "action_type",
    "transaction_type",
    "discount_type",
    "alert_type",
    "channel",
    "frequency",
    "log_level",
    "sender",
    "file_type",
)

# All CHECK / enum literals from ai_column_description (V49+). Keys: lowercase → canonical.
_ENUM_LITERAL_CANONICAL: dict[str, str] = {}
for _vals in (
    ("Active", "Inactive"),
    ("Active", "Maintenance", "Inactive"),
    ("Active", "Locked"),
    ("Draft", "Pending", "Approved", "Rejected"),
    ("Pending", "Processing", "Partial", "Shipped", "Delivered", "Cancelled"),
    ("Paid", "Unpaid"),
    ("Retail", "Wholesale", "Return"),
    ("Pending", "Full", "Partial", "Cancelled", "WaitingDispatch", "Delivering", "Delivered"),
    ("Income", "Expense"),
    ("Completed",),
    ("InDebt", "Cleared"),
    ("Customer", "Supplier"),
    ("Processed",),
    ("Pending", "In Progress", "Pending Owner Approval", "Completed", "Cancelled", "Re-check"),
    ("INBOUND", "OUTBOUND", "TRANSFER", "ADJUSTMENT"),
    ("SalesRevenue", "PurchaseCost", "OperatingExpense", "Refund"),
    ("LowStock", "ExpiryDate", "HighValueTransaction", "PendingApproval", "PartnerDebtDueSoon"),
    ("App", "Email", "SMS", "Zalo"),
    ("Realtime", "Daily", "Weekly"),
    ("INFO", "WARNING", "ERROR", "CRITICAL"),
    ("User", "Bot"),
    ("OCR_Image", "Voice_Audio"),
    ("Percent", "FixedAmount"),
):
    for v in _vals:
        _ENUM_LITERAL_CANONICAL[v.lower()] = v

_EQ_PATTERN = re.compile(
    r"\b(" + "|".join(_ENUM_FILTER_COLUMNS) + r")\s*=\s*'([^']*)'",
    re.IGNORECASE,
)
_IN_PATTERN = re.compile(
    r"\b(" + "|".join(_ENUM_FILTER_COLUMNS) + r")\s+IN\s*\(([^)]*)\)",
    re.IGNORECASE,
)
_IN_STRING = re.compile(r"'([^']*)'")


def canonical_enum_literal(value: str) -> str:
    """Return Pascal/correct-case literal if known; else unchanged."""
    key = (value or "").strip().lower()
    if not key:
        return value
    return _ENUM_LITERAL_CANONICAL.get(key, value)


def fix_enum_literals_in_sql(sql: str) -> tuple[str, list[str]]:
    """
    Rewrite wrong-case enum string literals next to known filter columns.
    Returns (sql, notes) e.g. ['status: approved → Approved'].
    """
    notes: list[str] = []

    def _fix_eq(m: re.Match[str]) -> str:
        col, raw = m.group(1), m.group(2)
        canon = canonical_enum_literal(raw)
        if canon != raw:
            notes.append(f"{col}: {raw!r} → {canon!r}")
            return f"{col} = '{canon}'"
        return m.group(0)

    out = _EQ_PATTERN.sub(_fix_eq, sql)

    def _fix_in(m: re.Match[str]) -> str:
        col, inner = m.group(1), m.group(2)

        def _fix_str(sm: re.Match[str]) -> str:
            raw = sm.group(1)
            canon = canonical_enum_literal(raw)
            if canon != raw:
                notes.append(f"{col} IN: {raw!r} → {canon!r}")
                return f"'{canon}'"
            return sm.group(0)

        fixed_inner = _IN_STRING.sub(_fix_str, inner)
        if fixed_inner != inner:
            return f"{col} IN ({fixed_inner})"
        return m.group(0)

    out = _IN_PATTERN.sub(_fix_in, out)
    return out, notes


def enum_literals_prompt_block() -> str:
    """Compact rules for gen_sql — case-sensitive string enums."""
    return (
        "Enum literals (PostgreSQL string comparison is CASE-SENSITIVE — copy exact spelling):\n"
        "- stockreceipts.status: Draft | Pending | Approved | Rejected (approved receipts: status = 'Approved').\n"
        "- salesorders.status: Pending | Processing | Partial | Shipped | Delivered | Cancelled.\n"
        "- salesorders.order_channel: Retail | Wholesale | Return (never 'Export').\n"
        "- salesorders.payment_status: Paid | Unpaid | Partial.\n"
        "- stockdispatches.status: Pending | Full | Partial | Cancelled | WaitingDispatch | "
        "Delivering | Delivered; active rows: deleted_at IS NULL.\n"
        "- cashtransactions.status: Pending | Completed | Cancelled; direction: Income | Expense.\n"
        "- financeledger.transaction_type: SalesRevenue | PurchaseCost | OperatingExpense | Refund.\n"
        "- Master data status (categories, suppliers, customers, products): Active | Inactive.\n"
        "- users.status: Active | Locked; partnerdebts.status: InDebt | Cleared; "
        "partner_type: Customer | Supplier.\n"
        "- inventorylogs.action_type: INBOUND | OUTBOUND | TRANSFER | ADJUSTMENT.\n"
    )
