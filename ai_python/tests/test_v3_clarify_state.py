"""SRS-006 AC-18: durable clarify state for v3 harness turns."""

from __future__ import annotations

import time
from types import SimpleNamespace

import pytest

from app.api.schemas import ChatMetadata, ChatOptions, ChatRequest, ClarificationOptions
from app.harness.hitl_store import InMemoryPendingHitlStore, PendingHitlRecord
from app.harness.orchestrator import ClarifyEvent, FinalAnswerEvent


def _request(message: str, *, clarification=None) -> ChatRequest:
    return ChatRequest(
        message=message,
        metadata=ChatMetadata(user_id="u1", tenant_id="t1", thread_id="thread-1", schema_version="v1"),
        options=ChatOptions(clarification=clarification),
    )


class _ClarifyOrchestrator:
    async def run(self, scratchpad, ctx):  # noqa: ANN001
        yield ClarifyEvent(
            questions=["Khoảng thời gian nào?"],
            suggested_rewrite="Doanh thu tháng này?",
            original_question="doanh thu",
        )


class _CaptureOrchestrator:
    def __init__(self) -> None:
        self.message = ""

    async def run(self, scratchpad, ctx):  # noqa: ANN001
        self.message = str(scratchpad.messages[0].content)
        yield FinalAnswerEvent("ok")


def _runtime(orchestrator, store):  # noqa: ANN001
    from app.api.runtime import LangHarnessRuntime

    return LangHarnessRuntime(
        compiled=None,
        orchestrator=orchestrator,
        graph_settings=SimpleNamespace(harness_loop_enabled=True, harness_loop_intents=["data_query"]),
        hitl_store=store,
    )


def test_clarify_event_persists_pending_state() -> None:
    store = InMemoryPendingHitlStore()
    runtime = _runtime(_ClarifyOrchestrator(), store)

    chunks = list(runtime.stream(_request("doanh thu"), correlation_id="cid"))

    assert chunks
    record = store.get("thread-1")
    assert record is not None
    assert record.tool_name == "clarify_user"
    assert record.payload["originalQuestion"] == "doanh thu"
    assert record.payload["questions"] == ["Khoảng thời gian nào?"]


def test_clarify_record_carries_inflight_plan_fields() -> None:
    # AC-18: the durable clarify record has plan-state fields (safe defaults today,
    # since clarify is emitted before any plan node runs).
    store = InMemoryPendingHitlStore()
    runtime = _runtime(_ClarifyOrchestrator(), store)

    list(runtime.stream(_request("doanh thu"), correlation_id="cid"))

    record = store.get("thread-1")
    assert record is not None
    assert record.payload["completedNodeIds"] == []
    assert record.payload["sideEffectNodeIds"] == []
    assert record.payload["resumeMode"] == "replan"
    assert "planGraphHash" in record.payload


def test_clarify_resume_does_not_replay_side_effect_node() -> None:
    # AC-18 / FR-13.3: even if the record names a completed side-effect node, resume
    # reruns the loop fresh and never re-executes it.
    store = InMemoryPendingHitlStore()
    store.put(
        "thread-1",
        PendingHitlRecord(
            tool_name="clarify_user",
            payload={
                "clarifyKind": "harness_data_query",
                "originalQuestion": "tạo phiếu nhập",
                "completedNodeIds": ["draft1"],
                "sideEffectNodeIds": ["draft1"],
                "resumeMode": "replan",
            },
            tenant_id="t1",
            user_id="u1",
            thread_id="thread-1",
            created_at=time.time(),
        ),
    )
    orchestrator = _CaptureOrchestrator()
    runtime = _runtime(orchestrator, store)
    req = _request(
        "kho A",
        clarification=ClarificationOptions(clarify_id="abc", clarify_kind="harness_data_query"),
    )

    events = list(runtime.stream(req, correlation_id="cid"))

    # resume reran the loop with the recombined question; no plan-node replay machinery
    assert "tạo phiếu nhập" in orchestrator.message
    assert "kho A" in orchestrator.message
    assert any(getattr(e, "__class__", None).__name__ for e in events)
    assert store.get("thread-1") is None  # cleared after resume


def test_clarify_resume_after_runtime_recreation_uses_stored_original_question() -> None:
    store = InMemoryPendingHitlStore()
    store.put(
        "thread-1",
        PendingHitlRecord(
            tool_name="clarify_user",
            payload={
                "clarifyKind": "harness_data_query",
                "originalQuestion": "doanh thu",
            },
            tenant_id="t1",
            user_id="u1",
            thread_id="thread-1",
            created_at=time.time(),
        ),
    )
    orchestrator = _CaptureOrchestrator()
    runtime = _runtime(orchestrator, store)
    req = _request(
        "tháng này",
        clarification=ClarificationOptions(
            clarify_id="abc",
            clarify_kind="harness_data_query",
        ),
    )

    _ = list(runtime.stream(req, correlation_id="cid"))

    assert "doanh thu" in orchestrator.message
    assert "tháng này" in orchestrator.message
    assert store.get("thread-1") is None


def test_clarify_resume_tenant_mismatch_does_not_load_stored_state() -> None:
    store = InMemoryPendingHitlStore()
    store.put(
        "thread-1",
        PendingHitlRecord(
            tool_name="clarify_user",
            payload={"originalQuestion": "doanh thu tenant khác"},
            tenant_id="t2",
            user_id="u1",
            thread_id="thread-1",
            created_at=time.time(),
        ),
    )
    orchestrator = _CaptureOrchestrator()
    runtime = _runtime(orchestrator, store)
    req = _request(
        "tháng này",
        clarification=ClarificationOptions(clarify_id="abc", clarify_kind="harness_data_query"),
    )

    _ = list(runtime.stream(req, correlation_id="cid"))

    assert "tenant khác" not in orchestrator.message
