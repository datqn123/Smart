from __future__ import annotations

from app.smart_erp_mcp.handlers import handle_intent_analyze, handle_write_commit
from app.smart_erp_mcp.observability import redact_hitl_token


def test_intent_transactional_hitl() -> None:
    out = handle_intent_analyze("cập nhật tồn kho SKU-1")
    assert out["ok"] is True
    assert out["primary_intent"] == "transactional_update"
    assert out["hitl_required"] is True
    assert "write_commit" in out["suggested_tools"]


def test_write_rejects_short_token() -> None:
    out = handle_write_commit(
        proposal_id="p1",
        hitl_token="tooshort",
        idempotency_key="idem-1",
        payload_json="{}",
    )
    assert out["ok"] is False
    assert out["error"]["code"] == "FORBIDDEN"


def test_write_accepts_stub() -> None:
    out = handle_write_commit(
        proposal_id="p1",
        hitl_token="x" * 16,
        idempotency_key="idem-1",
        payload_json='{"qty": 5}',
    )
    assert out["ok"] is True
    assert out["status"] == "accepted_stub"


def test_redact_token() -> None:
    assert "***" in redact_hitl_token("abc")
    r = redact_hitl_token("abcdefghijklmnop")
    assert r.startswith("abcd")
    assert "…" in r
