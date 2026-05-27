from __future__ import annotations

from typing import Any

from app.graph.draft_entity_resolution import (
    resolve_catalog_before_generate,
    resolve_inventory_before_generate,
    search_categories,
    search_products,
)
from app.graph.draft_reference_messages import format_draft_schema_issues
from app.graph.sql_executor import SqlExecutorError
from app.llm.schemas import CatalogDraftSlotsOutput, InventoryDraftSlotsOutput


class _FakeExecutor:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows
        self.last_sql: str | None = None

    def execute(
        self,
        sql: str,
        *,
        tenant_id: str | None,
        correlation_id: str | None = None,
        schema_version: str | None = None,
    ) -> dict[str, Any]:
        _ = tenant_id, correlation_id, schema_version
        self.last_sql = sql
        return {"rows": self.rows, "meta": {}}


def test_dispatch_zero_stock_with_qty_no_quantity_loop() -> None:
    ex = _FakeExecutor(
        [{"sku_code": "COMPUTER-002", "name": "Máy tính", "stock_qty": 0}],
    )
    slots = InventoryDraftSlotsOutput(
        doc_type="stock_dispatch",
        quantity=2,
        product_sku="COMPUTER-002",
        line_count_hint=1,
    )
    patch = resolve_inventory_before_generate(
        question="Tạo phiếu xuất kho: SKU COMPUTER-002, số lượng 2",
        slots=slots,
        executor=ex,
        tenant_id=None,
    )
    assert patch is not None
    body = patch["final_answer"]
    assert "tồn kho = 0" in body or "tồn kho: 0" in body.lower() or "tồn kho = **0**" in body
    assert "bao nhiêu" not in body.lower()
    assert "COMPUTER-002" in body


def test_dispatch_insufficient_stock() -> None:
    ex = _FakeExecutor(
        [{"sku_code": "SKU-1", "name": "SP", "stock_qty": 1}],
    )
    slots = InventoryDraftSlotsOutput(
        doc_type="stock_dispatch",
        quantity=5,
        product_sku="SKU-1",
    )
    patch = resolve_inventory_before_generate(
        question="xuất SKU-1 số lượng 5",
        slots=slots,
        executor=ex,
        tenant_id=None,
    )
    assert patch is not None
    assert "không đủ" in patch["final_answer"].lower() or "tồn **1**" in patch["final_answer"]


def test_resolve_dispatch_uses_llm_slots_not_full_phrase() -> None:
    ex = _FakeExecutor(
        [
            {"sku_code": "COMPUTER-002", "name": "Máy tính", "stock_qty": 0},
        ],
    )
    slots = InventoryDraftSlotsOutput(
        doc_type="stock_dispatch",
        quantity=2,
        product_query="Máy Tính",
        line_count_hint=1,
    )
    patch = resolve_inventory_before_generate(
        question="tạo phiếu xuất kho hai cái Máy Tính",
        slots=slots,
        executor=ex,
        tenant_id="t1",
    )
    assert patch is not None
    assert "COMPUTER-002" in patch["final_answer"]
    assert "hai cái Máy Tính" not in patch["final_answer"]
    assert ex.last_sql is not None
    assert "Máy Tính" in ex.last_sql
    assert "hai cái" not in ex.last_sql.lower()


def test_receipt_missing_import_qty_not_stock_check() -> None:
    slots = InventoryDraftSlotsOutput(
        doc_type="stock_receipt",
        product_sku="UONG-SUA-1L",
        supplier_code="NCC-SEED-V10-A",
        quantity=None,
    )
    patch = resolve_inventory_before_generate(
        question="Tạo phiếu nhập kho SKU UONG-SUA-1L từ NCC NCC-SEED-V10-A",
        slots=slots,
        executor=_FakeExecutor([{"sku_code": "UONG-SUA-1L", "name": "Sữa", "stock_qty": 0}]),
        tenant_id=None,
    )
    assert patch is not None
    assert "số lượng nhập" in patch["final_answer"].lower()
    assert "tồn kho hiện tại" in patch["final_answer"].lower()
    assert "quantity phải" not in patch["final_answer"].lower()


