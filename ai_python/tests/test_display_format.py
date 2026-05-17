"""Tests for chat display formatting helpers."""

from __future__ import annotations

from app.graph.display_format import format_display_for_chat_ui


def test_format_inserts_breaks_before_inline_order_list() -> None:
    raw = (
        "Tối nay có 2 đơn hàng được bán: - Đơn hàng SO-2026-000066 với tổng tiền 24.000đ "
        "- Đơn hàng SO-2026-000065 với tổng tiền 48.000đ"
    )
    out = format_display_for_chat_ui(raw)
    assert "bán:\n\n- Đơn" in out
    assert out.count("\n\n- Đơn hàng") >= 2


def test_format_empty() -> None:
    assert format_display_for_chat_ui("") == ""
    assert format_display_for_chat_ui("   ") == ""
