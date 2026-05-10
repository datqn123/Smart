"""SQL subgraph (TASK-LG-08 … LG-11)."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.graph.deps import GraphDeps
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
from app.graph.state import AgentState


def build_sql_subgraph(deps: GraphDeps):
    g = StateGraph(AgentState)
    g.add_node("gen_sql", make_gen_sql_node(deps))
    g.add_node("sql_review", make_sql_review_node(deps))
    g.add_node("validate_sql", make_validate_sql_node(deps))
    g.add_node("execute_sql", make_execute_sql_node(deps))
    g.add_node("validate_result", make_validate_result_node(deps))
    g.add_node("fail_max_attempts", make_fail_max_attempts_node(deps))

    g.add_edge(START, "gen_sql")
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
            "gen_sql": "gen_sql",
            "fail_max_attempts": "fail_max_attempts",
        },
    )
    g.add_edge("fail_max_attempts", END)
    return g
