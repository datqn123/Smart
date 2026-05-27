"""Catalog-specific resolution logic using dynamic SQL and legacy fallbacks.
"""

from __future__ import annotations

import logging
from typing import Any

from app.graph.sql_executor import SqlExecutor
from app.llm.schemas import CatalogDraftSlotsOutput, DomainIssue
from app.graph.draft_entity_resolution_common import (
    _category_term_from_slots,
    _product_term_from_slots,
    _strip_slot,
    _rows_from_result,
    search_categories,
    search_products,
    search_suppliers,
    pack_clarify_state,
    generate_sql_for_draft_lookup,
    _CATALOG_LABEL_VI,
)

logger = logging.getLogger(__name__)


def get_products_with_prices(
    executor: SqlExecutor | None,
    *,
    tenant_id: str | None,
    category_id: int | None = None,
    product_ids: list[int] | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    if not executor:
        return []
    if not category_id and not product_ids:
        return []
    conds = []
    if category_id:
        conds.append(f"p.category_id = {int(category_id)}")
    if product_ids:
        ids_str = ",".join(str(int(x)) for x in product_ids)
        conds.append(f"p.id IN ({ids_str})")
    where_clause = " AND ".join(conds)
    sql = f"""
SELECT p.id, p.sku_code, p.barcode, p.name, p.category_id, c.name AS category_name, c.category_code,
       pu.unit_name AS base_unit_name,
       latest_pph.cost_price::bigint AS cost_price,
       latest_pph.sale_price::bigint AS sale_price,
       p.status
FROM products p
JOIN productunits pu ON pu.product_id = p.id AND pu.is_base_unit = TRUE
LEFT JOIN categories c ON c.id = p.category_id
LEFT JOIN LATERAL (
  SELECT pph.cost_price, pph.sale_price
  FROM productpricehistory pph
  WHERE pph.product_id = p.id AND pph.unit_id = pu.id AND pph.effective_date <= CURRENT_DATE
  ORDER BY pph.effective_date DESC, pph.id DESC
  LIMIT 1
) latest_pph ON TRUE
WHERE {where_clause} AND p.status <> 'Inactive'
ORDER BY p.sku_code ASC
LIMIT {int(limit)}
""".strip()
    try:
        raw = _rows_from_result(executor.execute(sql, tenant_id=tenant_id))
        out = []
        for r in raw:
            out.append({
                "skuCode": r.get("sku_code"),
                "name": r.get("name"),
                "categoryName": r.get("category_name"),
                "categoryCode": r.get("category_code"),
                "baseUnitName": r.get("base_unit_name") or "Chiếc",
                "costPrice": r.get("cost_price") or 0,
                "salePrice": r.get("sale_price") or 0,
                "barcode": r.get("barcode"),
                "status": r.get("status") or "Active",
            })
        return out
    except Exception as exc:
        logger.warning("get_products_with_prices failed: %s", exc)
        return []


def resolve_catalog_before_generate(
    *,
    question: str,
    slots: CatalogDraftSlotsOutput,
    executor: SqlExecutor | None,
    tenant_id: str | None,
    llm_registry: Any = None,
    settings: Any = None,
) -> dict[str, Any] | None:
    entity_type = slots.entity_type
    
    # Kịch bản 1: Có LLM Registry -> Sử dụng AI Sinh SQL động (Linh hoạt và chính xác)
    if llm_registry and question:
        existing = generate_sql_for_draft_lookup(
            executor,
            entity_type=entity_type,
            question=question,
            tenant_id=tenant_id,
            llm_registry=llm_registry,
            settings=settings,
        )
        if existing:
            return {"catalog_draft_existing_data": existing}
            
    # Kịch bản 2: Không có LLM Registry (Unit Tests) -> Fallback về logic static truyền thống
    label = _CATALOG_LABEL_VI.get(entity_type, entity_type)
    term = _product_term_from_slots(slots)

    if entity_type == "product":
        cat_term = _category_term_from_slots(slots)
        if cat_term:
            cats, cat_err = search_categories(executor, tenant_id=tenant_id, term=cat_term)
            if not cat_err and len(cats) == 1:
                cat_id = cats[0].get("id")
                if cat_id:
                    existing_prods = get_products_with_prices(executor, tenant_id=tenant_id, category_id=cat_id)
                    if existing_prods:
                        return {"catalog_draft_existing_data": existing_prods}
        if term:
            hits = search_products(executor, tenant_id=tenant_id, term=term)
            if hits:
                ids = [h["id"] for h in hits if h.get("id")]
                existing_prods = get_products_with_prices(executor, tenant_id=tenant_id, product_ids=ids)
                if existing_prods:
                    return {"catalog_draft_existing_data": existing_prods}
        cat_term = _category_term_from_slots(slots)
        if cat_term:
            cats, cat_err = search_categories(executor, tenant_id=tenant_id, term=cat_term)
            if cat_err:
                return pack_clarify_state(
                    question=question,
                    intro=(
                        "Không tra cứu được danh mục trong DB (lỗi hệ thống). "
                        "Vui lòng thử lại sau hoặc dùng **mã danh mục** (vd. CAT002)."
                    ),
                    issues=[
                        DomainIssue(
                            type="unknown_entity",
                            user_text=cat_term,
                            canonical_vi="Lỗi tra cứu danh mục",
                            severity="block",
                        )
                    ],
                    questions=["Thử lại với mã danh mục chính xác (categoryCode)."],
                )
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
                    f"{i}. **{c.get('category_code')}** — {c.get('name')}"
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
