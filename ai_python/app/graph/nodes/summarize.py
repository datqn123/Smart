from __future__ import annotations

import logging
from collections.abc import Generator


from langchain_core.messages import AIMessage

from app.graph.agent_trace import emit_agent_trace
from app.graph.answer_fallbacks import SQL_EMPTY_VI
from app.graph.answer_quality import finalize_answer
from app.graph.datetime_display import localize_query_result_for_display
from app.graph.deps import GraphDeps
from app.graph.display_format import format_display_for_chat_ui
from app.graph.message_utils import (
    effective_user_question,
    format_dialog_tail_for_sql,
)
from app.graph.progress import emit_progress
from app.graph.state import AgentState
from app.prompts.load import load_agent_prompt


def scope_effective_question(user_q: str, business_scope: dict | None) -> str:
    if not isinstance(business_scope, dict):
        return user_q
    rewritten = business_scope.get("effective_question") or business_scope.get("normalized_question")
    return str(rewritten) if rewritten else user_q


def scalar_label_from_scope(business_scope: dict | None) -> str | None:
    if not isinstance(business_scope, dict):
        return None
    return business_scope.get("scalar_label")


def is_raw_sql_alias(key: str) -> bool:
    return any(
        key.lower().startswith(p)
        for p in ("sum_", "total_", "count_", "avg_", "min_", "max_")
    ) or key.lower() in ("total", "count", "sum", "value", "amount")


def is_followup_detail_reconciled(business_scope: dict | None) -> bool:
    if not isinstance(business_scope, dict):
        return False
    return bool(business_scope.get("reconciled"))

logger = logging.getLogger(__name__)

_SUMMARIZE_SYSTEM = load_agent_prompt("summarize")
_SUMMARIZE_EMPTY_SYSTEM = load_agent_prompt("summarize_empty")


def _format_vi_integer(val: float | int) -> str:
    n = int(round(float(val)))
    return f"{n:,}".replace(",", ".")


_COLUMN_LABELS_VI: dict[str, str] = {
    "total_value": "tổng giá trị",
    "total_amount": "tổng số tiền",
    "total_inventory_value": "tổng giá trị tồn kho",
    "total_capital_value": "tổng giá trị vốn",
    "sum": "tổng",
    "count": "số lượng",
    "revenue": "doanh thu",
    "quantity": "số lượng",
    "amount": "số tiền",
    "total_distinct_products_received": "tổng số mặt hàng đã nhập (không trùng)",
}

_COL_DISPLAY_VI: dict[str, str] = {
    "receipt_code": "Mã phiếu",
    "order_code": "Mã đơn",
    "sku_code": "Mã hàng",
    "total_amount": "Tổng giá trị",
    "quantity": "Số lượng",
    "name": "Tên",
}


def _scalar_row_label(column_key: str, user_q: str, business_scope: dict | None = None) -> str:
    qlow = (user_q or "").lower()
    key_norm = column_key.lower().strip().replace(" ", "_")
    scoped = scalar_label_from_scope(business_scope)
    if scoped:
        if is_raw_sql_alias(key_norm):
            return scoped
        if any(k in qlow for k in ("thu vào", "thu vao", "tổng thu", "tong thu", "thu tiền", "thu tien")):
            return scoped

    if "giá trị vốn" in qlow or ("giá trị" in qlow and "vốn" in qlow):
        if "phiếu nhập" in qlow or "nhập kho" in qlow:
            return "tổng giá trị vốn từ các phiếu nhập đã duyệt"
        return "tổng giá trị vốn"
    if "giá trị" in qlow and "tồn" in qlow:
        return "tổng giá trị tồn kho"
    if "doanh thu" in qlow:
        return "tổng doanh thu"
    if "thu vào" in qlow or "thu vao" in qlow or "tổng thu" in qlow or "tong thu" in qlow:
        return scoped or "tổng tiền thu"
    if "công nợ" in qlow:
        return "tổng công nợ"
    if is_raw_sql_alias(key_norm):
        return scoped or "kết quả tổng hợp"

    mapped = _COLUMN_LABELS_VI.get(key_norm)
    if mapped:
        return mapped

    if key_norm and all(ord(c) < 128 for c in key_norm):
        word_map = {
            "total": "tổng",
            "value": "giá trị",
            "amount": "số tiền",
            "count": "số lượng",
            "inventory": "tồn kho",
            "capital": "vốn",
            "revenue": "doanh thu",
        }
        return " ".join(word_map.get(p, p) for p in key_norm.split("_") if p)

    return column_key.replace("_", " ")


