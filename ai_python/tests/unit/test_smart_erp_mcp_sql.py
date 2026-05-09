from __future__ import annotations

import pytest

from app.smart_erp_mcp.catalog import allowlist_lower
from app.smart_erp_mcp.sql_execute import sql_execute_read
from app.smart_erp_mcp.sql_validate import SqlValidationError, validate_select


def test_validate_select_ok() -> None:
    tree = validate_select("SELECT qty FROM products WHERE id = 1", allowlist_lower())
    assert tree is not None


def test_validate_rejects_multi_statement() -> None:
    with pytest.raises(SqlValidationError) as ei:
        validate_select("SELECT 1; SELECT 2", allowlist_lower())
    assert ei.value.code == "VALIDATION_FAILED"


def test_validate_rejects_drop() -> None:
    with pytest.raises(SqlValidationError) as ei:
        validate_select("DROP TABLE products", allowlist_lower())
    assert ei.value.code in ("VALIDATION_FAILED", "FORBIDDEN")


def test_validate_rejects_unknown_table() -> None:
    with pytest.raises(SqlValidationError) as ei:
        validate_select("SELECT * FROM secret_table", allowlist_lower())
    assert ei.value.code == "SCOPE_VIOLATION"


def test_execute_read_products() -> None:
    out = sql_execute_read("SELECT id, sku, qty FROM products ORDER BY id")
    assert out["ok"] is True
    assert out["columns"] == ["id", "sku", "qty"]
    assert out["row_count"] == 2


def test_execute_rejects_injection_multi() -> None:
    out = sql_execute_read("SELECT 1; DELETE FROM products")
    assert out["ok"] is False
