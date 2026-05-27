"""Common helpers and DB lookup utilities for inventory and catalog draft resolution.
"""

from __future__ import annotations

import logging
import re
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
) -> tuple[list[dict[str, Any]], str | None]:
    """Return (rows, error). error is set when DB lookup failed (not empty result)."""
    needle = _escape_ilike(term)
    if not executor or not needle:
        return [], None
    pattern = f"%{needle}%"
    sql = f"""
SELECT c.id, c.category_code, c.name, c.status
FROM categories c
WHERE (c.name ILIKE '{pattern}' OR c.category_code ILIKE '{pattern}')
  AND c.status = 'Active'
  AND c.deleted_at IS NULL
ORDER BY c.name ASC
LIMIT {int(limit)}
""".strip()
    try:
        return _rows_from_result(executor.execute(sql, tenant_id=tenant_id)), None
    except (SqlExecutorError, ValueError, TypeError) as exc:
        logger.warning("category search failed: %s", exc)
        return [], "upstream"


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


def _extract_sql_from_text(text: str) -> str:
    text = text.strip()
    sql = text
    m = re.search(r"```sql\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    if m:
        sql = m.group(1).strip()
    else:
        m = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL)
        if m:
            sql = m.group(1).strip()
    return sql.rstrip(';').strip()


