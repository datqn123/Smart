"""Column registry and validation for AI catalog draft rows."""

from __future__ import annotations

import re
from typing import Any, Literal

CatalogEntityType = Literal["product", "category", "supplier", "customer"]

MAX_CATALOG_DRAFT_ROWS = 50

ENTITY_COLUMNS: dict[str, list[dict[str, Any]]] = {
    "product": [
        {"key": "skuCode", "label": "Mã SKU", "type": "string", "required": True},
        {"key": "name", "label": "Tên SP", "type": "string", "required": True},
        {"key": "categoryName", "label": "Danh mục", "type": "string", "required": False},
        {"key": "baseUnitName", "label": "Đơn vị", "type": "string", "required": True},
        {"key": "costPrice", "label": "Giá vốn", "type": "number", "required": True},
        {"key": "salePrice", "label": "Giá bán", "type": "number", "required": True},
        {"key": "barcode", "label": "Barcode", "type": "string", "required": False},
        {"key": "status", "label": "Trạng thái", "type": "enum", "required": False, "options": ["Active", "Inactive"]},
    ],
    "category": [
        {"key": "categoryCode", "label": "Mã DM", "type": "string", "required": True},
        {"key": "name", "label": "Tên danh mục", "type": "string", "required": True},
        {"key": "parentName", "label": "Danh mục cha", "type": "string", "required": False},
        {"key": "description", "label": "Mô tả", "type": "string", "required": False},
        {"key": "sortOrder", "label": "Thứ tự", "type": "number", "required": False},
        {"key": "status", "label": "Trạng thái", "type": "enum", "required": False, "options": ["Active", "Inactive"]},
    ],
    "supplier": [
        {"key": "supplierCode", "label": "Mã NCC", "type": "string", "required": True},
        {"key": "name", "label": "Tên NCC", "type": "string", "required": True},
        {"key": "contactPerson", "label": "Người liên hệ", "type": "string", "required": True},
        {"key": "phone", "label": "SĐT", "type": "string", "required": True},
        {"key": "email", "label": "Email", "type": "string", "required": False},
        {"key": "address", "label": "Địa chỉ", "type": "string", "required": False},
        {"key": "taxCode", "label": "MST", "type": "string", "required": False},
        {"key": "status", "label": "Trạng thái", "type": "enum", "required": False, "options": ["Active", "Inactive"]},
    ],
    "customer": [
        {"key": "customerCode", "label": "Mã KH", "type": "string", "required": True},
        {"key": "name", "label": "Tên KH", "type": "string", "required": True},
        {"key": "phone", "label": "SĐT", "type": "string", "required": True},
        {"key": "email", "label": "Email", "type": "string", "required": False},
        {"key": "address", "label": "Địa chỉ", "type": "string", "required": False},
        {"key": "status", "label": "Trạng thái", "type": "enum", "required": False, "options": ["Active", "Inactive"]},
    ],
}

REQUIRED_KEYS: dict[str, list[str]] = {
    entity: [c["key"] for c in cols if c.get("required")]
    for entity, cols in ENTITY_COLUMNS.items()
}


def default_columns(entity_type: str) -> list[dict[str, Any]]:
    return list(ENTITY_COLUMNS.get(entity_type, ENTITY_COLUMNS["product"]))


