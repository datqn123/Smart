from __future__ import annotations

import os
from typing import Any


def format_turn_as_chat_text(turn: dict[str, Any]) -> str:
    """
    Chuyển kết quả ``run_smart_erp_turn`` thành một đoạn chat thuần văn bản
    (không UI bảng/form — chỉ tóm tắt cho SSE ``delta``).
    """
    steps: list[dict[str, Any]] = list(turn.get("steps") or [])
    lines: list[str] = []

    intent_result: dict[str, Any] = {}
    for s in steps:
        if s.get("tool") == "intent_analyze":
            intent_result = dict(s.get("result") or {})
            break

    if not intent_result.get("ok", True):
        return "Xin lỗi, tôi không phân tích được yêu cầu của bạn."

    primary = str(intent_result.get("primary_intent", "?"))
    debug = os.getenv("SMART_ERP_CHAT_DEBUG", "false").strip().lower() in ("1", "true", "yes")
    if debug:
        lines.append(f"Ý định: {primary}.")

    if primary == "refusal":
        return "Tôi không thể hỗ trợ yêu cầu đó."
    if primary == "greeting":
        return "Xin chào! Bạn muốn hỏi về tồn kho, SKU, đơn hàng, hay schema Database?"

    for step in steps:
        tool = step.get("tool")
        raw = step.get("result")
        res: dict[str, Any] = raw if isinstance(raw, dict) else {}
        if tool == "rag_retrieve" and res.get("ok") and res.get("chunks"):
            lines.append("Tham chiếu nhanh (RAG / tài liệu):")
            for ch in res["chunks"][:3]:
                txt = str(ch.get("text", "")).strip()
                if txt:
                    lines.append(f"- {txt[:400]}{'…' if len(txt) > 400 else ''}")
            warn = res.get("rag_stale_warning")
            if isinstance(warn, str) and warn:
                lines.append(f"Lưu ý: {warn}")
        if tool == "sql_execute_read":
            if not res.get("ok"):
                err = res.get("error")
                msg = (
                    err.get("message", "lỗi")
                    if isinstance(err, dict)
                    else "lỗi"
                )
                lines.append(f"Không đọc được dữ liệu: {msg}.")
                continue
            cols = list(res.get("columns") or [])
            rows = list(res.get("rows") or [])
            lines.append("Số liệu (DB read-only qua template, tối đa 5 dòng):")
            if cols:
                lines.append(" | ".join(str(c) for c in cols))
            for row in rows[:5]:
                lines.append(" | ".join(str(x) for x in row))
            if res.get("data_as_of"):
                lines.append(f"(Cập nhật tại: {res['data_as_of']})")
        if tool == "viz_build_chart_spec" and res.get("ok"):
            lines.append("(Biểu đồ rich UI chưa bật; đã lấy series phục vụ báo cáo.)")

    if len(lines) <= (2 if debug else 1) and primary in ("conversation", "help", "rag_qa"):
        lines.append("Bạn có thể hỏi cụ thể hơn về tồn kho, SKU, doanh thu, hoặc tài liệu dự án.")

    return "\n".join(lines).strip()
