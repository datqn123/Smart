"""Name filter rewrite for case-insensitive category/product names."""

from __future__ import annotations

from app.graph.name_filters import fix_name_equality_to_ilike
from app.graph.validate_sql import validate_sql_deterministic
from app.config.graph_settings import GraphSettings


def test_fix_category_name_equality_to_ilike() -> None:
    sql = (
        "SELECT p.id FROM products p "
        "JOIN categories c ON p.category_id = c.id "
        "WHERE c.name = 'Điện tử 1' LIMIT 100"
    )
    fixed, notes = fix_name_equality_to_ilike(sql)
    assert "c.name ILIKE 'Điện tử 1'" in fixed
    assert "c.name = " not in fixed
    assert notes


def test_validate_sql_applies_name_ilike_rewrite() -> None:
    settings = GraphSettings()
    sql = (
        "SELECT p.sku_code, p.name FROM products p "
        "JOIN categories c ON p.category_id = c.id "
        "WHERE c.name = 'điện tử 1' LIMIT 50"
    )
    ok, _, sanitized, notes = validate_sql_deterministic(sql, settings)
    assert ok
    assert sanitized is not None
    assert "ILIKE" in sanitized
    assert any("ILIKE" in n for n in notes)
