"""Unit tests for answer quality profiles and heuristic gate."""

from __future__ import annotations

from app.config.graph_settings import GraphSettings
from app.graph.answer_quality import (
    QualityContext,
    _answer_fabricates_entities,
    check_answer_quality,
    enforce_answer_quality,
)
from app.graph.deps import GraphDeps
from app.graph.sql_executor import StubSqlExecutor


def _deps() -> GraphDeps:
    return GraphDeps(
        llm_registry=None,
        sql_executor=StubSqlExecutor(),
        settings=GraphSettings(answer_quality_enabled=True),
    )


def test_sql_empty_short_fails() -> None:
    ctx = QualityContext(
        node_name="summarize",
        scenario="sql_empty",
        has_query_result=False,
    )
    v = check_answer_quality("Không có dữ liệu.", ctx=ctx)
    assert not v.passed


def test_sql_empty_template_passes() -> None:
    from app.graph.answer_fallbacks import SQL_EMPTY_VI

    ctx = QualityContext(
        node_name="summarize",
        scenario="sql_empty",
        has_query_result=False,
    )
    v = check_answer_quality(SQL_EMPTY_VI, ctx=ctx)
    assert v.passed


def test_domain_clarify_skipped() -> None:
    ctx = QualityContext(node_name="domain_guard", scenario="domain_clarify")
    v = check_answer_quality("Ngắn.", ctx=ctx)
    assert v.passed


def test_sql_error_allows_xin_loi_when_long_enough() -> None:
    msg = (
        "Xin lỗi, không hoàn tất truy vấn (mã lỗi: timeout). "
        "Bạn có thể thử hỏi lại với khoảng thời gian rõ hơn, ví dụ doanh thu đơn bán lẻ tháng 5/2026, "
        "hoặc liệt kê 10 đơn gần nhất."
    )
    ctx = QualityContext(
        node_name="summarize",
        scenario="sql_error",
        has_query_result=False,
    )
    v = check_answer_quality(msg, ctx=ctx)
    assert v.passed


def test_enforce_uses_fallback_when_llm_missing() -> None:
    short = "Không có dữ liệu phù hợp."
    ctx = QualityContext(
        node_name="summarize",
        scenario="sql_empty",
        has_query_result=False,
        fallback_template_id="sql_empty_vi",
    )
    out = enforce_answer_quality(short, ctx=ctx, deps=_deps(), max_enrich_attempts=1)
    assert len(out) >= 200
    assert "Bạn có thể" in out.lower() or "ví dụ" in out.lower()


def test_quality_disabled_returns_original() -> None:
    deps = GraphDeps(
        llm_registry=None,
        sql_executor=StubSqlExecutor(),
        settings=GraphSettings(answer_quality_enabled=False),
    )
    ctx = QualityContext(node_name="chat_normal", scenario="chat")
    out = enforce_answer_quality("Hi.", ctx=ctx, deps=deps)
    assert out == "Hi."


def test_sql_summary_rejects_no_data_claim_when_rows_present() -> None:
    ctx = QualityContext(
        node_name="summarize",
        scenario="sql_summary",
        has_query_result=True,
    )
    v = check_answer_quality(
        "Tổng giá trị tồn kho hiện tại không có dữ liệu.",
        ctx=ctx,
    )
    assert not v.passed
    assert any("no data" in i.lower() or "rows" in i.lower() for i in v.issues)


def test_scalar_summary_formats_number() -> None:
    from app.graph.nodes.summarize import _try_single_scalar_summary

    ans = _try_single_scalar_summary(
        {"rows": [{"total_inventory_value": 30554000}]},
        "Tổng giá trị tồn kho hiện tại là bao nhiêu?",
    )
    assert ans and "30.554.000" in ans


def test_scalar_summary_null_not_no_data() -> None:
    from app.graph.nodes.summarize import _try_single_scalar_summary

    ans = _try_single_scalar_summary(
        {"rows": [{"total_inventory_value": None}]},
        "Tổng giá trị tồn kho hiện tại là bao nhiêu?",
    )
    assert ans and "chưa tính được" in ans
    assert "không có dữ liệu" not in ans.lower()


def test_row_highlight_summary_top_receipt() -> None:
    from app.graph.nodes.summarize import _try_single_row_highlight_summary

    qr = {
        "rows": [{"receipt_code": "PN-2026-0005", "total_amount": 56000000.0}],
    }
    ans = _try_single_row_highlight_summary(
        qr,
        "Phiếu nhập kho nào có tổng giá trị cao nhất?",
    )
    assert ans
    assert "PN-2026-0005" in ans
    assert "56.000.000" in ans


def test_sql_summary_rejects_vague_without_row_values() -> None:
    qr = {"rows": [{"receipt_code": "PN-2026-0005", "total_amount": 56000000.0}]}
    ctx = QualityContext(
        node_name="summarize",
        scenario="sql_summary",
        has_query_result=True,
        query_result=qr,
    )
    vague = (
        "Dựa trên dữ liệu phiếu nhập kho, chúng ta có thể xác định phiếu nhập kho "
        "có tổng giá trị cao nhất."
    )
    v = check_answer_quality(vague, ctx=ctx)
    assert not v.passed
    assert any("omits" in i.lower() or "rows" in i.lower() for i in v.issues)


def test_sql_summary_passes_when_row_values_quoted() -> None:
    qr = {"rows": [{"receipt_code": "PN-2026-0005", "total_amount": 56000000.0}]}
    ctx = QualityContext(
        node_name="summarize",
        scenario="sql_summary",
        has_query_result=True,
        query_result=qr,
    )
    good = (
        "Phiếu nhập kho **PN-2026-0005** có tổng giá trị cao nhất là **56.000.000**. "
        "Chi tiết từ truy vấn: mã phiếu PN-2026-0005, total_amount 56.000.000 VND. "
        "Đây là phiếu nhập kho đứng đầu khi sắp xếp theo total_amount giảm dần (LIMIT 1)."
    )
    v = check_answer_quality(good, ctx=ctx)
    assert v.passed


def test_aggregate_only_rejects_fabricated_products() -> None:
    qr = {"rows": [{"total_value": 8233000}]}
    fabricated = (
        "Tổng giá trị vốn là **8.233.000đ**, bao gồm các mặt hàng như "
        "**áo sơ mi, quần tây và áo khoác**."
    )
    assert _answer_fabricates_entities(fabricated, qr)
    ctx = QualityContext(
        node_name="summarize",
        scenario="sql_summary",
        has_query_result=True,
        query_result=qr,
    )
    v = check_answer_quality(fabricated, ctx=ctx)
    assert not v.passed
    assert any("invents" in i.lower() for i in v.issues)


def test_aggregate_scalar_short_answer_passes() -> None:
    qr = {"rows": [{"total_value": 8233000}]}
    ans = (
        "Tổng giá trị vốn từ các phiếu nhập đã duyệt là **8.233.000đ**. "
        "Nếu bạn muốn chi tiết theo mặt hàng hoặc phiếu, hãy nêu mã cụ thể nhé."
    )
    ctx = QualityContext(
        node_name="summarize",
        scenario="sql_summary",
        has_query_result=True,
        query_result=qr,
    )
    v = check_answer_quality(ans, ctx=ctx)
    assert v.passed
