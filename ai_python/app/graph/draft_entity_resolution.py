"""DB lookup + rich clarify before catalog/inventory draft generation.

Slot values (product, NCC, quantity, doc_type) come from LLM via inventory_draft_slots.md /
catalog_draft_slots.md — not from Python regex intent parsing.
"""

from __future__ import annotations

import logging
from typing import Any

from app.graph.sql_executor import SqlExecutor, SqlExecutorError
from app.llm.schemas import (
    CatalogDraftSlotsOutput,
    DomainIssue,
    InventoryDraftSlotsOutput,
)

logger = logging.getLogger(__name__)

_DOC_LABEL_VI = {
    "stock_receipt": "phiếu nhập kho",
    "stock_dispatch": "phiếu xuất kho",
}
_CATALOG_LABEL_VI = {
    "product": "sản phẩm",
    "supplier": "nhà cung cấp",
    "category": "danh mục",
    "customer": "khách hàng",
}


def _strip_slot(value: str | None) -> str:
    return (value or "").strip()


def _product_term_from_slots(slots: InventoryDraftSlotsOutput | CatalogDraftSlotsOutput) -> str:
    sku = _strip_slot(getattr(slots, "product_sku", None))
    if sku:
        return sku
    return _strip_slot(getattr(slots, "product_query", None))


def _supplier_term_from_slots(slots: InventoryDraftSlotsOutput) -> str:
    code = _strip_slot(slots.supplier_code)
    if code:
        return code
    return _strip_slot(slots.supplier_query)


def _category_term_from_slots(slots: CatalogDraftSlotsOutput) -> str:
    code = _strip_slot(slots.category_code)
    if code:
        return code
    return _strip_slot(slots.category_query)


def _escape_ilike(term: str) -> str:
    return (term or "").replace("'", "''").strip()


