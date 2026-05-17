"""Tests for enum literal canonicalization in SQL."""

from __future__ import annotations

from app.config.graph_settings import GraphSettings
from app.graph.enum_literals import canonical_enum_literal, fix_enum_literals_in_sql
from app.graph.nodes.chart_readiness import _state_for_chart_retry_route, route_after_chart_readiness_in_sql
from app.graph.retry_policy import RetryAction, decide_chart_readiness_retry
from app.graph.validate_sql import validate_sql_deterministic


def test_canonical_enum_literal_approved() -> None:
    assert canonical_enum_literal("approved") == "Approved"
    assert canonical_enum_literal("Approved") == "Approved"
    assert canonical_enum_literal("retail") == "Retail"


def test_fix_stockreceipts_status_lowercase() -> None:
    sql = (
        "SELECT COUNT(*) FROM stockreceipts "
        "WHERE status = 'approved' AND approved_at >= '2026-01-01'"
    )
    fixed, notes = fix_enum_literals_in_sql(sql)
    assert "status = 'Approved'" in fixed
    assert notes


def test_fix_order_channel_and_payment_status() -> None:
    sql = (
        "SELECT * FROM salesorders WHERE order_channel = 'retail' "
        "AND payment_status = 'unpaid'"
    )
    fixed, _ = fix_enum_literals_in_sql(sql)
    assert "order_channel = 'Retail'" in fixed
    assert "payment_status = 'Unpaid'" in fixed


def test_fix_status_in_clause() -> None:
    sql = "SELECT 1 FROM stockdispatches WHERE status IN ('pending', 'delivered')"
    fixed, notes = fix_enum_literals_in_sql(sql)
    assert "status IN ('Pending', 'Delivered')" in fixed
    assert notes


def test_validate_sql_deterministic_applies_enum_fix() -> None:
    settings = GraphSettings(sql_allowed_tables="stockreceipts")
    sql = "SELECT id FROM stockreceipts WHERE status = 'approved'"
    ok, _, sanitized, notes = validate_sql_deterministic(
        sql,
        settings,
        allowlist_tables={"stockreceipts"},
        table_columns={"stockreceipts": {"id", "status", "approved_at"}},
    )
    assert ok
    assert sanitized is not None
    assert "status = 'Approved'" in sanitized
    assert any("Approved" in n for n in notes)


def test_chart_retry_route_ignores_same_turn_feedback() -> None:
    state = {
        "intent": "system_data_chart",
        "chart_data_ok": False,
        "sql_attempt_count": 1,
        "validation_feedback": {
            "result": ["chart readiness: use status = 'Approved'"],
        },
    }
    trimmed = _state_for_chart_retry_route(state)
    assert decide_chart_readiness_retry(trimmed).action == RetryAction.REGEN_SQL
    assert route_after_chart_readiness_in_sql(state) == "gen_sql"
