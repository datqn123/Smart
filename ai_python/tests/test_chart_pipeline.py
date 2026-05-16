"""Tests for LLM-first chart pipeline helpers."""

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage

from app.config.graph_settings import GraphSettings
from app.graph.chart_data_profile import build_query_result_profile
from app.graph.chart_thread_context import format_prior_turns_for_chart
from app.graph.nodes.chart_readiness import _heuristic_readiness
from app.graph.nodes.sql_pipeline import _effective_ledger_first_prompts


def test_build_query_result_profile_time_columns() -> None:
    qr = {
        "rows": [
            {"month": "2026-01-01", "cnt": 10},
            {"month": "2026-02-01", "cnt": 12},
        ],
    }
    p = build_query_result_profile(qr)
    assert p["row_count"] == 2
    assert "month" in p.get("time_like_columns", [])


def test_heuristic_time_series_needs_multiple_rows() -> None:
    ok, issues, _ = _heuristic_readiness({"row_count": 1, "time_like_columns": []}, expected_shape="time_series")
    assert not ok
    assert issues


def test_effective_ledger_first_off_for_warehouse_chart_brief() -> None:
    s = GraphSettings(sql_ledger_first_prompts=True)
    state = {
        "intent": "system_data_chart",
        "idea_data_request": {
            "entity": "stock dispatch",
            "metric": "count shipped",
            "expected_result_shape": "time_series",
        },
    }
    assert _effective_ledger_first_prompts(state, s) is False


def test_effective_ledger_first_on_for_revenue_chart() -> None:
    s = GraphSettings(sql_ledger_first_prompts=True)
    state = {
        "intent": "system_data_chart",
        "idea_data_request": {"metric": "doanh thu", "source": "financeledger"},
    }
    assert _effective_ledger_first_prompts(state, s) is True


def test_format_prior_turns_for_chart() -> None:
    msgs = [
        HumanMessage(content="có bao nhiêu đơn xuất kho từ 2026"),
        AIMessage(content="34 đơn."),
        HumanMessage(content="vẽ biểu đồ tương tự"),
    ]
    ctx = format_prior_turns_for_chart(msgs, max_turns=2)
    assert "34 đơn" in ctx
    assert "xuất kho" in ctx