def _rows_from_result(result: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(result, dict):
        return []
    rows = result.get("rows")
    return [r for r in rows if isinstance(r, dict)] if isinstance(rows, list) else []


def search_products(
    executor: SqlExecutor | None,
    *,
    tenant_id: str | None,
    term: str,
    limit: int = 8,
) -> list[dict[str, Any]]:
    needle = _escape_ilike(term)
    if not executor or not needle:
        return []
    pattern = f"%{needle}%"
    sql = f"""
SELECT p.id, p.sku_code, p.name, p.status,
       COALESCE(inv.qty, 0)::bigint AS stock_qty
FROM products p
LEFT JOIN (
  SELECT product_id, SUM(quantity)::bigint AS qty FROM inventory GROUP BY product_id
) inv ON inv.product_id = p.id
WHERE (p.name ILIKE '{pattern}' OR p.sku_code ILIKE '{pattern}' OR COALESCE(p.barcode, '') ILIKE '{pattern}')
  AND p.status <> 'Inactive'
ORDER BY stock_qty DESC, p.name ASC
LIMIT {int(limit)}
""".strip()
    try:
        return _rows_from_result(
            executor.execute(sql, tenant_id=tenant_id),
        )
    except (SqlExecutorError, ValueError, TypeError) as exc:
        logger.warning("product search failed: %s", exc)
        return []


def search_suppliers(
    executor: SqlExecutor | None,
    *,
    tenant_id: str | None,
    term: str,
    limit: int = 6,
) -> list[dict[str, Any]]:
    needle = _escape_ilike(term)
    if not executor or not needle:
        return []
    pattern = f"%{needle}%"
    sql = f"""
SELECT s.id, s.supplier_code, s.name, s.status
FROM suppliers s
WHERE (s.name ILIKE '{pattern}' OR s.supplier_code ILIKE '{pattern}')
  AND s.status = 'Active'
ORDER BY s.name ASC
LIMIT {int(limit)}
""".strip()
    try:
        return _rows_from_result(executor.execute(sql, tenant_id=tenant_id))
    except (SqlExecutorError, ValueError, TypeError) as exc:
        logger.warning("supplier search failed: %s", exc)
        return []


def search_categories(
    executor: SqlExecutor | None,
    *,
    tenant_id: str | None,
    term: str,
    limit: int = 6,
) -> list[dict[str, Any]]:
    needle = _escape_ilike(term)
    if not executor or not needle:
        return []
    pattern = f"%{needle}%"
    sql = f"""
SELECT c.id, c.code, c.name, c.status
FROM categories c
WHERE (c.name ILIKE '{pattern}' OR c.code ILIKE '{pattern}')
  AND c.status = 'Active'
ORDER BY c.name ASC
LIMIT {int(limit)}
""".strip()
    try:
        return _rows_from_result(executor.execute(sql, tenant_id=tenant_id))
    except (SqlExecutorError, ValueError, TypeError) as exc:
        logger.warning("category search failed: %s", exc)
        return []


def _product_stock_qty(product: dict[str, Any]) -> int:
    try:
        return int(product.get("stock_qty", product.get("current_stock", 0)) or 0)
    except (TypeError, ValueError):
        return 0


def _narrow_products_by_sku(
    products: list[dict[str, Any]],
    slots: InventoryDraftSlotsOutput,
) -> list[dict[str, Any]]:
    sku = _strip_slot(slots.product_sku)
    if not sku or not products:
        return products
    key = sku.upper()
    exact = [p for p in products if str(p.get("sku_code") or "").upper() == key]
    if exact:
        return exact
    partial = [p for p in products if key in str(p.get("sku_code") or "").upper()]
    return partial or products


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


def _format_product_options(products: list[dict[str, Any]], *, max_items: int = 8) -> str:
    lines: list[str] = []
    for i, p in enumerate(products[:max_items], start=1):
        sku = str(p.get("sku_code") or p.get("skuCode") or "—")
        name = str(p.get("name") or "—")
        stock = p.get("stock_qty", p.get("current_stock", 0))
        lines.append(f"{i}. **{sku}** — {name} (tồn kho: {stock})")
    if len(products) > max_items:
        lines.append(f"… và {len(products) - max_items} sản phẩm khác.")
    return "\n".join(lines)


def _format_supplier_options(suppliers: list[dict[str, Any]], *, max_items: int = 6) -> str:
    lines: list[str] = []
    for i, s in enumerate(suppliers[:max_items], start=1):
        code = str(s.get("supplier_code") or s.get("supplierCode") or "—")
        name = str(s.get("name") or "—")
        lines.append(f"{i}. **{code}** — {name}")
    return "\n".join(lines)


def pack_clarify_state(
    *,
    question: str,
    intro: str,
    issues: list[DomainIssue],
    questions: list[str],
    suggested_rewrite: str = "",
) -> dict[str, Any]:
    suggested = (suggested_rewrite or "").strip()
    clarify_sse = {
        "questions": questions,
        "issues": [i.model_dump() for i in issues],
        "guideRefs": ["05_inventory.md"],
        "originalQuestion": question,
        "suggestedRewrite": suggested,
        "suggestedNormalized": suggested,
        "matchedModules": ["inventory"],
        "assistantIntro": intro.strip(),
    }
    body = intro.strip()
    if questions:
        body += "\n\n" + "\n".join(f"• {q}" for q in questions)
    return {
        "final_answer": body,
        "messages": [],  # caller adds AIMessage
        "domain_clarify_sse": clarify_sse,
        "error_payload": {"code": "DRAFT_NEEDS_CLARIFY", "message": body[:500]},
    }


def resolve_inventory_before_generate(
    *,
    question: str,
    slots: InventoryDraftSlotsOutput,
    executor: SqlExecutor | None,
    tenant_id: str | None,
) -> dict[str, Any] | None:
    """Return graph patch to stop with clarify, or None to continue."""
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
            except (SqlExecutorError, ValueError, TypeError):
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


def resolve_catalog_before_generate(
    *,
    question: str,
    slots: CatalogDraftSlotsOutput,
    executor: SqlExecutor | None,
    tenant_id: str | None,
) -> dict[str, Any] | None:
    entity_type = slots.entity_type
    label = _CATALOG_LABEL_VI.get(entity_type, entity_type)
    term = _product_term_from_slots(slots)

    if entity_type == "product" and term:
        hits = search_products(executor, tenant_id=tenant_id, term=term)
        if len(hits) > 1:
            opts = _format_product_options(hits)
            return pack_clarify_state(
                question=question,
                intro=(
                    f"Đã có **{len(hits)}** sản phẩm khớp «{term}» — có thể bạn muốn **cập nhật** "
                    f"thay vì tạo mới {label}:\n\n{opts}"
                ),
                issues=[
                    DomainIssue(
                        type="ambiguous_module",
                        user_text=term,
                        canonical_vi="Sản phẩm có thể đã tồn tại",
                        severity="warn",
                    )
                ],
                questions=[
                    "Bạn muốn **thêm mới** hay chỉnh sửa sản phẩm đã có?",
                    "Nếu thêm mới, dùng SKU khác hoặc nêu rõ tên khác biệt.",
                ],
                suggested_rewrite=question,
            )
        if len(hits) == 1:
            p = hits[0]
            return pack_clarify_state(
                question=question,
                intro=(
                    f"Sản phẩm **{p.get('sku_code')}** — {p.get('name')} **đã có** trong hệ thống "
                    f"(tồn: {p.get('stock_qty', 0)}).\n\n"
                    "Nếu cần chỉnh sửa, mở **Danh mục → Sản phẩm**. "
                    "Nếu vẫn muốn tạo bản ghi mới, hãy nêu **SKU khác**."
                ),
                issues=[
                    DomainIssue(
                        type="wrong_workflow",
                        user_text=term,
                        canonical_vi="SKU đã tồn tại",
                        severity="block",
                    )
                ],
                questions=["Bạn có chắc muốn tạo sản phẩm trùng tên/mã không?"],
                suggested_rewrite=question,
            )
        cat_term = _category_term_from_slots(slots)
        if cat_term:
            cats = search_categories(executor, tenant_id=tenant_id, term=cat_term)
            if cat_term and not cats:
                return pack_clarify_state(
                    question=question,
                    intro=(
                        f"Không tìm thấy danh mục «{cat_term}» trong DB. "
                        f"Cần **mã hoặc tên danh mục** đã có, hoặc tạo danh mục trước."
                    ),
                    issues=[
                        DomainIssue(
                            type="unknown_entity",
                            user_text=cat_term,
                            canonical_vi="Danh mục chưa có",
                            severity="block",
                        )
                    ],
                    questions=["Cho biết **mã danh mục** (categoryCode) hoặc tên chính xác."],
                )
            if len(cats) > 1:
                lines = [
                    f"{i}. **{c.get('code')}** — {c.get('name')}"
                    for i, c in enumerate(cats[:6], start=1)
                ]
                return pack_clarify_state(
                    question=question,
                    intro="Có nhiều danh mục khớp:\n\n" + "\n".join(lines),
                    issues=[
                        DomainIssue(
                            type="missing_slot",
                            user_text=cat_term,
                            canonical_vi="Chọn danh mục",
                            severity="block",
                        )
                    ],
                    questions=["Bạn muốn gán sản phẩm vào danh mục nào? (mã danh mục)"],
                )

    if entity_type == "supplier":
        sup_term = _strip_slot(slots.supplier_code) or _strip_slot(slots.supplier_query)
        if sup_term:
            hits = search_suppliers(executor, tenant_id=tenant_id, term=sup_term)
            if len(hits) == 1:
                s = hits[0]
                return pack_clarify_state(
                    question=question,
                    intro=(
                        f"NCC **{s.get('supplier_code')}** — {s.get('name')} đã tồn tại. "
                        "Mở **Danh mục → Nhà cung cấp** để chỉnh sửa."
                    ),
                    issues=[
                        DomainIssue(
                            type="wrong_workflow",
                            user_text=sup_term,
                            canonical_vi="NCC đã có",
                            severity="block",
                        )
                    ],
                    questions=["Bạn có muốn tạo NCC mới với mã khác không?"],
                )

    return None
