"""Main LangGraph: intent → chat | chart (idea→chart→review) | catalog/inventory drafts."""

from __future__ import annotations

import logging
from typing import Any

from langgraph.graph import END, START, StateGraph

from app.graph.checkpointing import build_checkpointer
from app.graph.deps import GraphDeps
from app.graph.nodes.chart_report import (
    make_agent_chart_node,
    make_agent_idea_node,
    make_agent_review_node,
    make_chart_fail_message_node,
)
from app.graph.nodes.chat_normal import make_chat_normal_node
from app.graph.nodes.context_compact import make_context_compact_node
from app.graph.nodes.domain_guard import make_domain_guard_node, route_after_domain_guard
from app.graph.nodes.planner import make_agent_planner_node
from app.graph.nodes.intent import make_intent_node, route_after_intent
from app.graph.catalog_draft_subgraph import build_catalog_draft_subgraph
from app.graph.inventory_draft_subgraph import build_inventory_draft_subgraph
from app.graph.progress import wrap_node_with_stream_progress as wrap
from app.graph.state import AgentState

logger = logging.getLogger(__name__)


def build_main_graph(deps: GraphDeps):
    g = StateGraph(AgentState)
    catalog_inner = build_catalog_draft_subgraph(deps)
    inventory_inner = build_inventory_draft_subgraph(deps)
    g.add_node("domain_guard", wrap("domain_guard", make_domain_guard_node(deps)))
    g.add_node("context_compact", wrap("context_compact", make_context_compact_node(deps)))
    g.add_node("agent_planner", wrap("agent_planner", make_agent_planner_node(deps)))
    g.add_node("classify_intent", wrap("classify_intent", make_intent_node(deps)))
    g.add_node("chat_normal", wrap("chat_normal", make_chat_normal_node(deps)))
    g.add_node("catalog_draft_branch", catalog_inner.compile())
    g.add_node("inventory_draft_branch", inventory_inner.compile())
    g.add_node("agent_idea", wrap("agent_idea", make_agent_idea_node(deps)))
    g.add_node("agent_chart", wrap("agent_chart", make_agent_chart_node(deps)))
    g.add_node("agent_review", wrap("agent_review", make_agent_review_node(deps)))
    g.add_node("chart_fail_message", wrap("chart_fail_message", make_chart_fail_message_node(deps)))

    g.add_edge(START, "domain_guard")
    g.add_conditional_edges(
        "domain_guard",
        route_after_domain_guard,
        {
            "continue": "context_compact",
            "stop": END,
        },
    )
    g.add_edge("context_compact", "agent_planner")
    g.add_edge("agent_planner", "classify_intent")
    g.add_conditional_edges(
        "classify_intent",
        route_after_intent,
        {
            "chat_normal": "chat_normal",
            "agent_idea": "agent_idea",
            "catalog_draft_branch": "catalog_draft_branch",
            "inventory_draft_branch": "inventory_draft_branch",
        },
    )
    g.add_edge("chat_normal", END)
    g.add_edge("catalog_draft_branch", END)
    g.add_edge("inventory_draft_branch", END)
    g.add_edge("agent_idea", "chat_normal")
    g.add_edge("agent_review", END)
    g.add_edge("chart_fail_message", END)
    logger.debug("graph_compile nodes=%s", list(g.nodes.keys()))
    return g


def compile_agent_graph(
    deps: GraphDeps,
    *,
    use_checkpointer: bool = True,
) -> Any:
    """Compile main graph; attach Memory/Sqlite checkpointer when enabled."""
    main = build_main_graph(deps)
    if not use_checkpointer:
        compiled = main.compile()
        logger.debug("graph_compiled checkpointer=%s", use_checkpointer)
        return compiled
    ck = build_checkpointer(deps.settings)
    compiled = main.compile(checkpointer=ck)
    logger.debug("graph_compiled checkpointer=%s", use_checkpointer)
    return compiled
