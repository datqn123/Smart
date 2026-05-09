"""Resolve a :class:`DbReadonlyMcpClient` for scheduled corpus jobs."""

from __future__ import annotations

import os

from app.mcp.db_readonly_port import DbReadonlyMcpClient
from app.mcp.spring_http_client import SpringHttpDbReadonlyClient
from app.mcp.task005_unconfigured_client import UnconfiguredDbReadonlyClient


def build_db_readonly_client_from_env() -> DbReadonlyMcpClient:
    """Return the MCP client for batch jobs.

    When ``TASK005_DB_READONLY_ADAPTER`` is unset or ``stub``, returns
    :class:`UnconfiguredDbReadonlyClient` (always fails transport — use tests or
    inject a real client). ``spring`` uses the Spring REST bridge (smart-erp).
    """

    raw = os.environ.get("TASK005_DB_READONLY_ADAPTER", "").strip().lower()
    if raw in ("", "stub", "unconfigured", "none"):
        return UnconfiguredDbReadonlyClient()
    if raw in ("spring", "spring-http", "erp"):
        base = os.environ.get("SPRING_AI_DB_BASE_URL", "http://localhost:8080").rstrip("/")
        timeout = float(os.environ.get("SPRING_AI_DB_TIMEOUT_SEC", "60"))
        return SpringHttpDbReadonlyClient(base_url=base, timeout_s=timeout)
    msg = f"Unknown TASK005_DB_READONLY_ADAPTER={raw!r}"
    raise RuntimeError(msg)
