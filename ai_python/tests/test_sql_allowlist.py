"""SQL allowlist FK closure and prompt/validation alignment."""

from __future__ import annotations

from app.graph.dbmeta import ColumnMeta, SchemaArtifact, TableMeta
from app.graph.sql_allowlist import (
    cap_tables_priority,
    fk_closure_list_ordered,
    resolve_sql_allowlist,
    validation_allowlist_from_state,
)


def _catalog_price_artifact() -> SchemaArtifact:
    cols = [ColumnMeta(name="id", type="int")]
    return SchemaArtifact(
        schema_version="test",
        tables=[
            TableMeta(
                name="products",
                columns=cols + [ColumnMeta(name="name", type="text")],
            ),
            TableMeta(
                name="productpricehistory",
                columns=cols
                + [
                    ColumnMeta(name="product_id", type="int"),
                    ColumnMeta(name="unit_id", type="int"),
                    ColumnMeta(name="cost_price", type="numeric"),
                ],
                fks=[
                    {"column": "product_id", "ref_table": "products", "ref_column": "id"},
                    {"column": "unit_id", "ref_table": "productunits", "ref_column": "id"},
                ],
            ),
            TableMeta(
                name="productunits",
                columns=cols
                + [
                    ColumnMeta(name="product_id", type="int"),
                    ColumnMeta(name="is_base_unit", type="bool"),
                ],
                fks=[{"column": "product_id", "ref_table": "products", "ref_column": "id"}],
            ),
            TableMeta(name="categories", columns=cols),
            TableMeta(name="vouchers", columns=cols),
        ],
    )


def test_fk_closure_adds_productunits_from_price_history() -> None:
    art = _catalog_price_artifact()
    out = fk_closure_list_ordered(
        art,
        ["productpricehistory", "products"],
        max_hops=1,
    )
    names = {t.lower() for t in out}
    assert "productunits" in names
    assert out.index("products") < out.index("productunits")


def test_resolve_allowlist_includes_join_partner_within_cap() -> None:
    art = _catalog_price_artifact()
    selected = [
        "categories",
        "productimages",
        "productpricehistory",
        "products",
        "stockreceiptdetails",
        "stockreceipts",
        "suppliers",
        "vouchers",
    ]
    # productimages not in artifact — dropped
    eff = resolve_sql_allowlist(
        art,
        selected,
        fk_expand=True,
        fk_hops=1,
        max_tables=10,
    )
    assert eff is not None
    names = {t.lower() for t in eff}
    assert "productunits" in names
    assert "productpricehistory" in names


def test_cap_tables_priority_keeps_seed_order() -> None:
    out = cap_tables_priority(
        ["products", "productpricehistory", "productunits", "categories"],
        3,
    )
    assert out == ["products", "productpricehistory", "productunits"]


def test_validation_allowlist_from_state_prefers_sql_allowlist_tables() -> None:
    art = _catalog_price_artifact()
    state = {
        "sql_allowlist_tables": ["products", "productpricehistory", "productunits"],
        "selected_tables": ["products"],
    }
    allow = validation_allowlist_from_state(
        art,
        state,
        fk_expand=True,
        fk_hops=1,
        max_tables=8,
    )
    assert allow is not None
    assert "productunits" in allow
