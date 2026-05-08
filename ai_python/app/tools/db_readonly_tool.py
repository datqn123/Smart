from __future__ import annotations

import time

from ..contracts import McpToolError, QueryReadonlyIn, QueryReadonlyOut
from ..mcp.db_readonly_port import DbReadonlyMcpPort
from ..observability import ToolAuditRecord, log_tool_audit


async def run_query_readonly_once(
    db: DbReadonlyMcpPort,
    body: QueryReadonlyIn,
    *,
    correlation_id: str,
    user_id: str | None,
    session_id: str | None,
) -> tuple[QueryReadonlyOut | None, McpToolError | None]:
    t0 = time.perf_counter()
    out, err = await db.sql_query_readonly(body, correlation_id=correlation_id)
    log_tool_audit(
        ToolAuditRecord(
            user_id=user_id,
            session_id=session_id,
            tool_name="db-readonly.sql.query_readonly",
            correlation_id=correlation_id,
            duration_ms=(time.perf_counter() - t0) * 1000,
        ),
        summary="redacted",
    )
    return out, err
