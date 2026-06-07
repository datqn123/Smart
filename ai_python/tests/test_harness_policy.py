from __future__ import annotations

import pytest


def test_policy_blocks_write_sql_keywords() -> None:
    from app.harness.policy import HarnessPolicy, HarnessPolicyError

    policy = HarnessPolicy()

    for sql in (
        "DELETE FROM orders WHERE 1=1",
        "UPDATE products SET price=0",
        "DROP TABLE cash_transactions",
        "INSERT INTO products(name) VALUES ('x')",
    ):
        with pytest.raises(HarnessPolicyError):
            policy.check("sql_query", {"sql": sql})


def test_policy_allows_select_and_unknown_tool() -> None:
    from app.harness.policy import HarnessPolicy

    policy = HarnessPolicy()

    policy.check("sql_query", {"sql": "SELECT id, name FROM products LIMIT 10"})
    policy.check("unknown_tool", {})


def test_policy_catalog_draft_does_not_sql_scan_args() -> None:
    from app.harness.policy import HarnessPolicy

    policy = HarnessPolicy()

    policy.check("catalog_draft", {"request": "tạo sản phẩm mới DELETE FROM x"})
