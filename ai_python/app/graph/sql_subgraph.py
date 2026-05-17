"""SQL subgraph (TASK-LG-08 … LG-11)."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.graph.deps import GraphDeps
from app.graph.nodes.chart_readiness import (
    make_chart_readiness_node,
    route_after_chart_readiness_in_sql,
)
from app.graph.nodes.schema_explore import make_schema_explore_node, route_sql_subgraph_start
from app.graph.nodes.sql_pipeline import (
    make_execute_sql_node,
    make_fail_max_attempts_node,
    make_gen_sql_node,
    make_sql_review_node,
    make_validate_result_node,
    make_validate_sql_node,
    route_after_gen_sql,
    route_after_sql_review,
    route_after_validate_result,
    route_after_validate_sql,
)
from app.graph.progress import wrap_node_with_stream_progress as wrap
from app.graph.state import AgentState


def build_sql_subgraph(deps: GraphDeps):
    g = StateGraph(AgentState)
    g.add_node("schema_explore", wrap("schema_explore", make_schema_explore_node(deps)))
    g.add_node("gen_sql", wrap("gen_sql", make_gen_sql_node(deps)))
    g.add_node("sql_review", wrap("sql_review", make_sql_review_node(deps)))
    g.add_node("validate_sql", wrap("validate_sql", make_validate_sql_node(deps)))
    g.add_node("execute_sql", wrap("execute_sql", make_execute_sql_node(deps)))
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
    g.add_edge("schema_explore", "gen_sql")
    g.add_conditional_edges(
        "gen_sql",
        route_after_gen_sql,
        {
            "sql_review": "sql_review",
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
    g.add_edge("execute_sql", "validate_result")
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
    return g
