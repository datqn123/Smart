"""Inventory document draft subgraph (stock receipt v1)."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.graph.deps import GraphDeps
from app.graph.nodes.inventory_draft import (
    make_classify_inventory_doc_node,
    make_generate_inventory_draft_node,
    make_persist_inventory_draft_node,
)
from app.graph.state import AgentState


def build_inventory_draft_subgraph(deps: GraphDeps):
    g = StateGraph(AgentState)
    g.add_node("classify_inventory_doc", make_classify_inventory_doc_node(deps))
    g.add_node("generate_inventory_draft", make_generate_inventory_draft_node(deps))
    g.add_node("persist_inventory_draft", make_persist_inventory_draft_node(deps))
    g.add_edge(START, "classify_inventory_doc")
    g.add_edge("classify_inventory_doc", "generate_inventory_draft")
    g.add_edge("generate_inventory_draft", "persist_inventory_draft")
    g.add_edge("persist_inventory_draft", END)
    return g
