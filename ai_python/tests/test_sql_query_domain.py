"""Tests for SQL query domain routing (inventory vs ledger vs documents)."""

from __future__ import annotations

from app.config.graph_settings import GraphSettings
from app.graph.dbmeta import ColumnMeta, SchemaArtifact, TableMeta
from app.graph.deps import GraphDeps
from app.graph.nodes.sql_pipeline import _effective_ledger_first_prompts
from app.graph.sql_executor import StubSqlExecutor
from app.graph.sql_query_domain import detect_sql_query_domain
from app.graph.sql_table_selection import (
    ensure_price_tables_for_question,
    heuristic_select_tables,
    select_tables_for_question,
)
from app.graph.state import AgentState
from langchain_core.messages import HumanMessage


def _inventory_artifact() -> SchemaArtifact:
    cols = [ColumnMeta(name="id", type="int")]
    return SchemaArtifact(
        schema_version="v1",
        tables=[
            TableMeta(name="inventory", columns=cols + [ColumnMeta(name="quantity", type="int")]),
            TableMeta(name="products", columns=cols + [ColumnMeta(name="name", type="text")]),
            TableMeta(name="stockreceipts", columns=cols),
            TableMeta(name="stockdispatches", columns=cols),
            TableMeta(name="warehouselocations", columns=cols),
        ],
    )


def test_detect_inventory_domain_vi() -> None:
    assert detect_sql_query_domain("Có bao nhiêu sản phẩm đang hết hàng?") == "inventory"
    assert detect_sql_query_domain("Tổng giá trị tồn kho") == "inventory"


def test_detect_ledger_domain() -> None:
    assert detect_sql_query_domain("Doanh thu tháng 5") == "ledger"


def test_detect_catalog_price_domain() -> None:
    assert detect_sql_query_domain("Tìm các sản phẩm có giá vốn trên 200000") == "catalog_price"


def test_ensure_price_tables_injects_productunits() -> None:
    picked = [
        "categories",
        "productimages",
        "productpricehistory",
        "products",
        "stockreceiptdetails",
        "stockreceipts",
        "suppliers",
        "vouchers",
    ]
    known = set(picked) | {"productunits"}
    out = ensure_price_tables_for_question(
        "Tìm các sản phẩm có giá vốn trên 200000",
        picked,
        max_tables=8,
        known_tables=known,
    )
    names = {t.lower() for t in out}
    assert "productunits" in names
    assert "productpricehistory" in names
    assert "products" in names
    assert len(out) <= 8


def test_heuristic_prefers_inventory_over_stock_docs() -> None:
    art = _inventory_artifact()
    picked = heuristic_select_tables(
        "Liệt kê sản phẩm hết hàng",
        art,
        max_tables=4,
    )
    names = {x.lower() for x in picked}
    assert "inventory" in names
    assert "products" in names


def test_ledger_first_off_for_inventory_question() -> None:
    settings = GraphSettings(sql_ledger_first_prompts=True)
    state: AgentState = {
        "messages": [HumanMessage(content="Có bao nhiêu sản phẩm đang hết hàng?")],
        "intent": "system_data_query",
    }
    assert _effective_ledger_first_prompts(state, settings) is False


def test_ledger_first_on_for_revenue_question() -> None:
    settings = GraphSettings(sql_ledger_first_prompts=True)
    state: AgentState = {
        "messages": [HumanMessage(content="Tổng doanh thu tháng này")],
        "intent": "system_data_query",
    }
    assert _effective_ledger_first_prompts(state, settings) is True
