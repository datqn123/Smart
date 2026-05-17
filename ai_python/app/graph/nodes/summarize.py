"""Summarize SQL subgraph output for main graph."""

from __future__ import annotations

import logging

from langchain_core.messages import AIMessage

from app.graph.agent_trace import emit_agent_trace
from app.graph.datetime_display import localize_query_result_for_display
from app.graph.deps import GraphDeps
from app.graph.display_format import format_display_for_chat_ui
from app.graph.message_utils import format_dialog_tail_for_sql, latest_human_question
from app.graph.state import AgentState
from app.prompts.load import load_agent_prompt

logger = logging.getLogger(__name__)

_SUMMARIZE_SYSTEM = load_agent_prompt("summarize")


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
            return {"final_answer": msg, "messages": [AIMessage(content=msg)]}
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
            empty_msg = "Không có dữ liệu phù hợp với câu hỏi của bạn."
            return {
                "final_answer": empty_msg,
                "messages": [AIMessage(content=empty_msg)],
            }
        reg = deps.llm_registry
        if reg is None:
            qr_stub = localize_query_result_for_display(qr, deps.settings.ai_display_timezone)
            stub_ans = str(qr_stub)[:8000]
            emit_agent_trace(
                logger,
                deps.settings,
                agent="summarize",
                phase="Tóm tắt stub (không gọi LLM)",
                detail=stub_ans if len(stub_ans) <= 1500 else stub_ans[:1500] + "…",
            )
            return {
                "final_answer": stub_ans,
                "messages": [AIMessage(content=stub_ans)],
            }
        user_q = latest_human_question(state.get("messages"))
        dialog_tail = format_dialog_tail_for_sql(
            state.get("messages"),
            max_messages=int(deps.settings.sql_dialog_tail_max_messages),
            max_chars=int(deps.settings.sql_dialog_tail_max_chars),
        )
        dialog_block = (
            f"Recent conversation (resolve pronouns like đơn đó / tháng đó; "
            f"do not invent numbers not in rows or not stated here):\n{dialog_tail}\n\n"
            if dialog_tail
            else ""
        )
        qr_prompt = localize_query_result_for_display(qr, deps.settings.ai_display_timezone)
        prompt = (
            f"{dialog_block}"
            f"Câu hỏi hiện tại (ưu tiên trả lời đúng phần này; bám rows cho số liệu): {user_q}\n\n"
            f"Kết quả truy vấn (đừng bịa số ngoài rows):\n{str(qr_prompt)[:6000]}\n\n"
            "Tóm tắt ngắn gọn bằng tiếng Việt (vi-VN). Ưu tiên số liệu cụ thể từ kết quả; "
            "không suy diễn ngoài dữ liệu.\n\n"
            "Trình bày cho khung chat: dùng Markdown nhẹ (xuống dòng thật, mỗi mục một dòng; "
            "danh sách bằng `- ` ở đầu dòng cho từng đơn / từng dòng kết quả quan trọng; "
            "có thể thêm `##` tiêu đề phụ rất ngắn nếu nhiều nhóm). "
            "Không bọc toàn bộ nội dung trong fence ```."
        )
        tz_note = (
            " Chuỗi thời gian trong block kết quả đã được chuyển sang giờ địa phương (múi giờ cấu hình) "
            "khi giá trị gốc có timezone (UTC/Z/offset); dùng đúng các mốc đó khi trả lời giờ/ngày."
            if deps.settings.ai_display_timezone
            else ""
        )
        ans = reg.get("summarize").invoke_text(
            prompt,
            system=_SUMMARIZE_SYSTEM + tz_note,
        )
        ans = format_display_for_chat_ui(ans)
        preview = ans if len(ans) <= 1200 else ans[:1200] + "…"
        emit_agent_trace(
            logger,
            deps.settings,
            agent="summarize",
            phase="Tóm tắt kết quả SQL (LLM)",
            detail=f"văn_bản_phản_hồi:\n{preview}",
        )
        return {"final_answer": ans, "messages": [AIMessage(content=ans)]}

    return summarize_answer
