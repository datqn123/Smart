import logging

import pytest
from pydantic import ValidationError

from app.agents.policy import policy_probe_message, should_route_db_numeric, wants_clarify_branch
from app.contracts import SseEnvelope
from app.contracts.sse_envelope import sse_error_message_for_mcp
from app.observability import rag_ingest_telemetry_best_effort


def test_policy_detects_secret_and_dml() -> None:
    assert policy_probe_message("postgres://localhost") == "POLICY_REFUSE_SECRET"
    assert policy_probe_message("DELETE from t") == "POLICY_REFUSE_WRITE"
    assert policy_probe_message("Đọc doanh thu") is None


def test_router_numeric_vs_conceptual() -> None:
    assert (
        should_route_db_numeric("doanh thu theo ngày 30 ngày qua (tóm tắt tổng cuối kỳ)".lower())
        is True
    )
    assert should_route_db_numeric("giải thích quan hệ giữa bảng a và b".lower()) is False


def test_clarify_sku_sentence() -> None:
    lowered = "làm rõ bạn đang hỏi doanh thu theo sku hay theo đơn hàng?".lower().replace("\n", " ")
    assert wants_clarify_branch(lowered) is True


def test_sse_envelope_validation() -> None:
    env = SseEnvelope(event="token", payload={"delta": "x"})
    parsed = env.to_wire_json()
    compact = "".join(parsed.split())
    assert '"event":"token"' in compact


def test_sse_error_mapper_db_rejected_message() -> None:
    m = sse_error_message_for_mcp("DB_QUERY_REJECTED", "")
    assert "read-only" in m.lower()


def test_search_docs_validator_not_wrapped_as_generic_exception() -> None:
    from app.contracts import SearchDocsIn

    with pytest.raises(ValidationError):
        SearchDocsIn(query="ok", top_k=50)


def test_rag_ingest_health_log(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setenv("RAG_LAST_INGEST_UNIX", str(1_706_500_800))
    monkeypatch.delenv("RAG_STALE_ACKNOWLEDGED", raising=False)
    with caplog.at_level(logging.INFO, logger="app.observability"):
        rag_ingest_telemetry_best_effort(now_ts=1_706_501_800.0)
    assert any(rec.msg == "rag_ingest_ok" for rec in caplog.records)
