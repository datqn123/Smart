"""Column registry and validation for AI catalog draft rows."""

from __future__ import annotations

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


def normalize_rows(raw_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for i, row in enumerate(raw_rows[:MAX_CATALOG_DRAFT_ROWS]):
        if "values" in row and isinstance(row["values"], dict):
            values = dict(row["values"])
            row_id = str(row.get("rowId") or f"r{i + 1}")
        else:
            values = dict(row)
            row_id = f"r{i + 1}"
        out.append({"rowId": row_id, "values": values})
    return out