def test_resolve_receipt_missing_supplier_with_product_slot() -> None:
    ex = _FakeExecutor([{"sku_code": "SKU-1", "name": "Máy tính", "stock_qty": 5}])

    def execute(sql: str, **kwargs: Any) -> dict[str, Any]:
        if "suppliers" in sql.lower():
            return {
                "rows": [{"supplier_code": "NCC1", "name": "Công ty A"}],
                "meta": {},
            }
        return {"rows": [{"sku_code": "SKU-1", "name": "Máy tính", "stock_qty": 5}], "meta": {}}

    ex.execute = execute  # type: ignore[method-assign]

    slots = InventoryDraftSlotsOutput(
        doc_type="stock_receipt",
        product_query="máy tính",
        line_count_hint=1,
    )
    patch = resolve_inventory_before_generate(
        question="tạo phiếu nhập kho máy tính",
        slots=slots,
        executor=ex,
        tenant_id=None,
    )
    assert patch is not None
    assert "nhà cung cấp" in patch["final_answer"].lower()
    assert "SKU-1" in patch["final_answer"]


def test_search_products_escapes_quotes() -> None:
    ex = _FakeExecutor([])
    search_products(ex, tenant_id=None, term="O'Brien")
    assert ex.last_sql is not None
    assert "O''Brien" in ex.last_sql


def test_search_categories_sql_uses_category_code() -> None:
    ex = _FakeExecutor(
        [{"id": 2, "category_code": "CAT002", "name": "Đồ uống", "status": "Active"}],
    )
    rows, err = search_categories(ex, tenant_id=None, term="Đồ uống")
    assert err is None
    assert len(rows) == 1
    assert rows[0]["category_code"] == "CAT002"
    assert ex.last_sql is not None
    assert "c.category_code" in ex.last_sql
    assert "c.code" not in ex.last_sql
    assert "deleted_at IS NULL" in ex.last_sql


def test_search_categories_upstream_error_not_empty() -> None:
    class _FailingExecutor:
        last_sql: str | None = None

        def execute(self, sql: str, **kwargs: Any) -> dict[str, Any]:
            _ = kwargs
            self.last_sql = sql
            raise SqlExecutorError("bad SQL", category="policy")

    ex = _FailingExecutor()
    rows, err = search_categories(ex, tenant_id=None, term="Đồ uống")
    assert rows == []
    assert err == "upstream"


def test_resolve_catalog_finds_do_uong_category() -> None:
    ex = _FakeExecutor(
        [{"id": 2, "category_code": "CAT002", "name": "Đồ uống", "status": "Active"}],
    )

    def execute(sql: str, **kwargs: Any) -> dict[str, Any]:
        if sql.lower().strip().startswith("select c.id"):
            return {
                "rows": [
                    {"id": 2, "category_code": "CAT002", "name": "Đồ uống", "status": "Active"},
                ],
                "meta": {},
            }
        return {"rows": [], "meta": {}}

    ex.execute = execute  # type: ignore[method-assign]

    slots = CatalogDraftSlotsOutput(
        entity_type="product",
        product_query="bánh tráng trộn",
        category_query="Đồ uống",
    )
    patch = resolve_catalog_before_generate(
        question="Thêm món bánh tráng trộn vào danh mục Đồ uống",
        slots=slots,
        executor=ex,
        tenant_id=None,
    )
    assert patch is None


def test_resolve_catalog_category_lookup_failure_message() -> None:
    class _FailingExecutor:
        def execute(self, sql: str, **kwargs: Any) -> dict[str, Any]:
            _ = kwargs
            if "categories" in sql.lower():
                raise SqlExecutorError("upstream", category="policy")
            return {"rows": [], "meta": {}}

    slots = CatalogDraftSlotsOutput(
        entity_type="product",
        product_query="bánh tráng trộn",
        category_query="Đồ uống",
    )
    patch = resolve_catalog_before_generate(
        question="Thêm món bánh tráng trộn vào danh mục Đồ uống",
        slots=slots,
        executor=_FailingExecutor(),
        tenant_id=None,
    )
    assert patch is not None
    assert "lỗi hệ thống" in patch["final_answer"].lower()
    assert "không tìm thấy danh mục" not in patch["final_answer"].lower()


def test_format_draft_schema_issues() -> None:
    msg = format_draft_schema_issues(
        doc_kind="phiếu nhập kho",
        issues=["Thiếu nhà cung cấp"],
    )
    assert "phiếu nhập kho" in msg
    assert "Thiếu nhà cung cấp" in msg
    assert "Gợi ý" in msg
