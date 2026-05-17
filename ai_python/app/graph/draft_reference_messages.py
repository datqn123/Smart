"""Format DB reference validation for chat responses."""

from __future__ import annotations


def format_draft_schema_issues(
    *,
    doc_kind: str,
    issues: list[str],
    extra_hints: list[str] | None = None,
    max_items: int = 8,
) -> str:
    head = f"Chưa đủ thông tin để tạo nháp **{doc_kind}**:\n"
    bullets = "\n".join(f"- {item}" for item in issues[:max_items])
    tail = ""
    if len(issues) > max_items:
        tail = f"\n- … và {len(issues) - max_items} mục khác"
    is_receipt = "nhập" in doc_kind.lower()
    hints = extra_hints or (
        [
            "Phiếu nhập cần **số lượng nhập** (bao nhiêu hàng nhập vào kho) — không phải tồn kho hiện tại.",
            "Gửi lại đủ: **mã SKU + mã/tên NCC + số lượng nhập** (vd: … số lượng 50).",
        ]
        if is_receipt
        else [
            "Kiểm tra **mã SKU** và **số lượng xuất** so với tồn kho.",
            "Gửi lại: mã SKU + số lượng xuất.",
        ]
    )
    hint_block = "\n".join(f"- {h}" for h in hints)
    return head + bullets + tail + "\n\nGợi ý:\n" + hint_block


def format_reference_validation_failure(
    *,
    draft_kind: str,
    issues: list[str],
    max_items: int = 8,
) -> str:
    head = (
        f"Không thể hiển thị nháp **{draft_kind}** vì một số giá trị chưa khớp dữ liệu trong hệ thống:\n"
    )
    bullets = "\n".join(f"- {item}" for item in issues[:max_items])
    tail = ""
    if len(issues) > max_items:
        tail = f"\n- … và {len(issues) - max_items} lỗi khác"
    hint = (
        "\n\nHãy dùng **đúng mã** (SKU, mã NCC, mã danh mục…) đã có trong Mini ERP, "
        "hoặc tạo master data trước rồi thử lại."
    )
    return head + bullets + tail + hint