def _format_col_label(column_key: str) -> str:
    key_norm = column_key.lower().strip().replace(" ", "_")
    return _COL_DISPLAY_VI.get(key_norm, _scalar_row_label(column_key, ""))


def _looks_like_money(label: str, column_key: str) -> bool:
    blob = f"{label} {column_key}".lower()
    return any(
        w in blob
        for w in (
            "giá trị",
            "tiền",
            "doanh thu",
            "công nợ",
            "vốn",
            "amount",
            "revenue",
            "price",
            "value",
            "capital",
        )
    )


def _format_money_amount(num: float | int, *, is_money: bool) -> str:
    text = f"**{_format_vi_integer(num)}**"
    if is_money:
        text += "đ"
    return text


def _format_cell_value(val: object) -> str:
    if isinstance(val, bool):
        return str(val)
    if isinstance(val, (int, float)):
        if float(val) == int(round(float(val))):
            return _format_vi_integer(val)
        return str(val)
    return str(val)


def _is_numeric_column(key: str, val: object) -> bool:
    kl = key.lower()
    if isinstance(val, (int, float)) and not isinstance(val, bool):
        return True
    return any(h in kl for h in ("amount", "quantity", "total", "value", "count", "price", "qty"))


def _is_identifier_column(key: str) -> bool:
    kl = key.lower()
    return kl in ("id", "name", "sku_code", "receipt_code", "order_code", "sku") or kl.endswith(
        ("_code", "_id", "_name", "_number")
    )


def _try_single_row_highlight_summary(qr: dict | None, user_q: str) -> str | None:
    """One row, multiple columns (TOP 1 / chi tiết một phiếu) — list facts from rows without LLM."""
    if not isinstance(qr, dict):
        return None
    rows = qr.get("rows")
    if not isinstance(rows, list) or len(rows) != 1:
        return None
    row = rows[0]
    if not isinstance(row, dict) or len(row) < 2:
        return None

    id_cols: list[tuple[str, str]] = []
    num_cols: list[tuple[str, str]] = []
    other_cols: list[tuple[str, str]] = []
    for key, val in row.items():
        if val is None:
            continue
        disp = _format_cell_value(val)
        if _is_numeric_column(str(key), val):
            num_cols.append((str(key), disp))
        elif _is_identifier_column(str(key)):
            id_cols.append((str(key), disp))
        else:
            other_cols.append((str(key), disp))

    qlow = (user_q or "").lower()
    rank_word = None
    if any(w in qlow for w in ("cao nhất", "lớn nhất", "max")):
        rank_word = "cao nhất"
    elif any(w in qlow for w in ("thấp nhất", "nhỏ nhất", "min")):
        rank_word = "thấp nhất"

    subject = "kết quả"
    if "phiếu nhập" in qlow or "nhập kho" in qlow:
        subject = "phiếu nhập kho"
    elif "phiếu xuất" in qlow or "xuất kho" in qlow:
        subject = "phiếu xuất kho"
    elif "đơn hàng" in qlow or "don hang" in qlow:
        subject = "đơn hàng"

    lines: list[str] = []
    if id_cols and num_cols and rank_word:
        code_v = id_cols[0][1]
        num_k, num_v = num_cols[0]
        num_label = _format_col_label(num_k)
        lines.append(
            f"{subject.capitalize()} có {num_label.lower()} {rank_word} là "
            f"**{code_v}**, với {num_label.lower()} **{num_v}**."
        )
    elif id_cols and num_cols:
        code_v = id_cols[0][1]
        num_k, num_v = num_cols[0]
        num_label = _format_col_label(num_k)
        lines.append(f"**{code_v}** — {num_label.lower()} **{num_v}**.")

    lines.append("")
    lines.append("Chi tiết:")
    for key, val in row.items():
        if val is None:
            continue
        lines.append(f"- {_format_col_label(str(key))}: **{_format_cell_value(val)}**")
    return "\n".join(lines)


