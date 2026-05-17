"""General chat branch."""

from __future__ import annotations

import logging

from langchain_core.messages import AIMessage

from app.graph.agent_trace import emit_agent_trace
from app.graph.deps import GraphDeps
from app.graph.display_format import format_display_for_chat_ui
from app.graph.state import AgentState
from app.prompts.load import load_agent_prompt

logger = logging.getLogger(__name__)

_CHAT_SYSTEM = load_agent_prompt("chat_normal")


def make_chat_normal_node(deps: GraphDeps):
    def chat_normal(state: AgentState) -> dict:
        logger.info("node=chat_normal action=start")
        reg = deps.llm_registry
        if reg is None:
            emit_agent_trace(
                logger,
                deps.settings,
                agent="chat_normal",
                phase="Stub — không có LLM registry",
                detail="final_answer cố định",
            )
            stub = "[chat] stub: no LLM registry"
            return {"final_answer": stub, "messages": [AIMessage(content=stub)]}
        msgs = state.get("messages") or []
        parts: list[str] = []
        for m in msgs[-20:]:
            c = getattr(m, "content", "")
            parts.append(str(c))
        text = "\n".join(parts)[-4000:]
        ans = reg.get("chat").invoke_text(text, system=_CHAT_SYSTEM)
        ans = format_display_for_chat_ui(ans)
        preview = ans if len(ans) <= 1200 else ans[:1200] + "…"
        emit_agent_trace(
            logger,
            deps.settings,
            agent="chat_normal",
            phase="Trả lời chat chung (LLM)",
            detail=f"văn_bản_phản_hồi:\n{preview}",
        )
        return {"final_answer": ans, "messages": [AIMessage(content=ans)]}

    return chat_normal