def validate_draft_rows(entity_type: str, rows: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    if len(rows) > MAX_CATALOG_DRAFT_ROWS:
        issues.append(f"Tối đa {MAX_CATALOG_DRAFT_ROWS} dòng")
    required = REQUIRED_KEYS.get(entity_type, [])
    for i, row in enumerate(rows):
        values = row.get("values") if isinstance(row.get("values"), dict) else row
        if not isinstance(values, dict):
            issues.append(f"Dòng {i + 1}: thiếu values")
            continue
        for key in required:
            val = values.get(key)
            if val is None or (isinstance(val, str) and not val.strip()):
                issues.append(f"Dòng {i + 1}: thiếu {key}")
    return issues


_ROW_META_KEYS = frozenset({"rowId", "values"})

# Aliases LLM may use instead of canonical column keys.
_VALUE_ALIASES: dict[str, str] = {
    "ten": "name",
    "ten_sp": "name",
    "ten_san_pham": "name",
    "product_name": "name",
    "productName": "name",
    "sku": "skuCode",
    "ma_sku": "skuCode",
    "ma": "skuCode",
    "category": "categoryName",
    "danh_muc": "categoryName",
    "category_name": "categoryName",
    "gia_ban": "salePrice",
    "gia": "salePrice",
    "price": "salePrice",
    "don_gia": "salePrice",
    "gia_von": "costPrice",
    "cost": "costPrice",
    "don_vi": "baseUnitName",
    "unit": "baseUnitName",
    "ma_danh_muc": "categoryCode",
    "ma_ncc": "supplierCode",
    "ma_kh": "customerCode",
    "sdt": "phone",
    "phone_number": "phone",
}


def _canonicalize_value_keys(values: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in values.items():
        if v is None:
            continue
        key = _VALUE_ALIASES.get(k, k)
        if key not in out or out[key] in (None, ""):
            out[key] = v
    return out


def _merge_row_dict(row: dict[str, Any], index: int) -> tuple[str, dict[str, Any]]:
    row_id = str(row.get("rowId") or f"r{index + 1}")
    values: dict[str, Any] = {}
    if isinstance(row.get("values"), dict):
        values.update(row["values"])
    for k, v in row.items():
        if k in _ROW_META_KEYS or v is None:
            continue
        values[k] = v
    return row_id, _canonicalize_value_keys(values)


def _parse_price_from_prompt(prompt: str) -> int | None:
    if not prompt:
        return None
    m = re.search(r"(?:giá|gia|price)\s*[:=]?\s*([\d.,]+)", prompt, re.IGNORECASE)
    if not m:
        m = re.search(r"([\d]{4,})(?:\s*(?:đ|vnd|dong))?", prompt, re.IGNORECASE)
    if not m:
        return None
    raw = m.group(1).replace(".", "").replace(",", "")
    try:
        return int(raw)
    except ValueError:
        return None


def _parse_product_theme(prompt: str) -> str:
    if not prompt:
        return "Sản phẩm"
    p = prompt.strip()
    m = re.search(
        r"sản\s*phẩm\s+([^\d,]+?)(?:\s+giá|\s+gía|\s+price|\s+\d|$)",
        p,
        re.IGNORECASE,
    )
    if m:
        return m.group(1).strip().title() or "Sản phẩm"
    m2 = re.search(r"(điện\s*tử|thực\s*phẩm|quần\s*áo|gia\s*dụng)", p, re.IGNORECASE)
    if m2:
        return m2.group(1).strip().title()
    return "Sản phẩm"


def enrich_catalog_draft_rows(
    entity_type: str,
    rows: list[dict[str, Any]],
    *,
    user_prompt: str = "",
) -> list[dict[str, Any]]:
    """Fill missing required fields so HITL table is usable when LLM output is partial."""
    theme = _parse_product_theme(user_prompt)
    price = _parse_price_from_prompt(user_prompt)
    required = REQUIRED_KEYS.get(entity_type, [])
    out: list[dict[str, Any]] = []

    for i, row in enumerate(rows):
        row_id, values = _merge_row_dict(row, i)
        idx = i + 1

        if entity_type == "product":
            if not values.get("name") or not str(values.get("name", "")).strip():
                values["name"] = f"{theme} {idx}"
            if not values.get("skuCode") or not str(values.get("skuCode", "")).strip():
                slug = re.sub(r"[^A-Za-z0-9]+", "-", theme.upper())[:12].strip("-") or "SP"
                values["skuCode"] = f"{slug}-{idx:03d}"
            if not values.get("baseUnitName") or not str(values.get("baseUnitName", "")).strip():
                values["baseUnitName"] = "Cái"
            sale = values.get("salePrice")
            cost = values.get("costPrice")
            if sale is None or sale == "":
                if price is not None:
                    values["salePrice"] = price
            if values.get("costPrice") is None or values.get("costPrice") == "":
                sp = values.get("salePrice")
                if isinstance(sp, (int, float)) and sp > 0:
                    values["costPrice"] = int(round(float(sp) * 0.8))
                elif price is not None:
                    values["costPrice"] = int(round(price * 0.8))
            if not values.get("categoryName") and theme != "Sản phẩm":
                values["categoryName"] = theme
            if not values.get("status"):
                values["status"] = "Active"
        elif entity_type == "category":
            if not values.get("name"):
                values["name"] = f"{theme} {idx}"
            if not values.get("categoryCode"):
                values["categoryCode"] = f"CAT-{idx:03d}"
            if not values.get("status"):
                values["status"] = "Active"
        elif entity_type == "supplier":
            if not values.get("name"):
                values["name"] = f"NCC {theme} {idx}"
            if not values.get("supplierCode"):
                values["supplierCode"] = f"NCC-{idx:03d}"
            if not values.get("contactPerson"):
                values["contactPerson"] = "Liên hệ"
            if not values.get("phone"):
                values["phone"] = f"090000{idx:04d}"
            if not values.get("status"):
                values["status"] = "Active"
        elif entity_type == "customer":
            if not values.get("name"):
                values["name"] = f"Khách {theme} {idx}"
            if not values.get("customerCode"):
                values["customerCode"] = f"KH-{idx:03d}"
            if not values.get("phone"):
                values["phone"] = f"091000{idx:04d}"
            if not values.get("status"):
                values["status"] = "Active"

        for key in required:
            if key not in values or values[key] is None or (
                isinstance(values[key], str) and not str(values[key]).strip()
            ):
                # Last resort for unknown gaps
                if entity_type == "product" and key in ("costPrice", "salePrice"):
                    values[key] = price if price is not None else 0

        out.append({"rowId": row_id, "values": values})
    return out


def normalize_rows(raw_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for i, row in enumerate(raw_rows[:MAX_CATALOG_DRAFT_ROWS]):
        row_id, values = _merge_row_dict(row, i)
        out.append({"rowId": row_id, "values": values})
    return out
