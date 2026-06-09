"""Heuristic analysis for empty SQL results — distinguishes legitimate no-data from wrong SQL."""

from __future__ import annotations

import logging
import re
from datetime import date
from typing import Any

logger = logging.getLogger(__name__)

_NAME_COLUMNS = frozenset({
    "name", "category_name", "supplier_name", "customer_name",
    "display_name", "full_name", "product_name", "warehouse_name",
})


def _detect_year_mismatch(sql: str, user_q: str) -> str | None:
    """Check if years in SQL date filters differ from years in user question.

    Returns a warning string or None.
    """
    sql_years = set(re.findall(r"(?<!\d)(?:19|20)\d{2}(?!\d)", sql))
    user_years = set(re.findall(r"(?<!\d)(?:19|20)\d{2}(?!\d)", user_q))

    if not sql_years or not user_years:
        return None

    if not sql_years & user_years:
        return (
            f"Năm trong câu SQL ({', '.join(sorted(sql_years))}) "
            f"không khớp với năm bạn hỏi ({', '.join(sorted(user_years))}). "
            "Có thể câu SQL đang lọc sai năm."
        )

    return None


def _detect_exact_name_match(sql: str) -> str | None:
    """Detect WHERE name = '...' instead of WHERE name ILIKE '...'.

    Returns a warning string or None.
    """
    pattern = (
        r"\bWHERE\s+.*?\b("
        + "|".join(re.escape(col) for col in _NAME_COLUMNS)
        + r")\s*=\s*'([^']+)'"
    )
    m = re.search(pattern, sql, re.IGNORECASE)
    if m:
        col = m.group(1)
        val = m.group(2)
        return (
            f"Cột '{col}' đang dùng dấu '=' với giá trị '{val}' "
            f"thay vì 'ILIKE'. Có thể không tìm thấy dữ liệu do sai kiểu chữ hoa/thường."
        )
    return None


def _detect_future_dates(sql: str) -> str | None:
    """Detect date filters that reference future dates.

    Returns a warning string or None.
    """
    today = date.today()
    dates = re.findall(r"(\d{4})-(\d{2})-(\d{2})", sql)
    for yr_str, mo_str, dy_str in dates:
        try:
            d = date(int(yr_str), int(mo_str), int(dy_str))
            if d > today:
                return f"Câu SQL lọc dữ liệu từ ngày {d.isoformat()} (trong tương lai) — kết quả rỗng là hợp lệ."
        except ValueError:
            continue
    return None


_DOMAIN_FACT_TABLES: dict[str, str] = {
    "inventory": "inventory",
    "receipt": "stockreceipts",
    "dispatch": "stockdispatches",
    "ledger": "financeledger",
    "catalog_price": "products",
}


def _detect_fact_table(sql: str) -> str | None:
    m = re.search(r'\b(?:FROM|JOIN)\s+(\w+)', sql, re.IGNORECASE)
    return m.group(1).lower() if m else None


def _analyze_empty_heuristic(sql: str, user_q: str, domain: str) -> dict[str, Any]:
    """Run heuristic checks on an empty SQL result.

    Returns dict with keys: verdict, reason, warning.
    """
    warnings: list[str] = []

    yr_warn = _detect_year_mismatch(sql, user_q)
    if yr_warn:
        warnings.append(yr_warn)

    name_warn = _detect_exact_name_match(sql)
    if name_warn:
        warnings.append(name_warn)

    # Domain fact-table check
    expected_fact = _DOMAIN_FACT_TABLES.get(domain)
    if expected_fact:
        actual_fact = _detect_fact_table(sql)
        if actual_fact and actual_fact != expected_fact:
            warnings.append(
                f"Miền '{domain}' yêu cầu bảng fact '{expected_fact}' "
                f"nhưng SQL dùng '{actual_fact}'. Có thể sai bảng chính."
            )

    future_warn = _detect_future_dates(sql)
    if future_warn:
        return {
            "verdict": "legitimate",
            "reason": future_warn,
            "warning": future_warn,
        }

    if warnings:
        return {
            "verdict": "suspicious",
            "reason": "; ".join(warnings),
            "warning": "; ".join(warnings),
        }

    return {
        "verdict": "legitimate",
        "reason": "No suspicious patterns detected in empty result.",
        "warning": "",
    }
