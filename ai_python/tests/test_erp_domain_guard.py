"""Task112 — ERP domain guard unit tests."""

from __future__ import annotations

from app.graph.erp_guide.load_index import load_domain_index
from app.graph.erp_guide.retrieve import detect_heuristic_misnomers, retrieve_guide_snippets
from app.graph.nodes.domain_guard import _apply_hard_rules
from app.llm.schemas import DomainGuardOutput, DomainIssue


def test_load_domain_index_has_modules() -> None:
    index = load_domain_index()
    assert len(index.get("modules") or []) >= 10


def test_heuristic_misnomer_xuat_khau() -> None:
    index = load_domain_index()
    hits = detect_heuristic_misnomers("danh sách phiếu xuất khẩu tháng 5", index)
    assert len(hits) >= 1
    assert any("xuất khẩu" in h.get("user_text", "") for h in hits)


def test_retrieve_stock_dispatch_chunk() -> None:
    snippets = retrieve_guide_snippets("phiếu xuất kho pending", max_chunks=2)
    assert len(snippets) >= 1


def test_build_suggested_rewrite_nhap_khau() -> None:
    from app.graph.erp_guide.rewrite import build_suggested_rewrite
    from app.llm.schemas import DomainIssue

    issues = [
        DomainIssue(
            type="term_mismatch",
            user_text="nhập khẩu",
            canonical_vi="phiếu nhập kho",
            severity="block",
        )
    ]
    original = "Vẽ biểu đồ thể hiện đơn hàng nhập khẩu từng tháng từ đầu năm 2026"
    rewritten = build_suggested_rewrite(original, issues, index=load_domain_index())
    assert "nhập khẩu" not in rewritten.lower()
    assert "phiếu nhập kho" in rewritten.lower()


def test_filter_year_slot_when_time_in_question() -> None:
    from app.graph.erp_guide.slot_resolution import filter_resolved_missing_slots

    q = "Từ đầu năm tới giờ có bao nhiêu đơn hàng bán lẻ"
    slots = filter_resolved_missing_slots(q, ["year", "Which year", "order_status"])
    joined = " ".join(slots).lower()
    assert "year" not in joined and "năm nào" not in joined


def test_proceed_when_only_optional_slots() -> None:
    from app.graph.nodes.domain_guard import _apply_hard_rules
    from app.llm.schemas import DomainGuardOutput

    out = DomainGuardOutput(
        action="clarify",
        in_scope=True,
        coverage="partial",
        missing_slots=["year", "order_status"],
        normalized_question="Từ đầu năm tới giờ có bao nhiêu đơn hàng bán lẻ",
        clarification_questions=["Bạn muốn hỏi cho năm nào?"],
    )
    final = _apply_hard_rules(out, [], user_question="Từ đầu năm tới giờ có bao nhiêu đơn hàng bán lẻ")
    assert final.action == "proceed"


def test_strip_noop_term_issue() -> None:
    from app.graph.erp_guide.slot_resolution import strip_noop_issues
    from app.llm.schemas import DomainIssue

    issues = [
        DomainIssue(
            type="term_mismatch",
            user_text="từ đầu năm tới giờ",
            canonical_vi="từ đầu năm tới giờ",
            severity="block",
        )
    ]
    assert len(strip_noop_issues(issues)) == 0


def test_apply_hard_rules_blocks_on_severity() -> None:
    out = DomainGuardOutput(
        action="proceed",
        in_scope=True,
        normalized_question="test",
        issues=[],
    )
    block = DomainIssue(
        type="term_mismatch",
        user_text="xuất khẩu",
        canonical_vi="phiếu xuất kho",
        severity="block",
    )
    final = _apply_hard_rules(out, [block], user_question="phiếu xuất khẩu")
    assert final.action == "clarify"
