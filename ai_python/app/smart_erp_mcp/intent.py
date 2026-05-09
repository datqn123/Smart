from __future__ import annotations

from typing import Any, Literal

PrimaryIntent = Literal[
    "conversation",
    "rag_qa",
    "data_query",
    "visualization",
    "transactional_update",
    "help",
    "refusal",
]


def intent_analyze(user_text: str, session_id: str = "") -> dict[str, Any]:
    _ = session_id
    t = user_text.lower()
    risk_flags: list[str] = []

    if any(x in t for x in ("password", "api key", "secret", "token jwt")):
        return {
            "ok": True,
            "primary_intent": "refusal",
            "entities": {},
            "risk_flags": ["secret_probe"],
            "hitl_required": False,
            "suggested_tools": [],
        }

    transactional = any(
        x in t for x in ("cập nhật", "cap nhat", "update", "sửa số", "ghi db", "điều chỉnh tồn")
    )
    visualization = any(x in t for x in ("biểu đồ", "bieu do", "chart", "đồ thị", "do thi"))
    dataish = any(
        x in t
        for x in (
            "select",
            "sql",
            "truy vấn",
            "truy van",
            "query",
            "tồn kho",
            "ton kho",
            "doanh thu",
            "sku",
            "hàng hoá",
            "hang hoa",
        )
    )

    primary: PrimaryIntent
    suggested: list[str]
    hitl: bool
    if transactional:
        risk_flags.append("mutation_request")
        primary = "transactional_update"
        suggested = [
            "read_catalog_snapshot",
            "sql_execute_read",
            "ui_build_form_spec",
            "write_commit",
        ]
        hitl = True
    elif visualization:
        primary = "visualization"
        suggested = ["read_catalog_snapshot", "sql_execute_read", "viz_build_chart_spec"]
        hitl = False
    elif dataish:
        primary = "data_query"
        suggested = ["read_catalog_snapshot", "sql_propose_select", "sql_execute_read"]
        hitl = False
    else:
        primary = "rag_qa"
        suggested = ["rag_retrieve"]
        hitl = False

    entities: dict[str, Any] = {}
    if "sku" in t:
        entities["mentions_sku"] = True

    return {
        "ok": True,
        "primary_intent": primary,
        "entities": entities,
        "risk_flags": risk_flags,
        "hitl_required": hitl,
        "suggested_tools": suggested,
    }