def generate_sql_for_draft_lookup(
    executor: SqlExecutor | None,
    *,
    entity_type: str,
    question: str,
    tenant_id: str | None,
    llm_registry: Any,
    settings: Any,
) -> list[dict[str, Any]]:
    if not executor or not llm_registry:
        return []
    
    schema_prompt = """
Các bảng trong cơ sở dữ liệu:
1. **products** (sản phẩm):
   - id: integer (primary key)
   - sku_code: character varying (mã SKU độc nhất)
   - barcode: character varying
   - name: character varying (tên sản phẩm)
   - description: text
   - status: character varying ('Active', 'Inactive')
   - category_id: integer (foreign key tham chiếu categories.id)
   
2. **categories** (danh mục):
   - id: integer (primary key)
   - category_code: character varying (mã danh mục)
   - name: character varying (tên danh mục)
   - status: character varying ('Active', 'Inactive')
   - parent_id: integer (danh mục cha)
   - deleted_at: timestamp

3. **suppliers** (nhà cung cấp):
   - id: integer (primary key)
   - supplier_code: character varying (mã NCC)
   - name: character varying (tên nhà cung cấp)
   - contact_person: character varying
   - phone: character varying
   - email: character varying
   - address: text
   - tax_code: character varying
   - status: character varying ('Active', 'Inactive')

4. **customers** (khách hàng):
   - id: integer (primary key)
   - customer_code: character varying (mã khách hàng)
   - name: character varying
   - phone: character varying
   - email: character varying
   - address: text
   - status: character varying ('Active', 'Inactive')
   - deleted_at: timestamp

5. **stockreceipts** (phiếu nhập kho):
   - id: integer (primary key)
   - approved_at: timestamp (ngày giờ duyệt, NULL nghĩa là chưa duyệt)
   - supplier_id: integer (foreign key tham chiếu suppliers.id)
   - status: character varying ('Draft', 'Pending', 'Approved', 'Rejected')

6. **productunits** (đơn vị sản phẩm):
   - id: integer
   - product_id: integer (foreign key tham chiếu products.id)
   - unit_name: character varying
   - is_base_unit: boolean (chỉ lọc is_base_unit = TRUE để lấy đơn vị chính)

7. **productpricehistory** (lịch sử giá sản phẩm):
   - product_id: integer
   - unit_id: integer
   - cost_price: numeric (giá vốn)
   - sale_price: numeric (giá bán)
   - effective_date: date (ngày áp dụng)
"""

    system_prompt = """Bạn là chuyên gia sinh SQL cho hệ thống ERP.
Nhiệm vụ của bạn: Chỉ ra một câu SQL SELECT duy nhất để lấy thông tin thực tế từ database đáp ứng câu hỏi của người dùng.
Quy tắc:
1. Chỉ trả về một câu lệnh SQL SELECT duy nhất bên trong thẻ ```sql ... ```. Tuyệt đối không giải thích hay thêm text nào khác.
2. Không sử dụng các bảng khác ngoài danh sách được cung cấp.
3. Chú ý các điều kiện lọc trạng thái (ví dụ: `status <> 'Inactive'` hoặc `deleted_at IS NULL`).
4. Nếu người dùng muốn lọc theo phiếu nhập kho chưa duyệt, hãy kiểm tra điều kiện `approved_at IS NULL` hoặc `status <> 'Approved'` của bảng `stockreceipts`.
5. Đảm bảo câu SQL tối ưu, chính xác và sử dụng INNER JOIN / LEFT JOIN thích hợp.
"""

    try:
        try:
            client = llm_registry.get("sql_gen")
        except KeyError:
            try:
                client = llm_registry.get("intent")
            except KeyError:
                client = llm_registry.get("default")
    except Exception as exc:
        logger.warning("Failed to get LLM client for draft lookup: %s", exc)
        return []

    prior_sql = None
    prior_error = None
    
    # AI Self-Healing loop: thử tối đa 3 lần
    for attempt in range(1, 4):
        if attempt == 1:
            user_prompt = f"""
{schema_prompt}

Hãy sinh câu SQL SELECT để lấy các bản ghi thuộc thực thể **{entity_type}** đáp ứng yêu cầu dưới đây:
Yêu cầu người dùng: "{question}"

Chú ý cột cần SELECT cho từng thực thể:
- Nếu thực thể là `product`, bạn phải SELECT các trường: `p.id, p.sku_code, p.name, c.name AS category_name, c.category_code, pu.unit_name, pph.cost_price, pph.sale_price, p.barcode, p.status` và JOIN với `categories c`, `productunits pu` (lọc is_base_unit = TRUE), và `productpricehistory pph` phù hợp (sử dụng DISTINCT ON hoặc LATERAL để lấy giá mới nhất).
- Nếu thực thể là `supplier`, bạn phải SELECT các trường: `s.id, s.supplier_code, s.name, s.contact_person, s.phone, s.email, s.address, s.tax_code, s.status`.
- Nếu thực thể là `customer`, bạn phải SELECT các trường: `c.id, c.customer_code, c.name, c.phone, c.email, c.address, c.status`.
- Nếu thực thể là `category`, bạn phải SELECT các trường: `c.id, c.category_code, c.name, c.description, c.status, p.name AS parent_name, p.category_code AS parent_code`.
"""
        else:
            logger.info("AI Self-Healing SQL Draft Lookup - Lần thử %d/3...", attempt)
            user_prompt = f"""
{schema_prompt}

Câu SQL bạn sinh ra trước đó bị lỗi:
```sql
{prior_sql}
```

Lý do lỗi từ DB: "{prior_error}"

Nhiệm vụ: Hãy phân tích kỹ lý do lỗi và sửa lại câu lệnh SQL trên.
Yêu cầu:
1. Khắc phục hoàn toàn lỗi cú pháp hoặc logic được nêu.
2. Đảm bảo SELECT đúng các trường tương ứng với thực thể **{entity_type}** như chỉ thị ban đầu.
3. Chỉ trả về một câu lệnh SQL SELECT duy nhất bên trong thẻ ```sql ... ```. Tuyệt đối không giải thích hay thêm text nào khác.
"""

        try:
            sql_res = client.invoke_text(user_prompt, system=system_prompt)
            sql = _extract_sql_from_text(sql_res)
            prior_sql = sql
            
            logger.info("Draft Lookup SQL (attempt %d/3): %s", attempt, sql)
            
            result = executor.execute(sql, tenant_id=tenant_id)
            raw_rows = _rows_from_result(result)
            
            mapped = []
            for r in raw_rows:
                if entity_type == "product":
                    mapped.append({
                        "skuCode": r.get("sku_code") or r.get("skuCode"),
                        "name": r.get("name"),
                        "categoryName": r.get("category_name") or r.get("categoryName"),
                        "categoryCode": r.get("category_code") or r.get("categoryCode"),
                        "baseUnitName": r.get("unit_name") or r.get("base_unit_name") or r.get("baseUnitName") or "Chiếc",
                        "costPrice": r.get("cost_price") or r.get("costPrice") or 0,
                        "salePrice": r.get("sale_price") or r.get("salePrice") or 0,
                        "barcode": r.get("barcode"),
                        "status": r.get("status") or "Active",
                    })
                elif entity_type == "supplier":
                    mapped.append({
                        "supplierCode": r.get("supplier_code") or r.get("supplierCode"),
                        "name": r.get("name"),
                        "contactPerson": r.get("contact_person") or r.get("contactPerson") or "",
                        "phone": r.get("phone") or "",
                        "email": r.get("email") or "",
                        "address": r.get("address") or "",
                        "taxCode": r.get("tax_code") or r.get("taxCode") or "",
                        "status": r.get("status") or "Active",
                    })
                elif entity_type == "customer":
                    mapped.append({
                        "customerCode": r.get("customer_code") or r.get("customerCode"),
                        "name": r.get("name"),
                        "phone": r.get("phone") or "",
                        "email": r.get("email") or "",
                        "address": r.get("address") or "",
                        "status": r.get("status") or "Active",
                    })
                elif entity_type == "category":
                    mapped.append({
                        "categoryCode": r.get("category_code") or r.get("categoryCode"),
                        "name": r.get("name"),
                        "description": r.get("description") or "",
                        "parentName": r.get("parent_name") or r.get("parentName") or "",
                        "parentCode": r.get("parent_code") or r.get("parentCode") or "",
                        "status": r.get("status") or "Active",
                    })
            
            logger.info("Draft Lookup SQL (attempt %d/3) executed successfully! Rows returned: %d", attempt, len(mapped))
            return mapped
            
        except Exception as exc:
            prior_error = str(exc)
            logger.warning("Draft Lookup SQL (attempt %d/3) failed: %s", attempt, prior_error)
            if attempt == 3:
                logger.error("Draft Lookup SQL failed after 3 attempts.")
                return []
                
    return []
