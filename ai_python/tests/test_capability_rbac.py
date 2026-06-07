from __future__ import annotations

import pytest


def test_staff_cannot_see_cost_price() -> None:
    from app.harness.capability import CapabilityMatrix

    rows = [{"product_name": "Áo", "cost_price": 100, "sale_price": 150}]

    masked = CapabilityMatrix().mask_columns("staff", rows)

    assert "cost_price" not in masked[0]
    assert masked[0]["sale_price"] == 150


def test_owner_sees_sensitive_columns() -> None:
    from app.harness.capability import CapabilityMatrix

    rows = [{"product_name": "Áo", "cost_price": 100}]

    masked = CapabilityMatrix().mask_columns("owner", rows)

    assert masked[0]["cost_price"] == 100


def test_capability_blocks_write_sql_100pct() -> None:
    from app.harness.policy import HarnessPolicy, HarnessPolicyError

    with pytest.raises(HarnessPolicyError):
        HarnessPolicy().check("sql_query", {"sql": "SELECT 1; DROP TABLE products"}, role="owner", tenant_id="t1")


def test_tenant_scope_enforced() -> None:
    from app.harness.policy import HarnessPolicy, HarnessPolicyError

    with pytest.raises(HarnessPolicyError):
        HarnessPolicy().check("sql_query", {"query": "SELECT 1", "tenant_id": "t2"}, role="owner", tenant_id="t1")


def test_select_star_masks_sensitive_at_output() -> None:
    from app.harness.capability import CapabilityMatrix

    rows = [{"id": 1, "cost_price": 100, "margin": 50, "product_name": "Áo"}]

    masked = CapabilityMatrix().mask_columns("staff", rows)

    assert "cost_price" not in masked[0]
    assert "margin" not in masked[0]
    assert masked[0]["product_name"] == "Áo"


def test_idempotency_prevents_double_confirm() -> None:
    from app.harness.capability import IdempotencyGuard

    guard = IdempotencyGuard()
    calls = 0

    def commit():
        nonlocal calls
        calls += 1
        return {"committed": True}

    first = guard.run_once("draft-1", commit)
    second = guard.run_once("draft-1", commit)

    assert first == {"committed": True}
    assert second == {"committed": True}
    assert calls == 1
