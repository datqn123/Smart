"""Placeholder ``DbReadonlyMcpClient`` until a transport adapter is wired.

Operators can schedule :mod:`app.cli.task005_daily`; without MCP configuration
the client raises :class:`McpTransportError` so the job exits non-zero without
silent failure (SRS §6 B5 / §7 AC6).
"""

from __future__ import annotations

from app.contracts.task005 import SqlDescribeIn, SqlQueryReadonlyIn
from app.mcp.db_readonly_port import (
    DescribeResult,
    McpTransportError,
    QueryReadonlyResult,
)


class UnconfiguredDbReadonlyClient:
    """Structural implementation of :class:`DbReadonlyMcpClient` for bootstrap."""

    _MSG = (
        "db-readonly MCP transport is not configured for Task005 "
        "(provide a real DbReadonlyMcpClient adapter)"
    )

    async def describe(self, _payload: SqlDescribeIn) -> DescribeResult:
        raise McpTransportError(self._MSG)

    async def query_readonly(
        self, _payload: SqlQueryReadonlyIn
    ) -> QueryReadonlyResult:
        raise McpTransportError(self._MSG)
