"""Build user clarify SSE when SQL pipeline cannot complete (Task112-style)."""

from __future__ import annotations

import re
from typing import Any

from app.graph.message_utils import effective_user_question
from app.graph.state import AgentState
from app.llm.schemas import DomainIssue

# Tables often required by question wording but dropped by 8-table cap / table pick.
_TABLE_LABEL_VI: dict[str, str] = {
    "users": "bảng nhân viên (users)",
    "customers": "bảng khách hàng",
    "salesorders": "bảng đơn hàng",
    "categories": "bảng danh mục",
    "roles": "bảng vai trò",
}

_STAFF_PHRASES = (
    "nhân viên",
    "nhan vien",
    "người tạo",
    "nguoi tao",
    "người lập",
    "nguoi lap",
    "staff",
    "nhân sự",
    "nhan su",
    "tạo phiếu",
    "tao phieu",
)

_RECEIPT_PHRASES = (
    "phiếu nhập",
    "phieu nhap",
    "nhập kho",
    "nhap kho",
    "stockreceipt",
)


def _extract_tables_from_sql(sql: str | None) -> set[str]:
    if not sql:
        return set()
    found: set[str] = set()
    for m in re.finditer(
        r"(?is)\b(?:from|join)\s+([a-z_][a-z0-9_]*)",
        sql,
    ):
        found.add(m.group(1).lower())
    return found


def _policy_messages(state: AgentState) -> list[str]:
    fb = state.get("validation_feedback")
    if not isinstance(fb, dict):
        return []
    out: list[str] = []
    for key in ("policy", "intent_review", "exec", "result"):
        raw = fb.get(key)
        if isinstance(raw, list):
            out.extend(str(x) for x in raw if x)
        elif raw:
            out.append(str(raw))
    return out


def _forbidden_tables(policy_msgs: list[str], allowlist: set[str] | None) -> list[str]:
    forbidden: list[str] = []
    for msg in policy_msgs:
        if "allowlist" not in msg.lower():
            continue
        sql_tables = _extract_tables_from_sql(msg)
        for t in sql_tables:
            if allowlist and t not in allowlist and t not in forbidden:
                forbidden.append(t)
    # Also compare last generated SQL vs allowlist from state
    return forbidden


def _allowlist_from_feedback(policy_msgs: list[str]) -> set[str] | None:
    for msg in policy_msgs:
        if "allowlist" not in msg.lower():
            continue
        parts = re.findall(r"'([^']+)'", msg)
        if parts:
            return {p.lower() for p in parts}
    return None


def _suggest_simpler_question(
    question: str,
    *,
    forbidden: list[str],
    allowlist: set[str] | None,
) -> str:
    q = question.strip()
    if "users" in forbidden and allowlist and "users" not in allowlist:
        return (
            f"{q}\n"
            "(Chỉ cần mã nhân viên staff_id trên phiếu, không cần tên đầy đủ.)"
        ).strip()
    if forbidden:
        return (
            f"{q}\n"
            f"(Thu hẹp phạm vi — chỉ dùng các bảng: {', '.join(sorted(allowlist or []))}.)"
        ).strip()
    return q


def build_sql_failure_clarify(state: AgentState) -> dict[str, Any] | None:
    """
    When SQL retries are exhausted, return clarify payload for FE (same shape as domain guard).
    Returns None if clarify is not appropriate (caller should use generic error).
    """
    err = state.get("error_payload")
    if not isinstance(err, dict) or err.get("error") != "max_sql_attempts":
        return None

    question = effective_user_question(
        state.get("messages"), state.get("normalized_user_question")
    )
    policy_msgs = _policy_messages(state)
    allowlist = _allowlist_from_feedback(policy_msgs)
    sql = str(state.get("generated_sql") or "")
    sql_tables = _extract_tables_from_sql(sql)
    forbidden = [
        t
        for t in sql_tables
        if allowlist and t not in allowlist
    ]
    if not forbidden:
        forbidden = _forbidden_tables(policy_msgs, allowlist)

    issues: list[DomainIssue] = []
    questions: list[str] = []
    guide_refs: list[str] = []

    if forbidden:
        for tbl in forbidden[:3]:
            label = _TABLE_LABEL_VI.get(tbl, f"bảng `{tbl}`")
            issues.append(
                DomainIssue(
                    type="sql_table_missing",
                    user_text=tbl,
                    canonical_vi=label,
                    severity="block",
                )
            )
        if "users" in forbidden:
            questions.extend(
                [
                    "Bạn cần **tên đầy đủ** của nhân viên tạo phiếu, hay chỉ cần **mã nhân viên (staff_id)** trên phiếu?",
                    "Bạn có thể hỏi lại theo hướng: chi tiết phiếu + nhà cung cấp (bỏ tên nhân viên) nếu chỉ cần thông tin phiếu?",
                ]
            )
            guide_refs.append("05_inventory")
        else:
            questions.append(
                f"Câu hỏi cần dữ liệu từ {', '.join(_TABLE_LABEL_VI.get(t, t) for t in forbidden)} "
                f"nhưng phiên hiện chỉ chọn được {len(allowlist or [])} bảng. "
                "Bạn muốn ưu tiên phần nào (vd. chỉ phiếu + NCC)?"
            )

    if not questions:
        if any(p in question.lower() for p in _STAFF_PHRASES):
            questions = [
                "Bạn muốn xem thông tin nhân viên ở mức nào (tên, mã NV, hay bỏ qua)?",
                "Phiếu nhập cần thêm trường nào ngoài mã phiếu và nhà cung cấp?",
            ]
        elif any(p in question.lower() for p in _RECEIPT_PHRASES):
            questions = [
                "Bạn cần chi tiết **một phiếu** (mã cụ thể) hay **danh sách** phiếu theo điều kiện?",
                "Có cần lọc theo trạng thái (Pending / Approved) không?",
            ]
        else:
            questions = [
                "Bạn có thể nêu rõ hơn khoảng thời gian hoặc mã cụ thể (phiếu, SKU, đơn hàng)?",
                "Bạn muốn xem tổng hợp (số lượng) hay danh sách chi tiết từng dòng?",
            ]

    if not issues and not questions:
        return None

    suggested = _suggest_simpler_question(
        question,
        forbidden=forbidden,
        allowlist=allowlist,
    )
    intro = (
        "Tôi chưa chạy được truy vấn sau vài lần thử. "
        "Làm rõ thêm giúp tôi — xem gợi ý và câu đề xuất bên dưới."
    )
    if forbidden and "users" in forbidden:
        intro = (
            "Để hiển thị **tên nhân viên** cần bảng users, nhưng phiên này chưa nạp bảng đó. "
            "Chọn một hướng bên dưới hoặc gửi lại câu đề xuất."
        )

    sse = {
        "questions": questions[:4],
        "issues": [i.model_dump() for i in issues],
        "guideRefs": guide_refs,
        "originalQuestion": question,
        "suggestedRewrite": suggested,
        "suggestedNormalized": suggested,
        "matchedModules": ["sql_pipeline"],
        "clarifyKind": "sql_failure",
    }
    return {
        "intro": intro,
        "sse": sse,
    }
