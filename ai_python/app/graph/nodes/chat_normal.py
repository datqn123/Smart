"""General chat branch."""

from __future__ import annotations

import logging

from langchain_core.messages import AIMessage

from app.graph.agent_trace import emit_agent_trace
from app.graph.answer_quality import finalize_answer
from app.graph.deps import GraphDeps
from app.graph.display_format import format_display_for_chat_ui
from app.graph.message_utils import build_chat_context_text, latest_human_question
from app.graph.progress import emit_progress
from app.graph.state import AgentState
from app.prompts.load import load_agent_prompt

from collections.abc import Generator

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
            return {**emit_progress(state, "chat_normal"), "final_answer": stub, "messages": [AIMessage(content=stub)]}
        text = build_chat_context_text(
            state.get("messages"),
            state.get("conversation_summary"),
            tail_messages=20,
            max_chars=4000,
        )
        
        # Lấy stream writer từ LangGraph để stream trực tiếp ra custom events
        writer = None
        try:
            from langgraph.config import get_stream_writer
            writer = get_stream_writer()
        except Exception:
            writer = None
            
        accumulated_ans = ""
        stream = reg.get("chat").stream_text(text, system=_CHAT_SYSTEM)
        for chunk in stream:
            accumulated_ans += chunk
            if writer is not None:
                writer({"final_answer": accumulated_ans})

            
        # Áp dụng finalize_answer ở cuối luồng để lưu trữ và cắt ngắn nếu cần (bypass quality enrichments)
        final_formatted = format_display_for_chat_ui(accumulated_ans)
        ans = finalize_answer(
            final_formatted,
            deps=deps,
            node_name="chat_normal",
            scenario="chat",
            user_question=latest_human_question(state.get("messages")),
            skip_quality=True,
        )
        preview = ans if len(ans) <= 1200 else ans[:1200] + "…"
        emit_agent_trace(
            logger,
            deps.settings,
            agent="chat_normal",
            phase="Trả lời chat chung (LLM)",
            detail=f"văn_bản_phản_hồi:\n{preview}",
        )
        return {**emit_progress(state, "chat_normal"), "final_answer": ans, "messages": [AIMessage(content=ans)]}

    return chat_normal


