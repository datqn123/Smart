"""Subgraph: classify entity → generate draft → persist to Spring."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.graph.deps import GraphDeps
from app.graph.nodes.catalog_draft import (
    make_classify_catalog_entity_node,
    make_generate_catalog_draft_node,
    make_persist_catalog_draft_node,
)
from app.graph.state import AgentState


def build_catalog_draft_subgraph(deps: GraphDeps):
    g = StateGraph(AgentState)
    g.add_node("classify_catalog_entity", make_classify_catalog_entity_node(deps))
    g.add_node("generate_catalog_draft", make_generate_catalog_draft_node(deps))
    g.add_node("persist_catalog_draft", make_persist_catalog_draft_node(deps))
    g.add_edge(START, "classify_catalog_entity")
    g.add_edge("classify_catalog_entity", "generate_catalog_draft")
    g.add_edge("generate_catalog_draft", "persist_catalog_draft")
    g.add_edge("persist_catalog_draft", END)
    return g
