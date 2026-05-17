"""Resolve missing_slots / noop issues before clarify vs proceed."""

from __future__ import annotations

import re
from datetime import datetime

from app.llm.schemas import DomainIssue

# User already gave a relative or absolute time window — do not ask "năm nào?"
_TIME_RANGE_PATTERNS = [
    r"từ\s+đầu\s+năm",
    r"đầu\s+năm\s+\d{4}",
    r"từ\s+đầu\s+năm\s+\d{4}",
    r"từ\s+tháng\s+\d",
    r"tháng\s+này",
    r"tháng\s+trước",
    r"quý\s+[1234]",
    r"năm\s+nay",
    r"năm\s+\d{4}",
    r"tới\s+giờ",
    r"đến\s+nay",
    r"hiện\s+tại",
    r"hôm\s+nay",
    r"tuần\s+này",
    r"trong\s+tháng",
    r"ytd",
]

_YEAR_SLOT_KEYWORDS = frozenset(
    {
        "year",
        "năm",
        "nam",
        "which year",
        "năm nào",
        "cho năm",
        "thời gian",
        "time period",
        "khoảng thời gian",
        "date range",
    }
)

_ORDER_STATUS_SLOT_KEYWORDS = frozenset(
    {
        "completed",
        "hoàn tất",
        "hoan tat",
        "trạng thái",
        "trang thai",
        "status",
        "đã hoàn",
        "da hoan",
    }
)


def _norm(s: str) -> str:
    return (s or "").strip().lower()


def has_time_range_in_question(question: str) -> bool:
    q = _norm(question)
    if not q:
        return False
    for pat in _TIME_RANGE_PATTERNS:
        if re.search(pat, q, re.IGNORECASE):
            return True
    if re.search(r"\b20\d{2}\b", q):
        return True
    return False


def _slot_mentions_year(slot: str) -> bool:
    s = _norm(slot)
    return any(k in s for k in _YEAR_SLOT_KEYWORDS)


def _slot_mentions_order_status(slot: str) -> bool:
    s = _norm(slot)
    return any(k in s for k in _ORDER_STATUS_SLOT_KEYWORDS)


def filter_resolved_missing_slots(question: str, missing_slots: list[str]) -> list[str]:
    """Drop slots already satisfied by the user message."""
    if not missing_slots:
        return []
    has_time = has_time_range_in_question(question)
    kept: list[str] = []
    for slot in missing_slots:
        s = str(slot).strip()
        if not s:
            continue
        if has_time and _slot_mentions_year(s):
            continue
        kept.append(s)
    return kept


def strip_noop_issues(issues: list[DomainIssue]) -> list[DomainIssue]:
    """Remove fake term fixes (canonical equals user phrase)."""
    out: list[DomainIssue] = []
    for i in issues:
        if i.type == "term_mismatch":
            u = _norm(i.user_text)
            c = _norm(i.canonical_vi or "")
            if u and c and u == c:
                continue
        out.append(i)
    return out


def has_blocking_issues(issues: list[DomainIssue]) -> bool:
    return any(i.severity == "block" and i.type == "term_mismatch" for i in issues)


def append_slot_hints_to_question(question: str, missing_slots: list[str]) -> str:
    """Light defaults for optional slots when we still clarify."""
    q = question.strip()
    if not q:
        return q
    extras: list[str] = []
    for slot in missing_slots:
        s = _norm(slot)
        if _slot_mentions_order_status(s) and "hoàn tất" not in _norm(q) and "đã" not in _norm(q):
            extras.append("đơn đã hoàn tất")
    if not extras:
        return q
    if not q.endswith("?"):
        q = q + "?"
    return f"{q.rstrip('?')} ({', '.join(extras)})?"


def default_normalized_for_proceed(question: str) -> str:
    """Normalize time phrase for SQL-friendly wording when proceeding."""
    q = question.strip()
    year = datetime.now().year
    if re.search(r"từ\s+đầu\s+năm(?!\s+\d{4})", q, re.IGNORECASE):
        q = re.sub(
            r"từ\s+đầu\s+năm",
            f"từ đầu năm {year}",
            q,
            count=1,
            flags=re.IGNORECASE,
        )
    return q
