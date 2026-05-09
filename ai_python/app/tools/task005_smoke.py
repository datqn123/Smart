"""`sql.query_readonly` smoke runner for Task005 (Feature-T005-3).

Iterates over registered smoke-safe templates with their default params; the
caller persists ``SmokeArtifactEntry`` rows (template id + ok + row_count +
optional code) — never raw rows.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.contracts.task005 import (
    McpToolError,
    SqlQueryReadonlyIn,
    SqlQueryReadonlyOut,
)
from app.mcp.db_readonly_port import DbReadonlyMcpClient, McpTransportError
from app.registry.task005_templates import TemplateRegistry
from app.tools.task005_artifacts import (
    SmokeArtifactEntry,
    smoke_entry_from_failure,
    smoke_entry_from_success,
)
from app.tools.task005_logging import get_logger, log_event


@dataclass(frozen=True)
class SmokeFailure:
    template_id: str
    code: str
    message: str
    transport_error: bool = False


@dataclass
class SmokeLoopOutcome:
    tried: list[str] = field(default_factory=list)
    passed: list[str] = field(default_factory=list)
    failed: list[SmokeFailure] = field(default_factory=list)
    entries: list[SmokeArtifactEntry] = field(default_factory=list)

    @property
    def has_failures(self) -> bool:
        return bool(self.failed)


async def run_smoke_loop(
    *,
    client: DbReadonlyMcpClient,
    registry: TemplateRegistry,
    correlation_id: str,
) -> SmokeLoopOutcome:
    """Run smoke validation for each ``smoke_safe`` template."""

    logger = get_logger()
    outcome = SmokeLoopOutcome()

    for template in registry.smoke_safe_templates():
        outcome.tried.append(template.template_id)
        payload = SqlQueryReadonlyIn(
            template_id=template.template_id,
            params=dict(template.params),
        )
        try:
            result = await client.query_readonly(payload)
        except McpTransportError as err:
            outcome.failed.append(
                SmokeFailure(
                    template_id=template.template_id,
                    code="MCP_TRANSPORT_DOWN",
                    message=str(err),
                    transport_error=True,
                )
            )
            outcome.entries.append(
                smoke_entry_from_failure(
                    template_id=template.template_id,
                    code="MCP_TRANSPORT_DOWN",
                )
            )
            log_event(
                logger,
                event="smoke.transport_error",
                correlation_id=correlation_id,
                template_id=template.template_id,
                code="MCP_TRANSPORT_DOWN",
            )
            continue

        if isinstance(result, SqlQueryReadonlyOut):
            outcome.passed.append(template.template_id)
            outcome.entries.append(
                smoke_entry_from_success(result, template_id=template.template_id)
            )
            log_event(
                logger,
                event="smoke.ok",
                correlation_id=correlation_id,
                template_id=template.template_id,
                row_count=result.row_count,
            )
        elif isinstance(result, McpToolError):
            outcome.failed.append(
                SmokeFailure(
                    template_id=template.template_id,
                    code=result.code,
                    message=result.message,
                )
            )
            outcome.entries.append(
                smoke_entry_from_failure(
                    template_id=template.template_id,
                    code=result.code,
                )
            )
            log_event(
                logger,
                event="smoke.error",
                correlation_id=correlation_id,
                template_id=template.template_id,
                code=result.code,
            )

    return outcome
