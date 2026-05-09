"""`sql.describe` batch runner for Task005 (Feature-T005-2).

Iterates over the configured allowlist, calls the MCP port, and aggregates
catalog entries + per-object status. Partial failures **do not** abort the
loop (per SRS OQ-02 default = continue) — they are surfaced via
``DescribeLoopOutcome.has_failures`` so the caller can set the exit code.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Literal

from app.contracts.task005 import (
    McpToolError,
    SqlDescribeIn,
    SqlDescribeOut,
)
from app.mcp.db_readonly_port import DbReadonlyMcpClient, McpTransportError
from app.tools.task005_artifacts import SchemaCatalogEntry, catalog_entry_from_describe
from app.tools.task005_logging import get_logger, log_event

DescribeStatus = Literal["ok", "failed"]


@dataclass(frozen=True)
class DescribeFailure:
    """Per-object failure record (no payload, only error code)."""

    object_name: str
    code: str
    message: str
    transport_error: bool = False


@dataclass
class DescribeLoopOutcome:
    """Aggregate of one describe pass."""

    catalog_entries: list[SchemaCatalogEntry] = field(default_factory=list)
    results: dict[str, DescribeStatus] = field(default_factory=dict)
    failures: list[DescribeFailure] = field(default_factory=list)

    @property
    def has_failures(self) -> bool:
        return bool(self.failures)


async def run_describe_loop(
    *,
    client: DbReadonlyMcpClient,
    objects: Iterable[str],
    correlation_id: str,
) -> DescribeLoopOutcome:
    """Run ``sql.describe`` for each allowlisted object."""

    logger = get_logger()
    outcome = DescribeLoopOutcome()

    for raw_name in objects:
        object_name = raw_name.strip()
        try:
            result = await client.describe(SqlDescribeIn(object_name=object_name))
        except McpTransportError as err:
            outcome.results[object_name] = "failed"
            outcome.failures.append(
                DescribeFailure(
                    object_name=object_name,
                    code="MCP_TRANSPORT_DOWN",
                    message=str(err),
                    transport_error=True,
                )
            )
            log_event(
                logger,
                event="describe.transport_error",
                correlation_id=correlation_id,
                object_name=object_name,
                code="MCP_TRANSPORT_DOWN",
            )
            continue

        if isinstance(result, SqlDescribeOut):
            outcome.results[object_name] = "ok"
            outcome.catalog_entries.append(catalog_entry_from_describe(result))
            log_event(
                logger,
                event="describe.ok",
                correlation_id=correlation_id,
                object_name=object_name,
                column_count=len(result.columns),
            )
        elif isinstance(result, McpToolError):
            outcome.results[object_name] = "failed"
            outcome.failures.append(
                DescribeFailure(
                    object_name=object_name,
                    code=result.code,
                    message=result.message,
                )
            )
            log_event(
                logger,
                event="describe.error",
                correlation_id=correlation_id,
                object_name=object_name,
                code=result.code,
            )

    return outcome
