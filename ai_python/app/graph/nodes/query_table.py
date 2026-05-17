"""Emit read-only query result table for SSE (Task111)."""

from __future__ import annotations

import logging

from app.graph.agent_trace import emit_agent_trace
from app.graph.deps import GraphDeps
from app.graph.interaction_mode import should_route_query_table
from app.graph.query_table_sse import build_query_table_sse
from app.graph.state import AgentState

logger = logging.getLogger(__name__)


def make_emit_query_table_node(deps: GraphDeps):
    def emit_query_table(state: AgentState) -> dict:
        logger.info("node=emit_query_table action=start")
        if not should_route_query_table(state):
            return {}
        err = state.get("error_payload")
        if err:
            emit_agent_trace(
                logger,
                deps.settings,
                agent="query_table",
                phase="Bỏ qua bảng — lỗi SQL",
                detail=str(err)[:500],
            )
            return {}
        qr = state.get("query_result")
        payload = build_query_table_sse(
            qr,
            display_timezone=deps.settings.ai_display_timezone,
        )
        if not payload:
            emit_agent_trace(
                logger,
                deps.settings,
                agent="query_table",
                phase="Bỏ qua bảng — không có rows",
                detail="empty query_result",
            )
            return {}
        emit_agent_trace(
            logger,
            deps.settings,
            agent="query_table",
            phase="SSE data_table",
            detail=f"rowCount={payload.get('rowCount')} truncated={payload.get('truncated')}",
        )
        return {"query_table_sse": payload}

    return emit_query_table


def route_after_sql_branch(state: AgentState) -> str:
    if state.get("intent") == "system_data_chart":
        if state.get("chart_data_ok") or state.get("chart_degraded"):
            return "agent_chart"
        err = state.get("error_payload")
        if isinstance(err, dict) and err.get("error") == "max_sql_attempts":
            return "chart_fail_message"
        if state.get("chart_data_ok") is False:
            return "chart_fail_message"
        return "agent_chart"
    if should_route_query_table(state):
        return "emit_query_table"
    return "summarize_answer"
