"""Write/secret/ambiguous refusal probes (SRS §5, §10)."""

from __future__ import annotations

import re

_DML = re.compile(
    r"\b(update|delete|insert|truncate|alter|drop|merge|exec|call sp_)\b",
    re.IGNORECASE,
)
_SECRET = re.compile(
    r"(connection string|postgres://|mysql://|"
    r"mongodb(\+srv)?://|jdbc:|password\s*=|apikey|secret key|"
    r"chuỗi kết nối|mật khẩu hệ thống)",
    re.IGNORECASE,
)


def policy_probe_message(msg: str) -> str | None:
    """Return refusal code name or None if allowed to continue read slice."""
    s = msg.strip()
    if not s:
        return "POLICY_EMPTY"
    if _SECRET.search(s):
        return "POLICY_REFUSE_SECRET"
    if _DML.search(s):
        return "POLICY_REFUSE_WRITE"
    return None


def wants_clarify_branch(msg_lower: str) -> bool:
    """Heuristic SKU vs order ambiguity hook (SRS E5 family)."""
    sku = "sku" in msg_lower
    return (sku and "đơn" in msg_lower and "hay" in msg_lower) or (
        sku
        and (
            "đơn hàng" in msg_lower
            or "don hang" in msg_lower.replace("ơ", "o")
        )
    )


def should_route_db_numeric(msg_lower: str) -> bool:
    conceptual = ("giải thích quan hệ", "quan hệ giữa", "là gì", "chuẩn hóa", "diagram")
    if any(x in msg_lower for x in conceptual):
        return False
    numeric_markers = (
        "doanh thu",
        "tổng",
        "tong",
        "30 ngày",
        "30 ngay",
        "bao nhiêu",
        "số liệu",
        "so lieu",
        "theo ngày",
        "theo ngay",
    )
    return any(k in msg_lower for k in numeric_markers)


def slice_intent_for_message(msg_lower: str) -> str | None:
    """Classify coarse intent bucket for observable state."""
    if wants_clarify_branch(msg_lower):
        return "clarify"
    return "query"
