"""General chat branch."""

from __future__ import annotations

import logging

from app.graph.agent_trace import emit_agent_trace
from app.graph.deps import GraphDeps
from app.graph.state import AgentState

logger = logging.getLogger(__name__)


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
                "Bạn là trợ lý ERP. Nhánh chat chung này không kèm kết quả truy vấn SQL từ backend "
                "(chỉ có ngữ cảnh hội thoại), nên không khẳng định số tồn kho/doanh thu cụ thể từ CSDL "
                "và không nói toàn bộ hệ thống 'không có quyền đọc DB' — quyền đọc nằm ở luồng câu hỏi "
                "báo cáo/dữ liệu. Nếu user cần số thực tế, gợi ý họ đặt một câu hỏi báo cáo rõ (vd. "
                "tồn kho SKU X, doanh thu hôm nay). Không tiết lộ schema/tên bảng nội bộ. "
                "Trả lời gọn, tiếng Việt nếu user dùng tiếng Việt."
            ),
        )
        preview = ans if len(ans) <= 1200 else ans[:1200] + "…"
        emit_agent_trace(
            logger,
            deps.settings,
            agent="chat_normal",
            phase="Trả lời chat chung (LLM)",
            detail=f"văn_bản_phản_hồi:\n{preview}",
        )
        return {"final_answer": ans}

    return chat_normal
