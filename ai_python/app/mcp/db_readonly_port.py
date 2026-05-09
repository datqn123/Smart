"""MCP `db-readonly` port — async protocol for Task005 batch consumers.

Concrete adapters (real MCP transport) live elsewhere. Task005 keeps the slice
test-friendly by depending on this protocol only — implementations may be
in-process fakes (tests) or transport-bound clients (production).

Per SRS §4 the runtime contract is **always** one of:

- ``SqlDescribeOut`` (success)
- ``McpToolError`` (failure, classified by ``code``)

so methods return a discriminated result via ``DescribeResult`` /
``QueryReadonlyResult`` aliases.
"""

from __future__ import annotations

from typing import Protocol

from app.contracts.task005 import (
    McpToolError,
    SqlDescribeIn,
    SqlDescribeOut,
    SqlQueryReadonlyIn,
    SqlQueryReadonlyOut,
)

DescribeResult = SqlDescribeOut | McpToolError
QueryReadonlyResult = SqlQueryReadonlyOut | McpToolError


class DbReadonlyMcpClient(Protocol):
    """Async port for the `db-readonly` MCP server tools used by Task005."""

    async def describe(self, payload: SqlDescribeIn) -> DescribeResult:
        """Run ``sql.describe`` for an allowlisted object."""

    async def query_readonly(
        self, payload: SqlQueryReadonlyIn
    ) -> QueryReadonlyResult:
        """Run ``sql.query_readonly`` for a registered template."""


class McpTransportError(RuntimeError):
    """Raised by adapters when the MCP transport itself is unreachable."""
