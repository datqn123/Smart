"""Inventory-specific resolution logic for stock dispatches and receipts.
"""

from __future__ import annotations

import logging
from typing import Any

from app.graph.sql_executor import SqlExecutor
from app.llm.schemas import DomainIssue, InventoryDraftSlotsOutput
from app.graph.draft_entity_resolution_common import (
    _strip_slot,
    _product_term_from_slots,
    _supplier_term_from_slots,
    _narrow_products_by_sku,
    _format_product_options,
    _format_supplier_options,
    _rows_from_result,
    search_products,
    search_suppliers,
    pack_clarify_state,
    _DOC_LABEL_VI,
)

logger = logging.getLogger(__name__)


def _resolve_stock_dispatch(
    *,
    question: str,
    doc_label: str,
    term: str,
    qty: int | None,
    products: list[dict[str, Any]],
    slots: InventoryDraftSlotsOutput,
) -> dict[str, Any] | None:
    products = _narrow_products_by_sku(products, slots)

    if len(products) > 1:
        opts = _format_product_options(products)
        qty_txt = f" {qty}" if qty else ""
        return pack_clarify_state(
            question=question,
            intro=(
                f"Có **{len(products)}** sản phẩm khớp «{term}». Chọn **một SKU** để xuất:\n\n{opts}"
            ),
            issues=[
                DomainIssue(
                    type="missing_slot",
                    user_text=term,
                    canonical_vi="Nhiều SKU — cần chọn một",
                    severity="block",
                )
            ],
            questions=[
                "Gửi lại kèm **mã SKU** chính xác.",
                f"Số lượng xuất{qty_txt or ''}?",
            ],
            suggested_rewrite=(
                f"Tạo phiếu xuất kho: SKU {products[0].get('sku_code')}, số lượng{qty_txt or ' …'}"
            ),
        )

    if len(products) == 1:
        p = products[0]
        sku = str(p.get("sku_code") or "—")
        name = str(p.get("name") or "—")
        
        # Thừa hưởng stock qty helper nội bộ
        from app.graph.draft_entity_resolution_common import _product_stock_qty
        stock = _product_stock_qty(p)

        if stock <= 0:
            want = f" **{qty}**" if qty else ""
            return pack_clarify_state(
                question=question,
                intro=(
                    f"**{sku}** — {name} có trong danh mục nhưng **tồn kho = 0**.\n\n"
                    f"Không thể xuất{want} cái khi chưa có hàng trong kho. "
                    "Hãy **nhập kho** (phiếu nhập) hoặc kiểm tra lô tại màn **Tồn kho** trước."
                ),
                issues=[
                    DomainIssue(
                        type="wrong_workflow",
                        user_text=sku,
                        canonical_vi="Hết tồn — không xuất được",
                        severity="block",
                    )
                ],
                questions=[
                    "Bạn có muốn tạo **phiếu nhập kho** cho sản phẩm này không?",
                ],
                suggested_rewrite=f"Tạo phiếu nhập kho SKU {sku} từ NCC …, số lượng …",
            )

        if qty is None:
            return pack_clarify_state(
                question=question,
                intro=(
                    f"Đã khớp **{sku}** — {name} (tồn kho: **{stock}**).\n\n"
                    "Cho biết **số lượng** cần xuất."
                ),
                issues=[
                    DomainIssue(
                        type="missing_slot",
                        user_text=sku,
                        canonical_vi="Thiếu số lượng xuất",
                        severity="block",
                    )
                ],
                questions=[f"Bạn muốn xuất **{sku}** bao nhiêu cái? (tối đa {stock})"],
                suggested_rewrite=f"Tạo phiếu xuất kho: SKU {sku}, số lượng …",
            )

        if qty > stock:
            return pack_clarify_state(
                question=question,
                intro=(
                    f"**{sku}** — {name}: tồn **{stock}**, không đủ để xuất **{qty}**.\n\n"
                    "Giảm số lượng hoặc nhập thêm hàng trước."
                ),
                issues=[
                    DomainIssue(
                        type="wrong_workflow",
                        user_text=str(qty),
                        canonical_vi="Số lượng xuất vượt tồn",
                        severity="block",
                    )
                ],
                questions=[
                    f"Xuất tối đa **{stock}** cái, hay nhập thêm tồn?",
                ],
                suggested_rewrite=f"Tạo phiếu xuất kho: SKU {sku}, số lượng {stock}",
            )

        return pack_clarify_state(
            question=question,
            intro=(
                f"Đã xác nhận xuất **{qty}** × **{sku}** — {name} (tồn hiện: **{stock}**).\n\n"
                f"Nháp **{doc_label}** qua chat đang hoàn thiện — "
                "vui lòng dùng màn **Xuất kho** để chọn lô và hoàn tất phiếu xuất."
            ),
            issues=[
                DomainIssue(
                    type="wrong_workflow",
                    user_text=sku,
                    canonical_vi="Đủ thông tin — xuất tại màn Xuất kho",
                    severity="warn",
                )
            ],
            questions=[],
            suggested_rewrite=f"Tạo phiếu xuất kho: SKU {sku}, số lượng {qty}",
        )

    return None


