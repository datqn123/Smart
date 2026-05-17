"""Column registry and validation for AI inventory document drafts (stock receipt v1)."""

from __future__ import annotations

import re
from datetime import date
from typing import Any, Literal

InventoryDocType = Literal["stock_receipt"]

MAX_INVENTORY_DRAFT_LINES = 20

RECEIPT_HEADER_KEYS = frozenset(
    {"supplierName", "supplierCode", "receiptDate", "invoiceNumber", "notes", "saveMode"}
)

RECEIPT_LINE_COLUMNS: list[dict[str, Any]] = [
    {"key": "skuCode", "label": "Mã SKU", "type": "string", "required": True},
    {"key": "productName", "label": "Tên SP", "type": "string", "required": False},
    {"key": "quantity", "label": "Số lượng", "type": "number", "required": True},
    {"key": "costPrice", "label": "Giá vốn", "type": "number", "required": True},
    {"key": "batchNumber", "label": "Số lô", "type": "string", "required": False},
    {"key": "expiryDate", "label": "HSD", "type": "string", "required": False},
]

RECEIPT_LINE_REQUIRED = ["skuCode", "quantity", "costPrice"]

_LINE_VALUE_ALIASES: dict[str, str] = {
    "sku": "skuCode",
    "ma_sku": "skuCode",
    "ten": "productName",
    "ten_sp": "productName",
    "so_luong": "quantity",
    "qty": "quantity",
    "gia_von": "costPrice",
    "cost": "costPrice",
    "lo": "batchNumber",
    "batch": "batchNumber",
    "hsd": "expiryDate",
    "expiry": "expiryDate",
}


def default_line_columns(doc_type: str) -> list[dict[str, Any]]:
    if doc_type == "stock_receipt":
        return list(RECEIPT_LINE_COLUMNS)
    return list(RECEIPT_LINE_COLUMNS)


def default_receipt_header() -> dict[str, Any]:
    return {
        "supplierName": "",
        "supplierCode": "",
        "receiptDate": date.today().isoformat(),
        "invoiceNumber": "",
        "notes": "",
        "saveMode": "draft",
    }


def _canonicalize_line_values(values: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in values.items():
        if v is None:
            continue
        key = _LINE_VALUE_ALIASES.get(k, k)
        if key not in out or out[key] in (None, ""):
            out[key] = v
    return out


def _merge_line(line: dict[str, Any], index: int) -> tuple[str, dict[str, Any]]:
    line_id = str(line.get("lineId") or f"l{index + 1}")
    values: dict[str, Any] = {}
    if isinstance(line.get("values"), dict):
        values.update(line["values"])
    for k, v in line.items():
        if k in ("lineId", "values") or v is None:
            continue
        values[k] = v
    return line_id, _canonicalize_line_values(values)


def _parse_quantity_from_prompt(prompt: str) -> int | None:
    if not prompt:
        return None
    m = re.search(r"(\d+)\s*(?:cái|chiếc|sp|sản phẩm|máy|hộp|thùng)?", prompt, re.IGNORECASE)
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            return None
    return None


def _parse_theme(prompt: str) -> str:
    if not prompt:
        return "Hàng"
    m = re.search(r"(máy tính|điện tử|thực phẩm|quần áo|gia dụng)", prompt, re.IGNORECASE)
    if m:
        return m.group(1).strip().title()
    return "Hàng"


def enrich_receipt_lines(
    lines: list[dict[str, Any]],
    *,
    user_prompt: str = "",
    header: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    theme = _parse_theme(user_prompt)
    qty_hint = _parse_quantity_from_prompt(user_prompt)
    out: list[dict[str, Any]] = []
    for i, row in enumerate(lines):
        line_id, values = _merge_line(row, i)
        idx = i + 1
        if not values.get("skuCode") or not str(values.get("skuCode", "")).strip():
            slug = re.sub(r"[^A-Za-z0-9]+", "-", theme.upper())[:10].strip("-") or "SP"
            values["skuCode"] = f"{slug}-{idx:03d}"
        if not values.get("productName") or not str(values.get("productName", "")).strip():
            values["productName"] = f"{theme} {idx}"
        if values.get("quantity") is None or values.get("quantity") == "":
            values["quantity"] = qty_hint if qty_hint is not None and i == 0 else 1
        if values.get("costPrice") is None or values.get("costPrice") == "":
            values["costPrice"] = 0
        out.append({"lineId": line_id, "values": values})
    return out


def enrich_receipt_header(header: dict[str, Any], *, user_prompt: str = "") -> dict[str, Any]:
    h = {**default_receipt_header(), **{k: v for k, v in header.items() if k in RECEIPT_HEADER_KEYS}}
    if not h.get("receiptDate"):
        h["receiptDate"] = date.today().isoformat()
    if not h.get("saveMode"):
        h["saveMode"] = "draft"
    if not h.get("supplierName") and not h.get("supplierCode"):
        m = re.search(r"(?:từ|ncc|nhà cung cấp)\s+([^\d,]+)", user_prompt, re.IGNORECASE)
        if m:
            h["supplierName"] = m.group(1).strip()[:120]
    return h


def validate_receipt_draft(header: dict[str, Any], lines: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    if not lines:
        issues.append("Phải có ít nhất một dòng hàng")
    if len(lines) > MAX_INVENTORY_DRAFT_LINES:
        issues.append(f"Tối đa {MAX_INVENTORY_DRAFT_LINES} dòng")
    if not (header.get("supplierName") or header.get("supplierCode")):
        issues.append("Thiếu nhà cung cấp (supplierName hoặc supplierCode)")
    rd = header.get("receiptDate")
    if not rd or not str(rd).strip():
        issues.append("Thiếu receiptDate")
    save_mode = str(header.get("saveMode") or "draft").lower()
    if save_mode not in ("draft", "pending"):
        issues.append("saveMode phải là draft hoặc pending")
    batch_keys: set[str] = set()
    for i, line in enumerate(lines):
        values = line.get("values") if isinstance(line.get("values"), dict) else line
        if not isinstance(values, dict):
            issues.append(f"Dòng {i + 1}: thiếu values")
            continue
        for key in RECEIPT_LINE_REQUIRED:
            val = values.get(key)
            if val is None or (isinstance(val, str) and not val.strip()):
                issues.append(f"Dòng {i + 1}: thiếu {key}")
        qty = values.get("quantity")
        if qty is not None and int(qty) <= 0:
            issues.append(f"Dòng {i + 1}: quantity phải > 0")
        sku = values.get("skuCode")
        batch = values.get("batchNumber")
        if sku and batch:
            bk = f"{sku}|{batch}"
            if bk in batch_keys:
                issues.append(f"Dòng {i + 1}: trùng lô SKU+batchNumber")
            batch_keys.add(bk)
    return issues


def normalize_lines(raw_lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for i, row in enumerate(raw_lines[:MAX_INVENTORY_DRAFT_LINES]):
        line_id, values = _merge_line(row, i)
        out.append({"lineId": line_id, "values": values})
    return out
