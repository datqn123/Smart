from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")

logger = logging.getLogger("smart_erp_mcp")


def redact_hitl_token(token: str) -> str:
    t = token.strip()
    if len(t) <= 8:
        return "***"
    return f"{t[:4]}…{t[-2:]}"


def with_timing(tool: str, fn: Callable[[], T]) -> T:
    t0 = time.perf_counter()
    try:
        return fn()
    finally:
        ms = (time.perf_counter() - t0) * 1000
        logger.info("tool=%s duration_ms=%.2f", tool, ms)
