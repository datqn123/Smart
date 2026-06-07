"""Capability, sensitive data masking and safety helpers."""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")

SENSITIVE_COLUMNS = {
    "cost_price",
    "costprice",
    "margin",
    "gross_margin",
    "debt_balance",
    "finance_ledger",
    "financeledger",
}


class CapabilityMatrix:
    def can(self, role: str | None, action: str) -> bool:
        if role is None:
            return True
        normalized = (role or "staff").lower()
        if normalized == "owner":
            return True
        if action in {"data_read", "chat"}:
            return True
        return False

    def mask_columns(self, role: str | None, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if (role or "").lower() == "owner":
            return [dict(row) for row in rows]
        masked: list[dict[str, Any]] = []
        for row in rows:
            masked.append(
                {
                    key: value
                    for key, value in row.items()
                    if key.lower() not in SENSITIVE_COLUMNS
                }
            )
        return masked


class IdempotencyGuard:
    def __init__(self) -> None:
        self._results: dict[str, Any] = {}

    def run_once(self, key: str, func: Callable[[], T]) -> T:
        if key in self._results:
            return self._results[key]
        result = func()
        self._results[key] = result
        return result


def sanitize_user_data(text: str) -> str:
    cleaned: list[str] = []
    for line in (text or "").splitlines():
        low = line.lower()
        if "ignore previous" in low or "ignore all previous" in low:
            continue
        if re.match(r"\s*(system|assistant|developer)\s*:", low):
            continue
        cleaned.append(line)
    return "\n".join(cleaned)
