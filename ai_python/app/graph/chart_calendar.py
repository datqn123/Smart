"""Month calendar spine hints for chart SQL (zero-fill months)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class MonthCalendarSpec:
    """Inclusive month range within a calendar year for generate_series spine."""

    year: int
    from_month: int
    to_month: int

    @property
    def month_count(self) -> int:
        return max(0, self.to_month - self.from_month + 1)

    def start_date(self) -> str:
        return f"{self.year}-{self.from_month:02d}-01"

    def end_date(self) -> str:
        return f"{self.year}-{self.to_month:02d}-01"


_ZERO_MONTH_PHRASES = (
    "tháng không có",
    "thang khong co",
    "không có đơn",
    "khong co don",
    "cũng vẽ",
    "cung ve",
    "đủ 12 tháng",
    "du 12 thang",
    "mọi tháng",
    "moi thang",
    "các tháng",
    "cac thang",
    "tháng trống",
    "thang trong",
    "zero month",
    "include zero",
)


def _blob(user_q: str, data_request: dict[str, Any] | None) -> str:
    parts = [user_q]
    if isinstance(data_request, dict):
        for k, v in data_request.items():
            parts.append(f"{k} {v}")
        cal = data_request.get("calendar")
        if isinstance(cal, dict):
            parts.append(str(cal))
        filt = data_request.get("filter") or data_request.get("filters")
        if isinstance(filt, dict):
            parts.append(str(filt))
    return " ".join(parts).lower()


def _parse_year(text: str, data_request: dict[str, Any] | None) -> int | None:
    if isinstance(data_request, dict):
        for key in ("year", "nam"):
            y = data_request.get(key)
            if isinstance(y, int) and 2000 <= y <= 2100:
                return y
            if isinstance(y, str) and y.isdigit():
                yi = int(y)
                if 2000 <= yi <= 2100:
                    return yi
        cal = data_request.get("calendar")
        if isinstance(cal, dict) and cal.get("year"):
            try:
                yi = int(cal["year"])
                if 2000 <= yi <= 2100:
                    return yi
            except (TypeError, ValueError):
                pass
        filt = data_request.get("filter") or data_request.get("filters")
        if isinstance(filt, dict) and filt.get("year"):
            try:
                yi = int(str(filt["year"]).strip()[:4])
                if 2000 <= yi <= 2100:
                    return yi
            except (TypeError, ValueError):
                pass
    m = re.search(r"\b(20\d{2})\b", text)
    if m:
        return int(m.group(1))
    return None


def _parse_month_range(text: str, data_request: dict[str, Any] | None) -> tuple[int, int] | None:
    if isinstance(data_request, dict):
        if data_request.get("include_zero_months") is True:
            cal = data_request.get("calendar")
            if isinstance(cal, dict):
                try:
                    fm = int(cal.get("from_month", 1))
                    tm = int(cal.get("to_month", 12))
                    return max(1, min(12, fm)), max(1, min(12, tm))
                except (TypeError, ValueError):
                    pass
        filt = data_request.get("filter") or data_request.get("filters")
        if isinstance(filt, dict):
            mo = filt.get("month")
            if isinstance(mo, str) and re.match(r"^\s*1\s*[-–]\s*12\s*$", mo):
                return 1, 12
    m = re.search(r"\b1\s*[-–]\s*12\b", text)
    if m:
        return 1, 12
    m = re.search(r"tháng\s*(\d{1,2})\s*[-–đến]+\s*(\d{1,2})", text)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        return max(1, min(12, a)), max(1, min(12, b))
    if "đầu năm" in text or "dau nam" in text:
        to_m = 12
        if "hiện tại" in text or "hien tai" in text or "nay" in text:
            to_m = min(12, datetime.now().month)
        return 1, to_m
    return None


def wants_zero_fill_months(user_q: str, data_request: dict[str, Any] | None = None) -> bool:
    if isinstance(data_request, dict) and data_request.get("include_zero_months") is True:
        return True
    text = _blob(user_q, data_request)
    if any(p in text for p in _ZERO_MONTH_PHRASES):
        return True
    if isinstance(data_request, dict):
        filt = data_request.get("filter") or data_request.get("filters")
        if isinstance(filt, dict) and isinstance(filt.get("month"), str):
            if re.search(r"1\s*[-–]\s*12", str(filt["month"])):
                return True
    if re.search(r"\b1\s*[-–]\s*12\b", user_q.lower()):
        return True
    return False


def resolve_month_calendar(
    user_q: str,
    data_request: dict[str, Any] | None = None,
) -> MonthCalendarSpec | None:
    if not wants_zero_fill_months(user_q, data_request):
        return None
    year = _parse_year(_blob(user_q, data_request), data_request)
    if year is None:
        year = datetime.now().year
    rng = _parse_month_range(_blob(user_q, data_request), data_request)
    if rng:
        fm, tm = rng
    else:
        fm, tm = 1, 12
    if fm > tm:
        fm, tm = tm, fm
    return MonthCalendarSpec(year=year, from_month=fm, to_month=tm)


def calendar_spine_prompt_block(spec: MonthCalendarSpec) -> str:
    n = spec.month_count
    return (
        "Month calendar spine (REQUIRED — include_zero_months):\n"
        f"- Emit exactly {n} rows, one per month from {spec.from_month:02d}/{spec.year} "
        f"through {spec.to_month:02d}/{spec.year}, including months with zero facts.\n"
        "- Use PostgreSQL generate_series for month buckets, LEFT JOIN the fact table, "
        "COALESCE(COUNT(...), 0) or COALESCE(COUNT(DISTINCT id), 0).\n"
        "- Do NOT use GROUP BY on the fact table alone (that drops empty months).\n"
        "- ORDER BY month bucket ascending.\n"
        "Pattern (adapt table/column/filter names from schema and brief):\n"
        f"  WITH months AS (\n"
        f"    SELECT (generate_series(\n"
        f"      DATE '{spec.start_date()}',\n"
        f"      DATE '{spec.end_date()}',\n"
        f"      INTERVAL '1 month'\n"
        f"    ))::date AS month_bucket\n"
        f"  )\n"
        f"  SELECT m.month_bucket AS month, COALESCE(COUNT(f.id), 0) AS metric_value\n"
        f"  FROM months m\n"
        f"  LEFT JOIN <fact_table> f ON DATE_TRUNC('month', f.<date_column>)::date = m.month_bucket\n"
        f"    AND <year_and_business_filters>\n"
        f"  GROUP BY m.month_bucket\n"
        f"  ORDER BY m.month_bucket\n"
    )
