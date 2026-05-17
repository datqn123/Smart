"""Tests for LLM-first chart pipeline helpers."""

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage

from app.config.graph_settings import GraphSettings
from app.graph.chart_data_profile import build_query_result_profile
from app.graph.chart_thread_context import format_prior_turns_for_chart
from app.graph.chart_calendar import (
    calendar_spine_prompt_block,
    resolve_month_calendar,
    wants_zero_fill_months,
)
from app.graph.chart_schema_merge import infer_tables_from_chart_context
from app.graph.sql_prompts import build_gen_sql_user_prompt
from app.graph.chart_sql_shape import sql_has_time_grouping
from app.graph.nodes.chart_readiness import _heuristic_readiness
from app.graph.nodes.sql_pipeline import _effective_ledger_first_prompts
from app.graph.pg_schema_context import rank_tables_for_question


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


def test_heuristic_time_series_one_row_without_groupby_fails() -> None:
    ok, issues, warnings = _heuristic_readiness(
        {"row_count": 1, "time_like_columns": []},
        expected_shape="time_series",
        generated_sql="SELECT COUNT(*) FROM salesorders",
    )
    assert not ok
    assert issues
    assert not warnings


def test_heuristic_time_series_one_row_with_groupby_ok_warning() -> None:
    sql = (
        "SELECT DATE_TRUNC('month', created_at) AS month, COUNT(*) AS n "
        "FROM salesorders GROUP BY DATE_TRUNC('month', created_at)"
    )
    assert sql_has_time_grouping(sql)
    ok, issues, warnings = _heuristic_readiness(
        {"row_count": 1, "time_like_columns": ["month"]},
        expected_shape="time_series",
        generated_sql=sql,
    )
    assert ok
    assert not issues
    assert warnings


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


def test_infer_tables_retail_orders() -> None:
    q = "Hãy vẽ biểu đồ báo cáo tình hành đơn hàng bán lẻ từ đầu năm 2026"
    dr = {"metric": "Đếm đơn hàng bán lẻ", "filter": {"channel": "Retail"}}
    tables = infer_tables_from_chart_context(q, dr)
    assert "salesorders" in tables


def test_rank_tables_boosts_salesorders_for_retail_orders() -> None:
    rows = [
        ("stockdispatches", "Phiếu xuất kho"),
        ("salesorders", "Đơn bán kênh bán lẻ"),
        ("customers", "Khách hàng"),
    ]
    ranked = rank_tables_for_question(
        "đơn hàng bán lẻ từ 2026",
        rows,
        max_tables=2,
    )
    assert ranked[0] == "salesorders"


def test_format_prior_turns_for_chart() -> None:
    msgs = [
        HumanMessage(content="có bao nhiêu đơn xuất kho từ 2026"),
        AIMessage(content="34 đơn."),
        HumanMessage(content="vẽ biểu đồ tương tự"),
    ]
    ctx = format_prior_turns_for_chart(msgs, max_turns=2)
    assert "34 đơn" in ctx
    assert "xuất kho" in ctx


def test_wants_zero_fill_months_from_phrase() -> None:
    q = "vẽ biểu đồ đơn bán lẻ 2026, tháng không có đơn cũng vẽ"
    assert wants_zero_fill_months(q, None) is True


def test_resolve_month_calendar_jan_to_april() -> None:
    q = "đơn bán lẻ tháng 1-4 năm 2026, tháng không có đơn cũng vẽ"
    spec = resolve_month_calendar(q, {"include_zero_months": True})
    assert spec is not None
    assert spec.year == 2026
    assert spec.from_month == 1
    assert spec.to_month == 4
    assert spec.month_count == 4


def test_calendar_spine_prompt_block_mentions_generate_series() -> None:
    from app.graph.chart_calendar import MonthCalendarSpec

    spec = MonthCalendarSpec(year=2026, from_month=1, to_month=4)
    block = calendar_spine_prompt_block(spec)
    assert "generate_series" in block
    assert "LEFT JOIN" in block
    assert "4" in block


def test_heuristic_zero_fill_one_row_fails() -> None:
    ok, issues, _ = _heuristic_readiness(
        {"row_count": 1, "time_like_columns": ["month"]},
        expected_shape="time_series",
        generated_sql=(
            "SELECT DATE_TRUNC('month', created_at) AS month, COUNT(*) "
            "FROM salesorders GROUP BY 1"
        ),
        expected_month_count=4,
    )
    assert not ok
    assert any("include_zero_months" in i for i in issues)


def test_gen_sql_prompt_includes_calendar_block() -> None:
    from app.graph.chart_calendar import MonthCalendarSpec

    spec = MonthCalendarSpec(year=2026, from_month=1, to_month=12)
    prompt = build_gen_sql_user_prompt(
        mode="exploit",
        user_q="đơn bán lẻ 2026",
        schema_block="-- schema",
        feedback_render="",
        seed_sql=None,
        sql_limit_max=500,
        planner_data_request_json='{"expected_result_shape":"time_series"}',
        month_calendar=spec,
    )
    assert "generate_series" in prompt
    assert "include_zero_months" in prompt.lower() or "calendar spine" in prompt.lower()
