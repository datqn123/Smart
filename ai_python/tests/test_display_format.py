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


def test_format_fixes_glued_don_so() -> None:
    """ĐơnSO should be normalised to Đơn SO."""
    raw = "tại quầy.- ĐơnSO-2026-000071(17/05/2026 19: 28: 01)"
    out = format_display_for_chat_ui(raw)
    assert "ĐơnSO" not in out
    assert "Đơn SO-2026-000071" in out


def test_format_fixes_missing_space_after_dash() -> None:
    """-Đơn should become - Đơn."""
    raw = "-Đơn SO-2026-000066 (13/05/2026 21:45:27)"
    out = format_display_for_chat_ui(raw)
    assert out.startswith("- Đơn SO")


def test_format_breaks_inline_don_so_items() -> None:
    """Multiple orders glued on the same line should each get their own line."""
    raw = (
        "thực thu 96.000đ- ĐơnSO-2026-000068(17/05/2026 07: 37: 19): "
        "Tổng 24.000đ, thực thu 24.000đ"
    )
    out = format_display_for_chat_ui(raw)
    assert "\n\n- Đơn SO-2026-000068" in out


def test_format_preserves_already_correct_lines() -> None:
    """Lines that already have correct formatting should not be mangled."""
    raw = "- Đơn SO-2026-000070 (17/05/2026 19:27:48): Tổng 36.000đ"
    out = format_display_for_chat_ui(raw)
    assert out.startswith("- Đơn SO-2026-000070")


def test_format_multiple_glued_orders() -> None:
    """A full block with multiple glued orders."""
    raw = (
        "thực thu 96.000đ- ĐơnSO-2026-000068(17/05/2026 07: 37: 19): "
        "Tổng 24.000đ, thực thu 24.000đ "
        "thực thu 35.700đ- ĐơnSO-2026-000063(02/05/2026 21: 10: 44): "
        "Tổng 42.000đ, thực thu 42.000đ"
    )
    out = format_display_for_chat_ui(raw)
    assert out.count("- Đơn SO") == 2
    assert "ĐơnSO" not in out

