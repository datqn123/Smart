"""Resolve a :class:`DbReadonlyMcpClient` for scheduled corpus jobs."""

from __future__ import annotations

import os

from app.mcp.db_readonly_port import DbReadonlyMcpClient
from app.mcp.task005_unconfigured_client import UnconfiguredDbReadonlyClient


def build_db_readonly_client_from_env() -> DbReadonlyMcpClient:
    """Return the MCP client for batch jobs.

    When ``TASK005_DB_READONLY_ADAPTER`` is unset or ``stub``, returns
    :class:`UnconfiguredDbReadonlyClient` (always fails transport — use tests or
    inject a real client). Future values may select stdio/SSE adapters.
    """

    raw = os.environ.get("TASK005_DB_READONLY_ADAPTER", "").strip().lower()
    if raw in ("", "stub", "unconfigured", "none"):
        return UnconfiguredDbReadonlyClient()
    msg = f"Unknown TASK005_DB_READONLY_ADAPTER={raw!r}"
    raise RuntimeError(msg)