def _resolve_stock_receipt_before_generate(
    *,
    question: str,
    doc_label: str,
    slots: InventoryDraftSlotsOutput,
    products: list[dict[str, Any]],
    term: str,
    qty: int | None,
) -> dict[str, Any] | None:
    """Phiếu nhập: cần số lượng **nhập**, không so với tồn kho."""
    sku = _strip_slot(slots.product_sku) or (
        str(products[0].get("sku_code") or "") if len(products) == 1 else ""
    )
    sup = _supplier_term_from_slots(slots)

    if qty is None or qty <= 0:
        detail = ""
        if sku:
            detail += f"\n\nĐã khớp SKU **{sku}**"
        if sup:
            detail += f", NCC **{sup}**"
        if detail:
            detail += "."
        return pack_clarify_state(
            question=question,
            intro=(
                f"Để tạo **{doc_label}** cần **số lượng nhập** (> 0) — "
                "đây là số hàng bạn muốn nhập vào kho, **không** phải tồn kho hiện tại."
                f"{detail}"
            ),
            issues=[
                DomainIssue(
                    type="missing_slot",
                    user_text="số lượng nhập",
                    canonical_vi="Thiếu số lượng nhập",
                    severity="block",
                )
            ],
            questions=[
                "Bạn muốn nhập bao nhiêu? (vd: 50 thùng, 100 cái)",
                "Giá vốn đơn vị nếu đã biết (tuỳ chọn).",
            ],
            suggested_rewrite=(
                f"Tạo phiếu nhập kho SKU {sku or term} từ NCC {sup or '…'}, số lượng …"
                if sku or term
                else question
            ),
        )

    return None


