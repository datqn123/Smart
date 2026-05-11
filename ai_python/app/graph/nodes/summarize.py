"""Summarize SQL subgraph output for main graph."""

from __future__ import annotations

import logging

from app.graph.agent_trace import emit_agent_trace
from app.graph.deps import GraphDeps
from app.graph.state import AgentState

logger = logging.getLogger(__name__)


def make_summarize_answer_node(deps: GraphDeps):
    def summarize_answer(state: AgentState) -> dict:
        logger.info("node=summarize_answer action=start")
        err = state.get("error_payload")
        if err:
            parts = [f"mã lỗi: {err.get('error')}"]
            if err.get("attempts") is not None:
                parts.append(f"attempts={err['attempts']}")
            msg = f"Xin lỗi, không hoàn tất truy vấn ({', '.join(parts)})."
            emit_agent_trace(
                logger,
                deps.settings,
                agent="summarize",
                phase="Không tóm tắt — lỗi pipeline SQL",
                detail=str(err),
            )
            return {"final_answer": msg}
        qr = state.get("query_result")
        empty = state.get("result_empty") or (
            isinstance(qr, dict) and not (qr.get("rows") or [])
        )
        if empty:
            emit_agent_trace(
                logger,
                deps.settings,
                agent="summarize",
                phase="Kết quả truy vấn rỗng",
                detail="Không có rows — trả lời cố định cho user.",
            )
            return {
                "final_answer": "Không có dữ liệu phù hợp với câu hỏi của bạn."
            }
        reg = deps.llm_registry
        if reg is None:
            stub_ans = str(qr)[:8000]
            emit_agent_trace(
                logger,
                deps.settings,
                agent="summarize",
                phase="Tóm tắt stub (không gọi LLM)",
                detail=stub_ans if len(stub_ans) <= 1500 else stub_ans[:1500] + "…",
            )
            return {"final_answer": stub_ans}
        messages_tail = state.get("messages") or []
        user_q = ""
        for m in reversed(messages_tail):
            c = getattr(m, "content", "")
            if c:
                user_q = str(c)
                break
        prompt = (
            f"Câu hỏi: {user_q}\n\n"
            f"Kết quả truy vấn (đừng bịa số ngoài rows):\n{str(qr)[:6000]}\n\n"
            "Tóm tắt ngắn gọn bằng tiếng Việt (vi-VN). Ưu tiên số liệu cụ thể từ kết quả; "
            "không suy diễn ngoài dữ liệu."
        )
        ans = reg.get("summarize").invoke_text(
            prompt,
            system="Bạn là trợ lý ERP. Tóm tắt số liệu chính xác, không bịa, locale vi-VN.",
        )
        preview = ans if len(ans) <= 1200 else ans[:1200] + "…"
        emit_agent_trace(
            logger,
            deps.settings,
            agent="summarize",
            phase="Tóm tắt kết quả SQL (LLM)",
            detail=f"văn_bản_phản_hồi:\n{preview}",
        )
        return {"final_answer": ans}

    return summarize_answer
