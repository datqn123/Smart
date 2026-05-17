"""SQL failure clarify + staff table selection."""

from __future__ import annotations

from app.graph.sql_clarify import build_sql_failure_clarify
from app.graph.sql_table_selection import (
    ensure_context_tables_for_question,
    question_needs_users_table,
)


def test_question_needs_users_table():
    assert question_needs_users_table("chi tiết phiếu nhập và nhân viên tạo phiếu")
    assert not question_needs_users_table("tổng doanh thu tháng 5")


def test_ensure_context_injects_users_within_cap():
    picked = [
        "stockreceipts",
        "suppliers",
        "stockreceiptdetails",
        "partnerdebts",
        "productunits",
        "categories",
        "products",
        "warehouses",
    ]
    out = ensure_context_tables_for_question(
        "phiếu nhập PN-1 gồm NCC và nhân viên tạo phiếu",
        picked,
        max_tables=8,
        known_tables=set(picked) | {"users"},
    )
    assert "users" in {t.lower() for t in out}
    assert len(out) <= 8


def test_build_sql_failure_clarify_users_allowlist():
    state = {
        "error_payload": {"error": "max_sql_attempts", "attempts": 3},
        "messages": [],
        "normalized_user_question": (
            "chi tiết phiếu nhập PN-V10-00002, gồm NCC và nhân viên tạo phiếu"
        ),
        "generated_sql": (
            "SELECT s.receipt_code, u.full_name FROM stockreceipts s "
            "JOIN users u ON s.staff_id = u.id"
        ),
        "validation_feedback": {
            "policy": [
                "table not in allowlist ['stockreceipts', 'suppliers', "
                "'stockreceiptdetails', 'partnerdebts', 'productunits', "
                "'categories', 'products', 'warehouses']"
            ],
        },
    }
    pack = build_sql_failure_clarify(state)
    assert pack is not None
    sse = pack["sse"]
    assert sse.get("clarifyKind") == "sql_failure"
    assert sse.get("questions")
    assert any(i.get("type") == "sql_table_missing" for i in sse.get("issues", []))
    assert "users" in (sse.get("suggestedRewrite") or "").lower() or sse.get("suggestedRewrite")