def resolve_inventory_before_generate(
    *,
    question: str,
    slots: InventoryDraftSlotsOutput,
    executor: SqlExecutor | None,
    tenant_id: str | None,
) -> dict[str, Any] | None:
    """Return graph patch to stop with clarify, or None to continue."""
    from app.graph.draft_entity_resolution_common import SqlExecutorError
    doc_type = slots.doc_type
    doc_label = _DOC_LABEL_VI.get(doc_type, doc_type)
    term = _product_term_from_slots(slots)
    qty = slots.quantity
    products = search_products(executor, tenant_id=tenant_id, term=term) if term else []

    if doc_type == "stock_dispatch":
        if not term:
            return pack_clarify_state(
                question=question,
                intro=(
                    f"Để tạo **{doc_label}**, cần biết **sản phẩm** (tên hoặc mã SKU) và **số lượng** xuất."
                ),
                issues=[
                    DomainIssue(
                        type="missing_slot",
                        user_text=question,
                        canonical_vi="Thiếu tên/mã sản phẩm",
                        severity="block",
                    )
                ],
                questions=[
                    "Bạn muốn xuất sản phẩm nào? (ví dụ: máy tính, SKU-LAP-01)",
                    "Số lượng xuất là bao nhiêu?",
                ],
            )
        if not products:
            return pack_clarify_state(
                question=question,
                intro=(
                    f"Chưa tìm thấy sản phẩm nào khớp «{term}» trong danh mục / tồn kho.\n\n"
                    "Kiểm tra lại tên hoặc mã SKU, hoặc tạo sản phẩm trong **Danh mục** trước khi xuất kho."
                ),
                issues=[
                    DomainIssue(
                        type="unknown_entity",
                        user_text=term,
                        canonical_vi="Không có sản phẩm khớp trong DB",
                        severity="block",
                    )
                ],
                questions=[
                    "Gửi lại kèm **mã SKU chính xác** nếu sản phẩm đã có trong hệ thống.",
                ],
            )
        dispatch_patch = _resolve_stock_dispatch(
            question=question,
            doc_label=doc_label,
            term=term,
            qty=qty,
            products=products,
            slots=slots,
        )
        if dispatch_patch is not None:
            return dispatch_patch

    # stock_receipt
    if term and not products:
        return pack_clarify_state(
            question=question,
            intro=(
                f"Chưa tìm thấy sản phẩm «{term}» trong hệ thống.\n\n"
                f"Để tạo **{doc_label}**, cần SKU đã có trong **Danh mục**, "
                "hoặc tạo sản phẩm mới trước (menu Danh mục → Sản phẩm)."
            ),
            issues=[
                DomainIssue(
                    type="unknown_entity",
                    user_text=term,
                    canonical_vi="Sản phẩm chưa có trong DB",
                    severity="block",
                )
            ],
            questions=[
                "Bạn có **mã SKU** chính xác không?",
                "Hay cần **thêm sản phẩm mới** vào danh mục trước?",
            ],
        )

    if len(products) > 1:
        opts = _format_product_options(products)
        return pack_clarify_state(
            question=question,
            intro=(
                f"Có **{len(products)}** sản phẩm khớp «{term}». Chọn một dòng để nhập kho:\n\n{opts}"
            ),
            issues=[
                DomainIssue(
                    type="missing_slot",
                    user_text=term,
                    canonical_vi="Nhiều SKU khớp — cần chọn một",
                    severity="block",
                )
            ],
            questions=[
                "Gửi lại kèm **mã SKU** (ví dụ: LAPTOP-001) bạn muốn nhập.",
                "Nêu thêm **nhà cung cấp** (tên hoặc mã NCC) nếu chưa có trong câu.",
            ],
            suggested_rewrite=f"Tạo phiếu nhập kho SKU {products[0].get('sku_code')} từ NCC …",
        )

    if not _supplier_term_from_slots(slots):
        active: list[dict[str, Any]] = []
        if executor:
            try:
                active = _rows_from_result(
                    executor.execute(
                        """
SELECT s.supplier_code, s.name
FROM suppliers s
WHERE s.status = 'Active'
ORDER BY s.name ASC
LIMIT 5
""".strip(),
                        tenant_id=tenant_id,
                    ),
                )
            except Exception:
                active = []

        prod_line = ""
        if len(products) == 1:
            p = products[0]
            prod_line = (
                f"\n\nSản phẩm đã khớp: **{p.get('sku_code')}** — {p.get('name')}."
            )
        sup_block = ""
        if active:
            sup_block = "\n\nMột số NCC đang hoạt động:\n" + _format_supplier_options(active)
        return pack_clarify_state(
            question=question,
            intro=(
                f"Để tạo **{doc_label}** cần thêm **nhà cung cấp** (tên hoặc mã NCC đã có trong hệ thống)."
                f"{prod_line}{sup_block}"
            ),
            issues=[
                DomainIssue(
                    type="missing_slot",
                    user_text="nhà cung cấp",
                    canonical_vi="Thiếu nhà cung cấp (supplierName / supplierCode)",
                    severity="block",
                )
            ],
            questions=[
                "Nhà cung cấp của lô hàng này là ai? (tên hoặc mã NCC)",
                "Giá vốn / số lượng nhập nếu bạn đã biết?",
            ],
            suggested_rewrite=(
                f"Tạo phiếu nhập kho SKU {products[0].get('sku_code')} từ NCC <tên hoặc mã>"
                if products
                else "Tạo phiếu nhập kho từ NCC …, SKU …"
            ),
        )

    sup_term = _supplier_term_from_slots(slots)
    if sup_term:
        suppliers = search_suppliers(executor, tenant_id=tenant_id, term=sup_term)
        if not suppliers:
            return pack_clarify_state(
                question=question,
                intro=(
                    f"Không tìm thấy nhà cung cấp «{sup_term}» trong hệ thống.\n\n"
                    "Tạo NCC trong **Danh mục → Nhà cung cấp** hoặc dùng đúng **mã/tên** đã có."
                ),
                issues=[
                    DomainIssue(
                        type="unknown_entity",
                        user_text=sup_term,
                        canonical_vi="NCC không có trong DB",
                        severity="block",
                    )
                ],
                questions=["Cho biết **mã NCC** (supplierCode) hoặc tên chính xác."],
            )
        if len(suppliers) > 1:
            return pack_clarify_state(
                question=question,
                intro=f"Có {len(suppliers)} NCC khớp «{sup_term}»:\n\n"
                + _format_supplier_options(suppliers),
                issues=[
                    DomainIssue(
                        type="missing_slot",
                        user_text=sup_term,
                        canonical_vi="Chọn một NCC",
                        severity="block",
                    )
                ],
                questions=["Bạn muốn nhập từ NCC nào? (mã hoặc tên)"],
            )

    if doc_type == "stock_receipt":
        receipt_patch = _resolve_stock_receipt_before_generate(
            question=question,
            doc_label=doc_label,
            slots=slots,
            products=_narrow_products_by_sku(products, slots) if products else products,
            term=term,
            qty=qty,
        )
        if receipt_patch is not None:
            return receipt_patch

    return None
