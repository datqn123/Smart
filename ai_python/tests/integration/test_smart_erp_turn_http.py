from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from app.main import app


def test_smart_erp_turn_inline_data_query(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SMART_ERP_MCP_INLINE", "1")
    monkeypatch.delenv("SMART_ERP_MCP_STDIO", raising=False)
    with TestClient(app) as client:
        r = client.post("/v1/smart-erp/turn", json={"user_text": "tồn kho các SKU"})
    assert r.status_code == 200
    body = r.json()
    assert body["mode"] == "inline"
    names = [s["tool"] for s in body["steps"]]
    assert "intent_analyze" in names
    assert "read_catalog_snapshot" in names
    assert "sql_execute_read" in names


def test_smart_erp_turn_inline_rag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SMART_ERP_MCP_INLINE", "1")
    monkeypatch.delenv("SMART_ERP_MCP_STDIO", raising=False)
    with TestClient(app) as client:
        r = client.post("/v1/smart-erp/turn", json={"user_text": "xin chào"})
    assert r.status_code == 200
    body = r.json()
    assert body["steps"][0]["tool"] == "intent_analyze"
    assert any(s["tool"] == "rag_retrieve" for s in body["steps"])


@pytest.mark.asyncio
async def test_smart_erp_turn_stdio_smoke(monkeypatch: pytest.MonkeyPatch) -> None:
    if os.environ.get("RUN_SMART_ERP_MCP_STDIO", "").lower() not in ("1", "true", "yes"):
        pytest.skip("set RUN_SMART_ERP_MCP_STDIO=1 to run stdio integration")
    monkeypatch.delenv("SMART_ERP_MCP_INLINE", raising=False)
    monkeypatch.setenv("SMART_ERP_MCP_STDIO", "1")
    from app.smart_erp_mcp.turn import run_smart_erp_turn

    out = await run_smart_erp_turn("tồn kho", "")
    assert out["mode"] == "stdio"
    assert out["steps"][0]["tool"] == "intent_analyze"
