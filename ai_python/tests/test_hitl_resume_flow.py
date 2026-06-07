from __future__ import annotations

import asyncio
from types import SimpleNamespace


def _request(message: str, *, thread_id: str = "thread-1", clarification=None):
    from app.api.schemas import ChatMetadata, ChatOptions, ChatRequest

    return ChatRequest(
        message=message,
        metadata=ChatMetadata(user_id="u1", tenant_id="t1", thread_id=thread_id, schema_version="v1"),
        options=ChatOptions(clarification=clarification),
    )


def _clarification(**context):
    from app.api.schemas import ClarificationOptions

    return ClarificationOptions(clarify_id="confirm", clarify_kind="hitl_resume", continuation_context=context or None)


def test_resume_turn_routes_to_harness_before_intent_classifier() -> None:
    from app.api.runtime import _should_use_harness_loop

    settings = SimpleNamespace(harness_loop_enabled=True, harness_loop_intents=["catalog_draft"])
    req = _request("xác nhận", clarification=_clarification(draftId="draft-1"))

    assert _should_use_harness_loop(req, settings) is True


def test_build_turn_context_carries_clarification_and_pending_payload() -> None:
    from app.api.runtime import _build_turn_context

    req = _request("xác nhận", clarification=_clarification(draftId="draft-1"))

    ctx = _build_turn_context(
        req,
        correlation_id="corr-1",
        bearer_token="token",
        pending_hitl_tool="catalog_draft",
        pending_hitl_payload={"draftId": "draft-1", "entityType": "product"},
    )

    assert ctx.clarification_response == {
        "clarify_id": "confirm",
        "clarify_kind": "hitl_resume",
        "suggested_rewrite": None,
        "continuation_context": {"draftId": "draft-1"},
    }
    assert ctx.pending_hitl_tool == "catalog_draft"
    assert ctx.pending_hitl_payload == {"draftId": "draft-1", "entityType": "product"}


def test_runtime_persists_pending_hitl_and_clears_after_resume_success() -> None:
    from app.api.runtime import LangHarnessRuntime
    from app.harness.orchestrator import FinalAnswerEvent, PendingHitlEvent, SsePayloadEvent
    from app.harness.tool_registry import HitlSpec

    class Legacy:
        def stream(self, *args, **kwargs):  # noqa: ANN002, ANN003
            raise AssertionError("resume turn must not use legacy graph")

    class Orchestrator:
        def __init__(self) -> None:
            self.contexts = []

        async def run(self, scratchpad, ctx):  # noqa: ANN001
            self.contexts.append(ctx)
            if len(self.contexts) == 1:
                payload = {"draftId": "draft-1", "entityType": "product"}
                yield SsePayloadEvent("draft", payload)
                yield PendingHitlEvent(HitlSpec(event_name="draft", payload=payload, resume_token="thread-1"))
                return
            assert ctx.clarification_response is not None
            assert ctx.pending_hitl_tool == "catalog_draft"
            assert ctx.pending_hitl_payload == {"draftId": "draft-1", "entityType": "product"}
            yield FinalAnswerEvent("Đã xác nhận")

    settings = SimpleNamespace(harness_loop_enabled=True, harness_loop_intents=["catalog_draft"])
    orchestrator = Orchestrator()
    runtime = LangHarnessRuntime(Legacy(), orchestrator, graph_settings=settings)

    first_chunks = list(runtime.stream(_request("tạo sản phẩm A"), correlation_id="corr-1"))
    assert {"harness": {"catalog_draft_sse": {"draftId": "draft-1", "entityType": "product"}}} in first_chunks

    second_chunks = list(runtime.stream(_request("xác nhận", clarification=_clarification()), correlation_id="corr-2"))
    assert ("custom", {"final_answer": "Đã xác nhận"}) in second_chunks
    assert runtime._pending_hitl == {}


def test_catalog_draft_confirm_commits_existing_draft_without_regenerating(monkeypatch) -> None:  # noqa: ANN001
    from app.graph.tools.catalog_draft import CatalogDraftTool
    from app.harness.tool_registry import TurnContext

    class Compiled:
        def invoke(self, *args, **kwargs):  # noqa: ANN002, ANN003
            raise AssertionError("confirm turn must not regenerate catalog draft")

    def fake_commit(settings, **kwargs):  # noqa: ANN001, ANN003
        assert kwargs["draft_id"] == "draft-1"
        return {"committedCount": 1, "failedCount": 0, "skippedCount": 0}

    monkeypatch.setattr("app.graph.tools.catalog_draft.commit_catalog_draft", fake_commit)
    deps = SimpleNamespace(settings=SimpleNamespace(), harness=SimpleNamespace())
    tool = CatalogDraftTool(deps, compiled=Compiled())
    ctx = TurnContext(
        tenant_id="t1",
        user_id="u1",
        thread_id="thread-1",
        correlation_id="corr-1",
        bearer_token=None,
        schema_version="v1",
        clarification_response={"clarify_id": "confirm"},
        pending_hitl_tool="catalog_draft",
        pending_hitl_payload={"draftId": "draft-1", "entityType": "product"},
    )

    result = asyncio.run(tool.invoke({"request": "confirm"}, ctx))

    assert result.ok is True
    assert result.output["commit_result"]["committedCount"] == 1
    assert "Đã xác nhận" in result.observation_text


def test_inventory_draft_confirm_commits_existing_draft_without_regenerating(monkeypatch) -> None:  # noqa: ANN001
    from app.graph.tools.inventory_draft import InventoryDraftTool
    from app.harness.tool_registry import TurnContext

    class Compiled:
        def invoke(self, *args, **kwargs):  # noqa: ANN002, ANN003
            raise AssertionError("confirm turn must not regenerate inventory draft")

    def fake_commit(settings, **kwargs):  # noqa: ANN001, ANN003
        assert kwargs["draft_id"] == "draft-2"
        return {"ok": True, "message": "Đã tạo phiếu", "createdReceiptId": 42}

    monkeypatch.setattr("app.graph.tools.inventory_draft.commit_inventory_draft", fake_commit)
    deps = SimpleNamespace(settings=SimpleNamespace(), harness=SimpleNamespace())
    tool = InventoryDraftTool(deps, compiled=Compiled())
    ctx = TurnContext(
        tenant_id="t1",
        user_id="u1",
        thread_id="thread-1",
        correlation_id="corr-1",
        bearer_token=None,
        schema_version="v1",
        clarification_response={"clarify_id": "confirm"},
        pending_hitl_tool="inventory_draft",
        pending_hitl_payload={"draftId": "draft-2", "entityType": "stock_receipt"},
    )

    result = asyncio.run(tool.invoke({"request": "confirm"}, ctx))

    assert result.ok is True
    assert result.output["commit_result"]["createdReceiptId"] == 42
    assert "Đã xác nhận" in result.observation_text