def _try_single_scalar_summary(qr: dict | None, user_q: str, business_scope: dict | None = None) -> str | None:
    """One row, one column (SUM/COUNT aggregate) — answer without LLM hallucination."""
    if not isinstance(qr, dict):
        return None
    rows = qr.get("rows")
    if not isinstance(rows, list) or len(rows) != 1:
        return None
    row = rows[0]
    if not isinstance(row, dict) or len(row) != 1:
        return None
    (key, val), = row.items()
    label = _scalar_row_label(str(key), user_q, business_scope=business_scope)
    if val is None:
        return (
            f"Hiện chưa tính được {label}. "
            "Thường do chưa có dòng dữ liệu khớp điều kiện hoặc chưa có giá vốn "
            "cho đơn vị tính cơ sở của sản phẩm."
        )
    if isinstance(val, bool):
        return None
    num: float | None = None
    if isinstance(val, (int, float)):
        num = float(val)
    elif isinstance(val, str):
        try:
            num = float(val.replace(",", "").strip())
        except ValueError:
            return f"{label.capitalize()}: {val}."
    if num is not None:
        qlow = (user_q or "").lower()
        is_money = _looks_like_money(label, str(key))
        amount = _format_money_amount(num, is_money=is_money)
        head = f"{label.capitalize()} là {amount}."
        if "giá trị" in qlow and "tồn" in qlow:
            tail = (
                "\n\nCon số này là tổng số lượng tồn nhân với giá vốn đơn vị hiện tại.\n\n"
                "Bạn có thể hỏi thêm, ví dụ:\n"
                "- Tồn của một mặt hàng cụ thể ở đâu?\n"
                "- Mặt hàng nào đang có giá trị tồn cao nhất?\n"
                "- Có bao nhiêu mặt hàng sắp hết hàng?"
            )
        else:
            tail = (
                "\n\nNếu bạn muốn xem chi tiết theo từng mặt hàng, phiếu hoặc khách hàng, "
                "hãy nêu rõ tên hoặc mã cụ thể nhé."
            )
        return head + tail
    return None


def _build_sql_empty_message(
    deps: GraphDeps,
    state: AgentState,
    user_q: str,
) -> str:
    empty_warning = state.get("empty_warning") or ""

    if empty_warning:
        return (
            "Không có dữ liệu phù hợp với điều kiện bạn yêu cầu.\n\n"
            f"⚠️ {empty_warning}\n\n"
            "Bạn muốn thử lại với thông tin khác không?"
        )

    reg = deps.llm_registry
    if reg is None:
        return SQL_EMPTY_VI
    dialog_tail = format_dialog_tail_for_sql(
        state.get("messages"),
        max_messages=int(deps.settings.sql_dialog_tail_max_messages),
        max_chars=int(deps.settings.sql_dialog_tail_max_chars),
        summary=state.get("conversation_summary"),
    )
    system = (
        _SUMMARIZE_EMPTY_SYSTEM.replace("{user_question}", user_q or "(không rõ)")
        .replace("{dialog_tail}", dialog_tail or "(không có)")
    )
    try:
        text = reg.get("summarize").invoke_text(
            "Write the user-facing reply.",
            system=system,
        )
        return format_display_for_chat_ui(text)
    except Exception:
        logger.warning("summarize_empty LLM failed", exc_info=True)
        return SQL_EMPTY_VI


