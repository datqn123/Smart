"""SQL subgraph (TASK-LG-08 … LG-11)."""

from __future__ import annotations

import logging

from langgraph.graph import END, START, StateGraph

from app.graph.deps import GraphDeps
from app.graph.nodes.chart_readiness import (
    make_chart_readiness_node,
    route_after_chart_readiness_in_sql,
)
from app.graph.nodes.schema_explore import make_schema_explore_node, route_sql_subgraph_start
from app.graph.nodes.sql_pipeline import (
    make_entity_resolution_node,
    make_execute_sql_node,
    make_fail_max_attempts_node,
    make_gen_sql_node,
    make_sql_review_node,
    make_validate_result_node,
    make_validate_sql_node,
    route_after_sql_review,
    route_after_validate_result,
    route_after_validate_sql,
)
from app.graph.progress import wrap_node_with_stream_progress as wrap
from app.graph.state import AgentState
from app.graph.verify_sql_intent import make_verify_sql_intent_node
from app.graph.analyze_empty_result import make_analyze_empty_result_node

logger = logging.getLogger(__name__)


def _route_after_gen_sql(state: AgentState) -> str:
    err = state.get("error_payload")
    if err and err.get("error") in ("schema_load_failed", "schema_catalog_failed"):
        logger.info("sql_route from=gen_sql to=fail_max_attempts reason=error_payload")
        return "fail_max_attempts"
    logger.info("sql_route from=gen_sql to=verify_sql_intent reason=no_error")
    return "verify_sql_intent"


def _route_after_verify_sql_intent(state: AgentState) -> str:
    action = state.get("verify_intent_action", "proceed")
    if action == "regen":
        attempt = int(state.get("sql_attempt_count") or 0)
        max_attempts = int(state.get("sql_repair_max_attempts") or 3)
        if attempt >= max_attempts:
            logger.info("sql_route from=verify_sql_intent to=fail_max_attempts reason=max_attempts attempt=%s/%s", attempt, max_attempts)
            return "fail_max_attempts"
        logger.info("sql_route from=verify_sql_intent to=gen_sql reason=regen attempt=%s/%s", attempt, max_attempts)
        return "gen_sql"
    if action == "bypass_review":
        logger.info("sql_route from=verify_sql_intent to=execute_sql reason=bypass_review")
        return "execute_sql"
    logger.info("sql_route from=verify_sql_intent to=sql_review reason=proceed")
    return "sql_review"


def _route_after_execute_sql(state: AgentState) -> str:
    qr = state.get("query_result")
    if qr is None:
        logger.info("sql_route from=execute_sql to=validate_result reason=no_query_result")
        return "validate_result"
    rows = qr.get("rows") if isinstance(qr, dict) else None
    if isinstance(rows, list) and len(rows) == 0:
        logger.info("sql_route from=execute_sql to=analyze_empty_result reason=empty_rows")
        return "analyze_empty_result"
    logger.info("sql_route from=execute_sql to=validate_result reason=has_rows")
    return "validate_result"


def _route_after_analyze_empty(state: AgentState) -> str:
    verdict = state.get("empty_verdict", "legitimate")
    if verdict == "wrong":
        attempt = int(state.get("sql_attempt_count") or 0)
        max_attempts = int(state.get("sql_repair_max_attempts") or 3)
        if attempt >= max_attempts:
            logger.info("sql_route from=analyze_empty to=fail_max_attempts reason=wrong_maxed attempt=%s/%s", attempt, max_attempts)
            return "fail_max_attempts"
        logger.info("sql_route from=analyze_empty to=gen_sql reason=wrong attempt=%s/%s", attempt, max_attempts)
        return "gen_sql"
    logger.info("sql_empty_verdict verdict=%s reason=legitimate", verdict)
    return "validate_result"


def build_sql_subgraph(deps: GraphDeps):
    g = StateGraph(AgentState)
    g.add_node("schema_explore", wrap("schema_explore", make_schema_explore_node(deps)))
    g.add_node("gen_sql", wrap("gen_sql", make_gen_sql_node(deps)))
    g.add_node("verify_sql_intent", wrap("verify_sql_intent", make_verify_sql_intent_node(deps)))
    g.add_node("sql_review", wrap("sql_review", make_sql_review_node(deps)))
    g.add_node("validate_sql", wrap("validate_sql", make_validate_sql_node(deps)))
    g.add_node("execute_sql", wrap("execute_sql", make_execute_sql_node(deps)))
    g.add_node("analyze_empty_result", wrap("analyze_empty_result", make_analyze_empty_result_node(deps)))
    g.add_node("validate_result", wrap("validate_result", make_validate_result_node(deps)))
    g.add_node("chart_readiness", wrap("chart_readiness", make_chart_readiness_node(deps)))
    g.add_node("fail_max_attempts", wrap("fail_max_attempts", make_fail_max_attempts_node(deps)))

    g.add_conditional_edges(
        START,
        route_sql_subgraph_start(deps),
        {
            "schema_explore": "schema_explore",
            "gen_sql": "gen_sql",
        },
    )
    # Entity resolution step (between schema_explore and gen_sql)
    if deps.settings.entity_resolution_enabled:
        g.add_node("resolve_entities", wrap("resolve_entities", make_entity_resolution_node(deps)))
        g.add_edge("schema_explore", "resolve_entities")
        g.add_edge("resolve_entities", "gen_sql")
    else:
        g.add_edge("schema_explore", "gen_sql")
    g.add_conditional_edges(
        "gen_sql",
        _route_after_gen_sql,
        {
            "verify_sql_intent": "verify_sql_intent",
            "fail_max_attempts": "fail_max_attempts",
        },
    )
    g.add_conditional_edges(
        "verify_sql_intent",
        _route_after_verify_sql_intent,
        {
            "sql_review": "sql_review",
            "gen_sql": "gen_sql",
            "execute_sql": "execute_sql",
            "fail_max_attempts": "fail_max_attempts",
        },
    )
    g.add_conditional_edges(
        "sql_review",
        route_after_sql_review,
        {
            "validate_sql": "validate_sql",
            "gen_sql": "gen_sql",
            "fail_max_attempts": "fail_max_attempts",
        },
    )
    g.add_conditional_edges(
        "validate_sql",
        route_after_validate_sql,
        {
            "execute_sql": "execute_sql",
            "gen_sql": "gen_sql",
            "fail_max_attempts": "fail_max_attempts",
        },
    )
    g.add_conditional_edges(
        "execute_sql",
        _route_after_execute_sql,
        {
            "validate_result": "validate_result",
            "analyze_empty_result": "analyze_empty_result",
        },
    )
    g.add_conditional_edges(
        "analyze_empty_result",
        _route_after_analyze_empty,
        {
            "validate_result": "validate_result",
            "gen_sql": "gen_sql",
            "fail_max_attempts": "fail_max_attempts",
        },
    )
    g.add_conditional_edges(
        "validate_result",
        route_after_validate_result,
        {
            "done": END,
            "chart_readiness": "chart_readiness",
            "gen_sql": "gen_sql",
            "fail_max_attempts": "fail_max_attempts",
        },
    )
    g.add_conditional_edges(
        "chart_readiness",
        route_after_chart_readiness_in_sql,
        {
            "done": END,
            "gen_sql": "gen_sql",
            "fail_max_attempts": "fail_max_attempts",
        },
    )
    g.add_edge("fail_max_attempts", END)
    logger.debug("sql_subgraph_compile nodes=%s", list(g.nodes.keys()))
    return g
