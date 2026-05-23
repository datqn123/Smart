"""Task112 — ERP domain guard unit tests."""

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage

from app.graph.erp_guide.load_index import load_domain_index
from app.graph.erp_guide.retrieve import detect_heuristic_misnomers, retrieve_guide_snippets
from app.graph.erp_guide.slot_resolution import strip_catalog_draft_misnomers
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


def test_expand_follow_up_retail_from_thread() -> None:
    from app.graph.erp_guide.slot_resolution import expand_elliptical_follow_up

    tail = (
        "User: trong tháng này có bao nhiêu đơn hàng bán lẻ nhỉ\n\n"
        "Assistant: Số lượng đơn hàng bán lẻ trong tháng này là 9."
    )
    expanded = expand_elliptical_follow_up("chi tiết từng đơn", tail)
    assert "bán lẻ" in expanded.lower()


def test_filter_order_channel_slot_when_in_dialog() -> None:
    from app.graph.erp_guide.slot_resolution import filter_resolved_missing_slots

    tail = "User: đơn hàng bán lẻ tháng này\n\nAssistant: 9 đơn"
    slots = filter_resolved_missing_slots(
        "chi tiết từng đơn",
        ["order_channel", "Which order type"],
        dialog_tail=tail,
    )
    assert slots == []


def test_proceed_follow_up_retail_orders() -> None:
    from app.graph.nodes.domain_guard import _apply_hard_rules
    from app.llm.schemas import DomainGuardOutput

    tail = (
        "User: trong tháng này có bao nhiêu đơn hàng bán lẻ nhỉ\n\n"
        "Assistant: 9 đơn hàng bán lẻ."
    )
    out = DomainGuardOutput(
        action="clarify",
        in_scope=True,
        coverage="partial",
        missing_slots=["order_channel"],
        clarification_questions=["Bạn muốn xem chi tiết loại đơn hàng nào?"],
        normalized_question="chi tiết từng đơn",
    )
    final = _apply_hard_rules(
        out, [], user_question="chi tiết từng đơn", dialog_tail=tail
    )
    assert final.action == "proceed"
    assert "bán lẻ" in final.normalized_question.lower()


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


def test_strip_catalog_category_name_misnomer() -> None:
    issues = [
        DomainIssue(
            type="term_mismatch",
            user_text="đồ uống",
            canonical_vi="loại sản phẩm",
            severity="block",
        )
    ]
    q = "Thêm món bánh tráng trộn vào danh mục Đồ uống"
    assert strip_catalog_draft_misnomers(issues, q) == []


def test_catalog_write_proceed_after_strip_misnomer() -> None:
    out = DomainGuardOutput(
        action="clarify",
        in_scope=True,
        matched_modules=["catalog"],
        coverage="full",
        issues=[
            DomainIssue(
                type="term_mismatch",
                user_text="đồ uống",
                canonical_vi="loại sản phẩm",
                severity="block",
            )
        ],
        normalized_question="Thêm món bánh tráng trộn vào danh mục Đồ uống",
    )
    final = _apply_hard_rules(
        out,
        [],
        user_question="Thêm món bánh tráng trộn vào danh mục Đồ uống",
    )
    assert final.action == "proceed"


def test_repeated_catalog_question_proceeds() -> None:
    q = "Thêm món bánh tráng trộn vào danh mục Đồ uống"
    messages = [
        HumanMessage(content=q),
        AIMessage(content="Cần làm rõ thêm"),
        HumanMessage(content=q),
    ]
    out = DomainGuardOutput(
        action="clarify",
        in_scope=True,
        matched_modules=["[catalog]"],
        coverage="full",
        issues=[
            DomainIssue(
                type="term_mismatch",
                user_text="món",
                canonical_vi="sản phẩm",
                severity="block",
            )
        ],
        normalized_question=q,
    )
    final = _apply_hard_rules(
        out,
        [],
        user_question=q,
        messages=messages,
    )
    assert final.action == "proceed"