def make_summarize_answer_node(deps: GraphDeps):
    def summarize_answer(state: AgentState) -> dict:
        logger.info("node=summarize_answer action=start")
        progress_dict = emit_progress(state, "summarize_answer")
        business_scope = state.get("business_scope") if isinstance(state.get("business_scope"), dict) else None
        err = state.get("error_payload")
        if err:
            parts = [f"mã lỗi: {err.get('error')}"]
            if err.get("attempts") is not None:
                parts.append(f"attempts={err['attempts']}")
            msg = f"Xin lỗi, chưa tra cứu được dữ liệu ({', '.join(parts)})."
            user_q = scope_effective_question(
                effective_user_question(state.get("messages"), state.get("normalized_user_question")),
                business_scope,
            )
            msg = finalize_answer(
                msg,
                deps=deps,
                node_name="summarize",
                scenario="sql_error",
                user_question=user_q,
                has_query_result=False,
                fallback_template_id="sql_error_vi",
            )
            emit_agent_trace(
                logger,
                deps.settings,
                agent="summarize",
                phase="Không tóm tắt — lỗi pipeline SQL",
                detail=str(err),
            )
            return {
                **progress_dict,
                "final_answer": msg,
                "messages": [AIMessage(content=msg)],
            }
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
            user_q = scope_effective_question(
                effective_user_question(state.get("messages"), state.get("normalized_user_question")),
                business_scope,
            )
            empty_msg = _build_sql_empty_message(deps, state, user_q)
            empty_msg = finalize_answer(
                empty_msg,
                deps=deps,
                node_name="summarize",
                scenario="sql_empty",
                user_question=user_q,
                has_query_result=False,
                fallback_template_id="sql_empty_vi",
            )
            return {
                **progress_dict,
                "final_answer": empty_msg,
                "messages": [AIMessage(content=empty_msg)],
            }
        table_sse = state.get("query_table_sse")
        
        # Lấy stream writer từ LangGraph để stream trực tiếp ra custom events
        writer = None
        try:
            from langgraph.config import get_stream_writer
            writer = get_stream_writer()
        except Exception:
            writer = None

        if isinstance(table_sse, dict) and table_sse:
            row_count = table_sse.get("rowCount", 0)
            truncated = bool(table_sse.get("truncated"))
            trunc_note = (
                f" (hiển thị tối đa {table_sse.get('maxDisplayRows', 200)} dòng)"
                if truncated
                else ""
            )
            user_q = scope_effective_question(
                effective_user_question(state.get("messages"), state.get("normalized_user_question")),
                business_scope,
            )
            reg = deps.llm_registry
            if reg is None:
                intro = (
                    f"Đã tìm thấy {row_count} dòng phù hợp{trunc_note}. "
                    "Xem bảng chi tiết bên dưới."
                )
            else:
                dialog_tail = format_dialog_tail_for_sql(
                    state.get("messages"),
                    max_messages=int(deps.settings.sql_dialog_tail_max_messages),
                    max_chars=int(deps.settings.sql_dialog_tail_max_chars),
                    summary=state.get("conversation_summary"),
                )
                dialog_block = (
                    f"Recent conversation:\n{dialog_tail}\n\n" if dialog_tail else ""
                )
                prompt = (
                    f"{dialog_block}"
                    f"Câu hỏi: {user_q}\n"
                    f"Số dòng kết quả: {row_count}{trunc_note}.\n"
                    "Bảng chi tiết đã hiển thị riêng bên dưới UI — "
                    "chỉ viết 1–2 câu tiếng Việt giới thiệu ngắn (không liệt kê từng dòng, không bullet dài)."
                )
                accumulated_ans = ""
                stream = reg.get("summarize").stream_text(
                    prompt,
                    system=_SUMMARIZE_SYSTEM
                    + "\n\nKhi có bảng UI: tối đa 2 câu, không markdown list dài.",
                )
                for chunk in stream:
                    accumulated_ans += chunk
                    if writer is not None:
                        writer({"final_answer": accumulated_ans})
                intro = format_display_for_chat_ui(accumulated_ans)
            intro = finalize_answer(
                intro,
                deps=deps,
                node_name="summarize",
                scenario="sql_summary",
                user_question=user_q,
                has_query_result=True,
                skip_quality=True,
            )
            emit_agent_trace(
                logger,
                deps.settings,
                agent="summarize",
                phase="Tóm tắt ngắn (có bảng UI)",
                detail=intro[:800],
            )
            return {**progress_dict, "final_answer": intro, "messages": [AIMessage(content=intro)]}
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
                **progress_dict,
                "final_answer": stub_ans,
                "messages": [AIMessage(content=stub_ans)],
            }
        user_q = scope_effective_question(
            effective_user_question(state.get("messages"), state.get("normalized_user_question")),
            business_scope,
        )
        qr_dict = qr if isinstance(qr, dict) else None
        deterministic_ans = _try_single_scalar_summary(qr_dict, user_q, business_scope=business_scope)
        if not deterministic_ans:
            # Detail follow-ups after scalar totals must pass reconcile check first; avoid
            # shortcutting to a single-row highlight before SQL context is corrected.
            if is_followup_detail_reconciled(business_scope):
                deterministic_ans = _try_single_row_highlight_summary(qr_dict, user_q)
        if deterministic_ans:
            deterministic_ans = format_display_for_chat_ui(deterministic_ans)
            deterministic_ans = finalize_answer(
                deterministic_ans,
                deps=deps,
                node_name="summarize",
                scenario="sql_summary",
                user_question=user_q,
                has_query_result=True,
                query_result=qr_dict,
                enrich_allowed=False,
            )
            phase = "Tóm tắt deterministic (không gọi LLM)"
            emit_agent_trace(
                logger,
                deps.settings,
                agent="summarize",
                phase=phase,
                detail=deterministic_ans[:800],
            )
            return {
                **progress_dict,
                "final_answer": deterministic_ans,
                "messages": [AIMessage(content=deterministic_ans)],
            }
        dialog_tail = format_dialog_tail_for_sql(
            state.get("messages"),
            max_messages=int(deps.settings.sql_dialog_tail_max_messages),
            max_chars=int(deps.settings.sql_dialog_tail_max_chars),
            summary=state.get("conversation_summary"),
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
            f"Dữ liệu trả về (chỉ dùng số trong block này, đừng bịa thêm):\n{str(qr_prompt)[:6000]}\n\n"
            "Tóm tắt ngắn gọn bằng tiếng Việt (vi-VN), giọng gần gũi như đồng nghiệp. "
            "Ưu tiên số liệu cụ thể; không suy diễn ngoài dữ liệu. "
            "Nếu kết quả chỉ có một con số tổng: **không** bịa tên sản phẩm / phiếu / khách hàng ví dụ.\n\n"
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
        accumulated_ans = ""
        stream = reg.get("summarize").stream_text(
            prompt,
            system=_SUMMARIZE_SYSTEM + tz_note,
        )
        for chunk in stream:
            accumulated_ans += chunk
            if writer is not None:
                writer({"final_answer": accumulated_ans})

        ans = format_display_for_chat_ui(accumulated_ans)
        ans = finalize_answer(
            ans,
            deps=deps,
            node_name="summarize",
            scenario="sql_summary",
            user_question=user_q,
            has_query_result=True,
            query_result=qr if isinstance(qr, dict) else None,
            skip_quality=True,
        )
        preview = ans if len(ans) <= 1200 else ans[:1200] + "…"
        emit_agent_trace(
            logger,
            deps.settings,
            agent="summarize",
            phase="Tóm tắt kết quả SQL (LLM)",
            detail=f"văn_bản_phản_hồi:\n{preview}",
        )
        return {**progress_dict, "final_answer": ans, "messages": [AIMessage(content=ans)]}

    return summarize_answer

