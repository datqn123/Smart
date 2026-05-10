"""Intent routing node."""

from __future__ import annotations

import logging

from app.graph.deps import GraphDeps
from app.graph.registry import normalize_intent
from app.graph.state import AgentState
from app.llm.schemas import IntentOutput

logger = logging.getLogger(__name__)


def make_intent_node(deps: GraphDeps):
    def intent(state: AgentState) -> dict:
        logger.info("node=intent action=start")
        reg = deps.llm_registry
        if reg is None:
            return {"intent": "general_chat"}
        messages = state.get("messages") or []
        client = reg.get("intent")
        try:
            out = client.structured_predict(messages, IntentOutput)
            raw = out.intent
        except Exception:
            logger.warning("intent structured_predict failed; routing to general_chat", exc_info=True)
            return {"intent": "general_chat"}
        return {"intent": normalize_intent(raw)}

    return intent


def route_after_intent(state: AgentState) -> str:
    intent = state.get("intent") or "general_chat"
    if intent == "system_data_query":
        return "sql_branch"
    return "chat_normal"
