"""General chat branch."""

from __future__ import annotations

import logging

from app.graph.deps import GraphDeps
from app.graph.state import AgentState

logger = logging.getLogger(__name__)


def make_chat_normal_node(deps: GraphDeps):
    def chat_normal(state: AgentState) -> dict:
        logger.info("node=chat_normal action=start")
        reg = deps.llm_registry
        if reg is None:
            return {"final_answer": "[chat] stub: no LLM registry"}
        msgs = state.get("messages") or []
        parts: list[str] = []
        for m in msgs[-20:]:
            c = getattr(m, "content", "")
            parts.append(str(c))
        text = "\n".join(parts)[-4000:]
        ans = reg.get("chat").invoke_text(
            text,
            system=(
                "Bạn là trợ lý ERP. Trong nhánh này KHÔNG được tiết lộ schema cơ sở dữ liệu nội bộ "
                "và KHÔNG truy cập DB. Trả lời gọn, tiếng Việt nếu user dùng tiếng Việt."
            ),
        )
        return {"final_answer": ans}

    return chat_normal
