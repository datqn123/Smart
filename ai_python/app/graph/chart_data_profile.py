"""Query-result profiling for chart readiness (no business templates)."""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any


def _rows_from_query_result(qr: Any) -> list[dict[str, Any]]:
    if not isinstance(qr, dict):
        return []
    rows = qr.get("rows")
    if not isinstance(rows, list):
        return []
    return [dict(r) for r in rows if isinstance(r, dict)]


def _looks_like_time_value(v: Any) -> bool:
    if v is None:
        return False
    if isinstance(v, (datetime, date)):
        return True
    s = str(v).strip()
    if not s:
        return False
    if re.match(r"^\d{4}-\d{2}-\d{2}", s):
        return True
    if re.match(r"^\d{4}-\d{2}-\d{2}T", s):
        return True
    return False


def _column_profile(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    vals: list[Any] = []
    for r in rows:
        if key in r:
            vals.append(r[key])
    distinct = list(dict.fromkeys(str(v) for v in vals if v is not None))[:12]
    numeric = 0
    time_like = 0
    for v in vals[:200]:
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            numeric += 1
        elif _looks_like_time_value(v):
            time_like += 1
    return {
        "name": key,
        "non_null": len(vals),
        "distinct_sample": distinct,
        "numeric_ratio": round(numeric / max(len(vals), 1), 2),
        "time_like_ratio": round(time_like / max(len(vals), 1), 2),
    }


def build_query_result_profile(qr: Any, *, sample_rows: int = 8) -> dict[str, Any]:
    """Factual profile of executor rows for chart LLM / readiness checks."""
    rows = _rows_from_query_result(qr)
    if not rows:
        return {"row_count": 0, "columns": [], "column_profiles": [], "sample_rows": []}
    keys = list(rows[0].keys())
    profiles = [_column_profile(rows, k) for k in keys]
    time_cols = [p["name"] for p in profiles if p.get("time_like_ratio", 0) >= 0.5]
    numeric_cols = [p["name"] for p in profiles if p.get("numeric_ratio", 0) >= 0.5]
    return {
        "row_count": len(rows),
        "columns": keys,
        "column_profiles": profiles,
        "time_like_columns": time_cols,
        "numeric_columns": numeric_cols,
        "sample_rows": rows[: max(1, sample_rows)],
    }


def profile_for_prompt(profile: dict[str, Any], *, max_chars: int = 4000) -> str:
    import json

    blob = json.dumps(profile, ensure_ascii=False, default=str)
    if len(blob) <= max_chars:
        return blob
    return blob[: max_chars - 1] + "…"
