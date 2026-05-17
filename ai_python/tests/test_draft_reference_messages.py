from __future__ import annotations

from app.graph.draft_reference_messages import format_reference_validation_failure


def test_format_reference_validation_failure() -> None:
    msg = format_reference_validation_failure(
        draft_kind="phiếu nhập kho",
        issues=["Nhà cung cấp: Không tìm thấy Tên NCC", "Dòng 1 (SKU-X): Không tìm thấy Mã SKU"],
    )
    assert "phiếu nhập kho" in msg
    assert "Nhà cung cấp" in msg
    assert "SKU-X" in msg
