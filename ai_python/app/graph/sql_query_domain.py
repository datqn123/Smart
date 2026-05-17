"""Rule-based SQL query domain (inventory vs ledger vs documents) for table selection and prompts."""

from __future__ import annotations

from typing import Literal

SqlQueryDomain = Literal["inventory", "receipt", "dispatch", "ledger", "catalog_price", "generic"]

_INVENTORY_PHRASES = (
    "hết hàng",
    "het hang",
    "out of stock",
    "out-of-stock",
    "tồn kho",
    "ton kho",
    "sắp hết",
    "sap het",
    "low stock",
    "low_stock",
    "còn bao nhiêu",
    "con bao nhieu",
    "số lượng tồn",
    "so luong ton",
    "giá trị tồn",
    "gia tri ton",
    "tồn hiện",
    "ton hien",
    "trong kho",
    "inventory",
    "min_quantity",
    "min_stock",
    "sắp hết hạn",
    "sap het han",
    "expiry",
    "hết hạn",
    "het han",
)

_RECEIPT_PHRASES = (
    "phiếu nhập",
    "phieu nhap",
    "nhập kho",
    "nhap kho",
    "stockreceipt",
)

_DISPATCH_PHRASES = (
    "phiếu xuất",
    "phieu xuat",
    "xuất kho",
    "xuat kho",
    "stockdispatch",
    "giao hàng",
    "giao hang",
)

_CATALOG_PRICE_PHRASES = (
    "giá vốn",
    "gia von",
    "giá bán",
    "gia ban",
    "cost price",
    "cost_price",
    "sale price",
    "sale_price",
    "đơn giá",
    "don gia",
)

_LEDGER_PHRASES = (
    "doanh thu",
    "doanh so",
    "chi phí",
    "chi phi",
    "dòng tiền",
    "dong tien",
    "cashflow",
    "financeledger",
    "sổ cái",
    "so cai",
    "tổng thu",
    "tong thu",
    "tổng chi",
    "tong chi",
)


def detect_sql_query_domain(user_q: str) -> SqlQueryDomain:
    """Classify question for table seeds and prompt bias (heuristic, Vietnamese + English)."""
    q = (user_q or "").lower()
    if any(p in q for p in _INVENTORY_PHRASES):
        return "inventory"
    if any(p in q for p in _RECEIPT_PHRASES):
        return "receipt"
    if any(p in q for p in _DISPATCH_PHRASES):
        return "dispatch"
    if any(p in q for p in _LEDGER_PHRASES):
        return "ledger"
    if any(p in q for p in _CATALOG_PRICE_PHRASES):
        return "catalog_price"
    return "generic"


def default_tables_for_domain(domain: SqlQueryDomain) -> list[str]:
    """Minimal table shortlist before LLM / FK expansion."""
    if domain == "inventory":
        return ["inventory", "products", "warehouselocations", "productunits"]
    if domain == "receipt":
        return ["stockreceipts", "stockreceiptdetails", "products", "suppliers"]
    if domain == "dispatch":
        return ["stockdispatches", "stockdispatch_lines", "products"]
    if domain == "ledger":
        return ["financeledger"]
    if domain == "catalog_price":
        return ["products", "productpricehistory", "productunits", "categories"]
    return []


def sql_hints_for_domain(domain: SqlQueryDomain) -> list[str]:
    """Lines injected into schema_plan / gen_sql context."""
    if domain == "inventory":
        return [
            "Domain: current stock snapshot — fact table is inventory (quantity, product_id, location_id).",
            "Join products for sku_code, name, min_quantity/min_stock; warehouselocations for warehouse/shelf.",
            "Out of stock: inventory.quantity = 0. Low stock: quantity > 0 AND quantity <= min_quantity.",
            "Do NOT use products.status = 'Inactive' for out-of-stock.",
            "Do NOT compute stock from SUM(stockreceiptdetails) - SUM(stockdispatch_lines).",
        ]
    if domain == "receipt":
        return ["Domain: stock receipts — stockreceipts + stockreceiptdetails (+ suppliers, products)."]
    if domain == "dispatch":
        return ["Domain: stock dispatch — stockdispatches + stockdispatch_lines (+ products)."]
    return []


def should_use_ledger_first_prompts(domain: SqlQueryDomain) -> bool:
    return domain == "ledger"


def boost_table_scores_for_domain(
    scores: dict[str, float],
    domain: SqlQueryDomain,
) -> dict[str, float]:
    """Re-rank heuristic table scores when Vietnamese question lacks English table names."""
    if domain == "catalog_price":
        boosts = {
            "products": 40.0,
            "productpricehistory": 35.0,
            "productunits": 30.0,
            "categories": 10.0,
        }
        out = dict(scores)
        for k in list(out.keys()):
            kl = k.lower()
            if kl in boosts:
                out[k] = out.get(k, 0.0) + boosts[kl]
        return out
    if domain != "inventory":
        return scores
    boosts = {
        "inventory": 50.0,
        "products": 25.0,
        "warehouselocations": 15.0,
        "productunits": 12.0,
        "productpricehistory": 8.0,
        "categories": 5.0,
    }
    penalize = {
        "stockreceipts": -20.0,
        "stockreceiptdetails": -20.0,
        "stockdispatches": -20.0,
        "stockdispatch_lines": -20.0,
    }
    out = dict(scores)
    for k in list(out.keys()):
        kl = k.lower()
        if kl in boosts:
            out[k] = out.get(k, 0.0) + boosts[kl]
        if kl in penalize:
            out[k] = out.get(k, 0.0) + penalize[kl]
    return out
