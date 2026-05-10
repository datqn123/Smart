"""Main LangGraph: intent → chat | SQL subgraph → summarize."""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from app.graph.checkpointing import build_checkpointer
from app.graph.deps import GraphDeps
from app.graph.nodes.chat_normal import make_chat_normal_node
from app.graph.nodes.intent import make_intent_node, route_after_intent
from app.graph.nodes.summarize import make_summarize_answer_node
from app.graph.sql_subgraph import build_sql_subgraph
from app.graph.state import AgentState


def build_main_graph(deps: GraphDeps):
    g = StateGraph(AgentState)
    sql_inner = build_sql_subgraph(deps)
    g.add_node("classify_intent", make_intent_node(deps))
    g.add_node("chat_normal", make_chat_normal_node(deps))
    g.add_node("sql_branch", sql_inner.compile())
    g.add_node("summarize_answer", make_summarize_answer_node(deps))

    g.add_edge(START, "classify_intent")
    g.add_conditional_edges(
        "classify_intent",
        route_after_intent,
        {
            "chat_normal": "chat_normal",
            "sql_branch": "sql_branch",
        },
    )
    g.add_edge("chat_normal", END)
    g.add_edge("sql_branch", "summarize_answer")
    g.add_edge("summarize_answer", END)
    return g


def compile_agent_graph(
    deps: GraphDeps,
    *,
    use_checkpointer: bool = True,
) -> Any:
    """Compile main graph; attach Memory/Sqlite checkpointer when enabled."""
    main = build_main_graph(deps)
    if not use_checkpointer:
        return main.compile()
    ck = build_checkpointer(deps.settings)
    return main.compile(checkpointer=ck)
