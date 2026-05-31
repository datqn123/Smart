#!/usr/bin/env python3
"""Build erp_domain_index.json and guide chunks from docs/guides/GUID_ERP.md (Task112)."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_GUIDE = _REPO_ROOT / "docs" / "guides" / "GUID_ERP.md"
_OUT_DIR = Path(__file__).resolve().parents[1] / "app" / "data" / "erp"
_CHUNKS_DIR = _OUT_DIR / "guide_chunks"

_STATIC_MISNOMERS = [
    {
        "phrase_vi": "phiếu xuất khẩu",
        "canonical_vi": "phiếu xuất kho",
        "canonical_en": "Stock Dispatch",
        "module_id": "inventory_stock_dispatch",
        "note": "Hệ thống không có module xuất khẩu quốc tế",
    },
    {
        "phrase_vi": "xuất khẩu",
        "canonical_vi": "phiếu xuất kho",
        "canonical_en": "Stock Dispatch",
        "module_id": "inventory_stock_dispatch",
        "note": "Trong ERP thường là phiếu xuất kho (outbound), không phải export",
    },
    {
        "phrase_vi": "đơn hàng nhập khẩu",
        "canonical_vi": "phiếu nhập kho",
        "canonical_en": "Stock Receipt",
        "module_id": "inventory_stock_receipt",
        "note": "Không có đơn nhập khẩu — dùng phiếu nhập kho",
    },
    {
        "phrase_vi": "nhập khẩu",
        "canonical_vi": "phiếu nhập kho",
        "canonical_en": "Stock Receipt",
        "module_id": "inventory_stock_receipt",
        "note": "Trong ERP thường là phiếu nhập kho (inbound)",
    },
    {
        "phrase_vi": "bill xuất",
        "canonical_vi": "phiếu xuất kho",
        "canonical_en": "Stock Dispatch",
        "module_id": "inventory_stock_dispatch",
        "note": None,
    },
]

_GLOBAL_OUT_OF_SCOPE = [
    "wordpress",
    "woocommerce",
    "shopify",
    "excel macro",
    "google sheets",
    "facebook ads",
    "tiktok shop",
    "zalo pay api",
    "cài đặt windows",
    "máy in driver",
]

_AI_RULES_SUMMARY = [
    "SQL read-only: chỉ SELECT, không DDL/DML",
    "Chỉ truy vấn bảng trong allowlist",
    "Doanh thu/chi phí: ưu tiên financeledger",
    "Tăng tồn: duyệt phiếu nhập kho; giảm tồn: phiếu xuất Delivered hoặc kiểm kê",
    "Master catalog (product/category/supplier/customer) khác chứng từ kho (receipt/dispatch)",
]

_SECTION_MODULE_MAP: list[tuple[str, str, str, str]] = [
    (r"^## 1\.", "architecture", "Kiến trúc hệ thống", "Architecture Overview"),
    (r"^## 2\.", "permissions", "Phân quyền", "Permissions & Roles"),
    (r"^## 3\.", "auth_session", "Đăng nhập / phiên", "Login / Logout / Session"),
    (r"^## 4\.", "dashboard", "Dashboard", "Dashboard"),
    (r"^## 5\.", "inventory", "Quản lý kho", "Inventory Management"),
    (r"^## 6\.", "catalog", "Sản phẩm & danh mục", "Product Management"),
    (r"^## 7\.", "orders", "Đơn hàng", "Order Management"),
    (r"^## 8\.", "finance", "Dòng tiền / sổ cái", "Cash Flow Management"),
    (r"^## 9\.", "ai_chat", "Trợ lý AI", "AI Chat"),
    (r"^## 10\.", "settings", "Cài đặt hệ thống", "System Settings"),
    (r"^## 11\.", "notifications", "Thông báo", "Notifications"),
    (r"^## 12\.", "approvals", "Phê duyệt", "Approvals"),
    (r"^## 13\.", "reports", "Báo cáo", "Reports & Analytics"),
    (r"^## 14\.", "api_reference", "API tham chiếu", "API Reference"),
    (r"^## 15\.", "database", "Cơ sở dữ liệu", "Database Reference"),
    (r"^## 16\.", "appendix", "Quy tắc nghiệp vụ", "Appendix: Key Business Rules"),
]


def _slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return s[:80] or "section"


def _split_sections(text: str) -> list[dict[str, str]]:
    parts = re.split(r"(?=^## )", text, flags=re.MULTILINE)
    sections: list[dict[str, str]] = []
    for part in parts:
        part = part.strip()
        if not part.startswith("##"):
            continue
        lines = part.split("\n", 1)
        header = lines[0].strip()
        body = lines[1].strip() if len(lines) > 1 else ""
        sections.append({"header": header, "body": body})
    return sections


def _module_for_header(header: str) -> tuple[str, str, str]:
    for pattern, mid, title_vi, title_en in _SECTION_MODULE_MAP:
        if re.match(pattern, header):
            return mid, title_vi, title_en
    return _slug(header), header, header


def _extract_subsections(body: str) -> list[str]:
    subs = re.findall(r"^###+ (.+)$", body, flags=re.MULTILINE)
    return subs[:24]


def _terms_from_header(header: str, body: str) -> tuple[list[str], list[str]]:
    vi: list[str] = []
    en: list[str] = []
    if "Stock Dispatch" in body or "Stock Dispatch" in header:
        vi.extend(["phiếu xuất kho", "xuất kho"])
        en.extend(["stock dispatch", "outbound"])
    if "Stock Receipt" in body or "Receipt" in header:
        vi.extend(["phiếu nhập kho", "nhập kho"])
        en.extend(["stock receipt", "inbound"])
    if "Product" in header or "products" in body.lower():
        vi.extend(["sản phẩm", "SKU"])
        en.extend(["product", "sku"])
    if "Sales Order" in body or "POS" in body:
        vi.extend(["đơn hàng", "bán hàng", "POS"])
        en.extend(["sales order", "pos"])
    if "financeledger" in body.lower() or "Finance" in header:
        vi.extend(["sổ cái", "doanh thu", "chi phí"])
        en.extend(["finance ledger", "revenue", "expense"])
    return list(dict.fromkeys(vi)), list(dict.fromkeys(en))


def build(guide_path: Path) -> dict:
    text = guide_path.read_text(encoding="utf-8")
    guide_sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    sections = _split_sections(text)

    _CHUNKS_DIR.mkdir(parents=True, exist_ok=True)
    for old in _CHUNKS_DIR.glob("*.md"):
        old.unlink()

    modules: list[dict] = []
    for i, sec in enumerate(sections):
        header = sec["header"]
        body = sec["body"]
        mid, title_vi, title_en = _module_for_header(header)
        chunk_id = f"{i:02d}_{mid}"
        guide_ref = header.split(".", 1)[0].replace("## ", "§") if header.startswith("##") else header
        vi_terms, en_terms = _terms_from_header(header, body)
        subs = _extract_subsections(body)

        chunk_name = f"{chunk_id}.md"
        chunk_path = _CHUNKS_DIR / chunk_name
        chunk_path.write_text(f"{header}\n\n{body}", encoding="utf-8")

        misnomers = [m for m in _STATIC_MISNOMERS if m.get("module_id", "").startswith(mid.split("_")[0]) or mid in str(m.get("module_id", ""))]
        if mid == "inventory":
            misnomers = [m for m in _STATIC_MISNOMERS if "inventory" in m.get("module_id", "") or "stock" in m.get("module_id", "")]

        modules.append(
            {
                "id": mid if i == 0 or modules and modules[-1]["id"] != mid else f"{mid}_{i}",
                "title_vi": title_vi,
                "title_en": title_en,
                "guide_refs": [guide_ref],
                "chunk_file": chunk_name,
                "subsections": subs,
                "user_terms_vi": vi_terms,
                "user_terms_en": en_terms,
                "common_misnomers": misnomers,
                "capabilities": subs[:12],
            }
        )

    # Deduplicate module ids
    seen: set[str] = set()
    for m in modules:
        base = m["id"]
        if base in seen:
            m["id"] = f"{base}_{len(seen)}"
        seen.add(m["id"])

    return {
        "version": "1",
        "guide_sha256": guide_sha,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_path": str(guide_path.relative_to(_REPO_ROOT)) if guide_path.is_relative_to(_REPO_ROOT) else str(guide_path),
        "modules": modules,
        "global_misnomers": _STATIC_MISNOMERS,
        "global_out_of_scope": _GLOBAL_OUT_OF_SCOPE,
        "ai_rules_summary": _AI_RULES_SUMMARY,
    }


def main() -> int:
    guide = Path(sys.argv[1]) if len(sys.argv) > 1 else _DEFAULT_GUIDE
    if not guide.is_file():
        print(f"GUID not found: {guide}", file=sys.stderr)
        return 1
    index = build(guide)
    _OUT_DIR.mkdir(parents=True, exist_ok=True)
    index_path = _OUT_DIR / "erp_domain_index.json"
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    meta = {
        "guide_sha256": index["guide_sha256"],
        "generated_at": index["generated_at"],
        "module_count": len(index["modules"]),
        "chunk_count": len(list(_CHUNKS_DIR.glob("*.md"))),
    }
    (_OUT_DIR / "index_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"Wrote {index_path} ({len(index['modules'])} modules, {meta['chunk_count']} chunks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
