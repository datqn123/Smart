"""Detect time-grouped SQL shape for chart readiness (avoid pointless regen)."""

from __future__ import annotations

import re


_GROUP_BY_TIME = re.compile(
    r"\bgroup\s+by\b.{0,120}\b("
    r"date_trunc|extract\s*\(\s*year|extract\s*\(\s*month|to_char\s*\("
    r")",
    re.IGNORECASE | re.DOTALL,
)

_SELECT_TIME_BUCKET = re.compile(
    r"\bselect\b.{0,200}\b(date_trunc|extract\s*\(\s*year|extract\s*\(\s*month)\s*\(",
    re.IGNORECASE | re.DOTALL,
)


def sql_has_calendar_spine(sql: str | None) -> bool:
    """True when SQL uses generate_series (or similar) for full month calendar."""
    if not sql:
        return False
    s = str(sql).lower()
    return "generate_series" in s and "left join" in s


def sql_has_time_grouping(sql: str | None) -> bool:
    """True when SQL likely buckets by time (GROUP BY + date_trunc/extract in SELECT)."""
    if not sql or not str(sql).strip():
        return False
    s = str(sql)
    if _GROUP_BY_TIME.search(s):
        return True
    if _SELECT_TIME_BUCKET.search(s) and re.search(r"\bgroup\s+by\b", s, re.IGNORECASE):
        return True
    return False
