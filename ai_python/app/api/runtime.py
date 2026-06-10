"""Thin adapter from API layer to compiled LangGraph runtime."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass
from functools import lru_cache
from time import monotonic
from typing import Any, Protocol
from uuid import uuid4

from langchain_core.messages import HumanMessage

from app.api.schemas import ChatRequest
from app.config.graph_settings import load_graph_settings
from app.config.settings import load_llm_settings
from app.graph import compile_agent_graph, default_initial_state, iter_graph_stream
from app.graph.deps import GraphDeps
from app.graph.state import fresh_turn_overlay
from app.graph.tools import (
    AnswerComposerTool,
    BuildChartTool,
    CatalogDraftTool,
    DataTableBuilderTool,
    DataValidatorTool,
    ErpGuideTool,
    InventoryDraftTool,
    SchemaExploreTool,
    SqlQueryTool,
)
from app.harness import (
    AgentHarness,
    ClarifyEvent,
    ErrorEvent,
    FinalAnswerEvent,
    HarnessOrchestrator,
    HarnessPolicy,
    PendingHitlEvent,
    ProgressEvent,
    SsePayloadEvent,
    ToolRegistry,
    TurnContext,
    TurnScratchpad,
)
from app.graph.sql_executor import build_sql_executor
from app.harness.hitl_store import (
    InMemoryPendingHitlStore,
    PendingHitlRecord,
    PendingHitlStore,
    SqlitePendingHitlStore,
)
from app.harness.history_store import InMemoryIntentHistoryStore, SqliteIntentHistoryStore
from app.harness.plan_template_store import InMemoryPlanTemplateStore, SqlitePlanTemplateStore
from app.llm.registry import LlmRegistry, build_llm_registry

logger = logging.getLogger(__name__)


def empty_feedback() -> dict:
    return {"policy": [], "exec": [], "result": [], "extras": {}}

HARNESS_LOOP_INTENTS = frozenset(
    {
        "data_query",
        "schema_explore",
        "catalog_draft",
        "inventory_draft",
    }
)
PENDING_HITL_TTL_SECONDS = 30 * 60


class GraphRuntime(Protocol):
    def invoke(
        self,
        request: ChatRequest,
        *,
        correlation_id: str,
        bearer_token: str | None = None,
    ) -> dict[str, Any]:
        ...

    def stream(
        self,
        request: ChatRequest,
        *,
        correlation_id: str,
        bearer_token: str | None = None,
    ) -> Any:
        ...


class LangGraphRuntime:
    def __init__(self, compiled: Any, *, graph_settings: Any) -> None:
        self._compiled = compiled
        self._graph_settings = graph_settings

    def invoke(
        self,
        request: ChatRequest,
        *,
        correlation_id: str,
        bearer_token: str | None = None,
    ) -> dict[str, Any]:
        state = _build_state(
            request=request,
            correlation_id=correlation_id,
            graph_settings=self._graph_settings,
            bearer_token=bearer_token,
        )
        config = _build_graph_config(request, correlation_id=correlation_id)
        out = self._compiled.invoke(state, config)
        return dict(out or {})

    def stream(
        self,
        request: ChatRequest,
        *,
        correlation_id: str,
        bearer_token: str | None = None,
    ) -> Any:
        state = _build_state(
            request=request,
            correlation_id=correlation_id,
            graph_settings=self._graph_settings,
            bearer_token=bearer_token,
        )
        config = _build_graph_config(request, correlation_id=correlation_id)
        return iter_graph_stream(
            self._compiled,
            state,
            config=config,
            correlation_id=correlation_id,
        )


class LangHarnessRuntime:
    """Strangler runtime: route selected turns to Harness loop, otherwise legacy graph."""

    def __init__(
        self,
        compiled: Any,
        orchestrator: HarnessOrchestrator,
        *,
        graph_settings: Any,
        hitl_store: PendingHitlStore | None = None,
    ) -> None:
        self._legacy = LangGraphRuntime(compiled, graph_settings=graph_settings)
        self._orchestrator = orchestrator
        self._graph_settings = graph_settings
        self._hitl_store: PendingHitlStore = hitl_store or InMemoryPendingHitlStore(
            ttl_seconds=float(PENDING_HITL_TTL_SECONDS)
        )

    @property
    def _pending_hitl(self) -> dict[str, Any]:
        """Backward-compat view used by existing tests."""
        store = self._hitl_store
        if hasattr(store, "_store"):
            return store._store  # type: ignore[attr-defined]
        return {}

    def invoke(
        self,
        request: ChatRequest,
        *,
        correlation_id: str,
        bearer_token: str | None = None,
    ) -> dict[str, Any]:
        if _should_use_harness_loop(request, self._graph_settings):
            logger.warning(
                "harness_loop_enabled=True but /invoke always uses legacy graph; "
                "use /stream for harness-orchestrated responses (correlation_id=%s)",
                correlation_id,
            )
        return self._legacy.invoke(request, correlation_id=correlation_id, bearer_token=bearer_token)

    def stream(
        self,
        request: ChatRequest,
        *,
        correlation_id: str,
        bearer_token: str | None = None,
    ) -> Any:
        if not _should_use_harness_loop(request, self._graph_settings):
            intent = _quick_classify_harness_intent(request.message)
            logger.info("harness_route=legacy intent=%s message_preview=%.60s", intent, request.message)
            return self._legacy.stream(request, correlation_id=correlation_id, bearer_token=bearer_token)
        logger.info("harness_route=loop intent=%s message_preview=%.60s", _quick_classify_harness_intent(request.message), request.message)
        hitl_key = _pending_hitl_key(request, correlation_id=correlation_id)
        is_resume = _clarification_response(request) is not None
        pending_record = self._get_pending_hitl(hitl_key, request) if is_resume else None
        pending_clarify_payload = None
        if pending_record is not None and pending_record.tool_name == "clarify_user":
            pending_clarify_payload = pending_record.payload
            pending_record = None
        return _iter_harness_stream(
            self._orchestrator,
            request,
            graph_settings=self._graph_settings,
            correlation_id=correlation_id,
            bearer_token=bearer_token,
            pending_hitl_tool=pending_record.tool_name if pending_record else None,
            pending_hitl_payload=pending_record.payload if pending_record else None,
            pending_clarify_payload=pending_clarify_payload,
            on_pending_hitl=lambda spec: self._store_pending_hitl(
                hitl_key,
                spec,
                tenant_id=request.metadata.tenant_id,
                user_id=request.metadata.user_id,
                thread_id=request.metadata.thread_id,
            ),
            on_pending_clarify=lambda event: self._store_pending_clarify(
                hitl_key,
                event,
                tenant_id=request.metadata.tenant_id,
                user_id=request.metadata.user_id,
                thread_id=request.metadata.thread_id,
            ),
            on_resume_success=(lambda: self._hitl_store.delete(hitl_key)) if is_resume else None,
        )

    async def astream(
        self,
        request: ChatRequest,
        *,
        correlation_id: str,
        bearer_token: str | None = None,
    ) -> AsyncIterator[Any]:
        """Native async stream path — avoids private event loop per request."""
        if not _should_use_harness_loop(request, self._graph_settings):
            # Wrap legacy sync path in async bridge (asyncio.to_thread is not needed
            # here because iter_graph_stream is a sync iterator; yielding directly is
            # safe since FastAPI handles sync iterables in StreamingResponse too, but
            # we keep the async contract for the caller).
            for chunk in self._legacy.stream(request, correlation_id=correlation_id, bearer_token=bearer_token):
                yield chunk
            return

        logger.info(
            "harness_route=loop/async intent=%s message_preview=%.60s",
            _quick_classify_harness_intent(request.message),
            request.message,
        )
        hitl_key = _pending_hitl_key(request, correlation_id=correlation_id)
        is_resume = _clarification_response(request) is not None
        pending_record = self._get_pending_hitl(hitl_key, request) if is_resume else None
        pending_clarify_payload = None
        if pending_record is not None and pending_record.tool_name == "clarify_user":
            pending_clarify_payload = pending_record.payload
            pending_record = None

        async for event in _harness_events(
            self._orchestrator,
            request,
            correlation_id=correlation_id,
            bearer_token=bearer_token,
            pending_hitl_tool=pending_record.tool_name if pending_record else None,
            pending_hitl_payload=pending_record.payload if pending_record else None,
            pending_clarify_payload=pending_clarify_payload,
        ):
            if isinstance(event, PendingHitlEvent):
                self._store_pending_hitl(
                    hitl_key,
                    event.spec,
                    tenant_id=request.metadata.tenant_id,
                    user_id=request.metadata.user_id,
                    thread_id=request.metadata.thread_id,
                )
            if isinstance(event, ClarifyEvent):
                self._store_pending_clarify(
                    hitl_key,
                    event,
                    tenant_id=request.metadata.tenant_id,
                    user_id=request.metadata.user_id,
                    thread_id=request.metadata.thread_id,
                )
            if isinstance(event, FinalAnswerEvent) and is_resume:
                self._hitl_store.delete(hitl_key)
            yield _event_to_stream_chunk(event)

    def _store_pending_hitl(
        self,
        key: str,
        spec: Any,
        *,
        tenant_id: str | None = None,
        user_id: str | None = None,
        thread_id: str | None = None,
    ) -> None:
        import time

        tool_name = _tool_name_from_hitl_event(str(getattr(spec, "event_name", "") or ""))
        if not tool_name:
            return
        payload = getattr(spec, "payload", None)
        self._hitl_store.put(
            key,
            PendingHitlRecord(
                tool_name=tool_name,
                payload=dict(payload) if isinstance(payload, dict) else {},
                tenant_id=tenant_id,
                user_id=user_id,
                thread_id=thread_id,
                created_at=time.time(),
            ),
        )

    def _store_pending_clarify(
        self,
        key: str,
        event: ClarifyEvent,
        *,
        tenant_id: str | None = None,
        user_id: str | None = None,
        thread_id: str | None = None,
    ) -> None:
        import time

        self._hitl_store.put(
            key,
            PendingHitlRecord(
                tool_name="clarify_user",
                payload={
                    "clarifyKind": "harness_data_query",
                    "questions": list(event.questions),
                    "suggestedRewrite": event.suggested_rewrite,
                    "originalQuestion": event.original_question,
                    # AC-18 in-flight plan state. Clarify is currently emitted before
                    # any plan node runs, so these are empty; carrying them keeps the
                    # record shape correct and lets resume guarantee no side-effect
                    # node is ever replayed (resume reruns the loop, FR-13.3).
                    "planGraphHash": getattr(event, "plan_graph_hash", None),
                    "completedNodeIds": list(getattr(event, "completed_node_ids", []) or []),
                    "sideEffectNodeIds": list(getattr(event, "side_effect_node_ids", []) or []),
                    "resumeMode": getattr(event, "resume_mode", "replan") or "replan",
                },
                tenant_id=tenant_id,
                user_id=user_id,
                thread_id=thread_id,
                created_at=time.time(),
            ),
        )

    def _get_pending_hitl(self, key: str, request: ChatRequest) -> PendingHitlRecord | None:
        record = self._hitl_store.get(key)
        if record is None:
            return None
        if record.tenant_id and record.tenant_id != request.metadata.tenant_id:
            return None
        if record.user_id and record.user_id != request.metadata.user_id:
            return None
        return record


def _build_state(
    *,
    request: ChatRequest,
    correlation_id: str,
    graph_settings: Any,
    bearer_token: str | None = None,
) -> dict[str, Any]:
    state = dict(default_initial_state())
    state["messages"] = [HumanMessage(content=request.message)]
    state["correlation_id"] = correlation_id
    state["user_id"] = request.metadata.user_id
    state["tenant_id"] = request.metadata.tenant_id
    state["thread_id"] = request.metadata.thread_id
    state["schema_version"] = request.metadata.schema_version
    # Fresh turn: do not let checkpointed SQL channel bleed into this answer.
    state.update(fresh_turn_overlay())
    state["sql_repair_max_attempts"] = int(getattr(graph_settings, "sql_repair_max_attempts", 3))
    state["validation_feedback"] = empty_feedback()
    state["interaction_mode"] = request.options.interaction_mode
    state["planning_mode"] = request.options.planning_mode
    clar = getattr(request.options, "clarification", None)
    state["clarification_response"] = (
        clar.model_dump(mode="json")
        if clar is not None
        else None
    )
    state["spring_bearer_token"] = bearer_token
    return state


def _build_graph_config(request: ChatRequest, *, correlation_id: str) -> dict[str, Any]:
    return {
        "configurable": {
            "correlation_id": correlation_id,
            "user_id": request.metadata.user_id,
            "tenant_id": request.metadata.tenant_id,
            "thread_id": request.metadata.thread_id,
            "schema_version": request.metadata.schema_version,
        },
    }


def _build_graph_deps() -> GraphDeps:
    graph_settings = load_graph_settings()
    llm_registry: LlmRegistry | None = None
    llm_settings = load_llm_settings()
    try:
        llm_registry = build_llm_registry(llm_settings)
    except ValueError:
        if llm_settings.required:
            raise
        logger.warning("LLM credentials missing; runtime will use fallback graph behavior.")
        llm_registry = None

    return GraphDeps(
        llm_registry=llm_registry,
        sql_executor=build_sql_executor(graph_settings),
        harness=AgentHarness(
            enabled=bool(graph_settings.harness_enabled),
            audit_jsonl_path=graph_settings.harness_audit_jsonl_path,
        ),
        settings=graph_settings,
    )


def _build_tool_registry(deps: GraphDeps) -> ToolRegistry:
    registry = ToolRegistry()
    tools: list[Any] = [
        SqlQueryTool(deps),
        SchemaExploreTool(deps),
        CatalogDraftTool(deps),
        InventoryDraftTool(deps),
    ]
    settings = deps.settings
    # P3 — data validator (gated; keeps the flags-off manifest unchanged for regression).
    if bool(getattr(settings, "agentic_data_validator_enabled", False)):
        tools.append(DataValidatorTool())
    # P4 — answer composer + chart + erp guide (gated together).
    if bool(getattr(settings, "agentic_answer_composer_enabled", False)):
        tools.extend((AnswerComposerTool(), BuildChartTool(), DataTableBuilderTool(), ErpGuideTool()))
    for tool in tools:
        registry.register(tool.manifest, tool)
    return registry


def _should_use_harness_loop(request: ChatRequest, graph_settings: Any) -> bool:
    if not bool(getattr(graph_settings, "harness_loop_enabled", False)):
        return False
    if _clarification_response(request) is not None:
        return True
    allowed = {
        str(item).strip()
        for item in (getattr(graph_settings, "harness_loop_intents", None) or HARNESS_LOOP_INTENTS)
        if str(item).strip()
    }
    intent = _quick_classify_harness_intent(request.message)
    return intent in allowed


def _quick_classify_harness_intent(message: str) -> str:
    """Best-effort intent label for the harness route.

    Only the write-style intents (drafts) and schema exploration are detected by
    keyword, because they map to dedicated tool flows. Everything else defaults to
    ``data_query`` so any read-style question reliably enters the harness loop —
    the harness planner LLM then decides whether to call a tool or answer directly
    (incl. politely declining out-of-scope questions). Keyword precision is no
    longer load-bearing for read queries; it only affects the logged label.
    """
    text = (message or "").lower()
    if any(token in text for token in ("tạo phiếu", "nhập kho", "xuất kho", "inventory draft", "stock receipt")):
        return "inventory_draft"
    if any(token in text for token in ("tạo sản phẩm", "tạo danh mục", "catalog", "product draft")):
        return "catalog_draft"
    if any(token in text for token in ("schema", "bảng nào", "cột nào", "join")):
        return "schema_explore"
    return "data_query"


def _build_turn_context(
    request: ChatRequest,
    *,
    correlation_id: str,
    bearer_token: str | None,
    pending_hitl_tool: str | None = None,
    pending_hitl_payload: dict[str, Any] | None = None,
) -> TurnContext:
    return TurnContext(
        tenant_id=request.metadata.tenant_id,
        user_id=request.metadata.user_id,
        thread_id=request.metadata.thread_id,
        correlation_id=correlation_id,
        bearer_token=bearer_token,
        schema_version=request.metadata.schema_version,
        clarification_response=_clarification_response(request),
        pending_hitl_tool=pending_hitl_tool,
        pending_hitl_payload=pending_hitl_payload,
        role=str(getattr(request.metadata, "role", "") or "") or None,
        permissions=_metadata_permissions(request.metadata),
    )


def _metadata_permissions(metadata: Any) -> tuple[str, ...]:
    raw = getattr(metadata, "permissions", ()) or getattr(metadata, "scopes", ()) or ()
    if isinstance(raw, str):
        items = [item.strip() for item in raw.replace(",", " ").split()]
    else:
        items = [str(item).strip() for item in raw if str(item).strip()]
    return tuple(items)


async def _harness_events(
    orchestrator: HarnessOrchestrator,
    request: ChatRequest,
    *,
    correlation_id: str,
    bearer_token: str | None,
    pending_hitl_tool: str | None = None,
    pending_hitl_payload: dict[str, Any] | None = None,
    pending_clarify_payload: dict[str, Any] | None = None,
) -> AsyncIterator[Any]:
    scratchpad = TurnScratchpad(
        messages=[HumanMessage(content=_resume_scratchpad_message(request, pending_clarify_payload))]
    )
    ctx = _build_turn_context(
        request,
        correlation_id=correlation_id,
        bearer_token=bearer_token,
        pending_hitl_tool=pending_hitl_tool,
        pending_hitl_payload=pending_hitl_payload,
    )
    async for event in orchestrator.run(scratchpad, ctx):
        yield event


def _iter_harness_stream(
    orchestrator: HarnessOrchestrator,
    request: ChatRequest,
    *,
    graph_settings: Any,
    correlation_id: str,
    bearer_token: str | None,
    pending_hitl_tool: str | None = None,
    pending_hitl_payload: dict[str, Any] | None = None,
    pending_clarify_payload: dict[str, Any] | None = None,
    on_pending_hitl: Any | None = None,
    on_pending_clarify: Any | None = None,
    on_resume_success: Any | None = None,
) -> Iterator[Any]:
    _ = graph_settings
    agen = _harness_events(
        orchestrator,
        request,
        correlation_id=correlation_id,
        bearer_token=bearer_token,
        pending_hitl_tool=pending_hitl_tool,
        pending_hitl_payload=pending_hitl_payload,
        pending_clarify_payload=pending_clarify_payload,
    )
    loop = asyncio.new_event_loop()
    try:
        while True:
            try:
                event = loop.run_until_complete(agen.__anext__())
            except StopAsyncIteration:
                break
            if isinstance(event, PendingHitlEvent) and on_pending_hitl is not None:
                on_pending_hitl(event.spec)
            if isinstance(event, ClarifyEvent) and on_pending_clarify is not None:
                on_pending_clarify(event)
            if isinstance(event, FinalAnswerEvent) and on_resume_success is not None:
                on_resume_success()
            yield _event_to_stream_chunk(event)
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()


def _resume_scratchpad_message(
    request: ChatRequest,
    pending_clarify_payload: dict[str, Any] | None = None,
) -> str:
    """Resolve the question to run when resuming a harness data_query clarification.

    If the user accepted the suggested rewrite, use it verbatim. For a free-form
    reply, recombine the original question (carried in continuationContext) with the
    answer so the planner keeps full context. Draft HITL resumes are untouched.
    """
    answer = request.message
    clar = _clarification_response(request)
    if not clar:
        return answer
    cc = clar.get("continuation_context") or {}
    kind = cc.get("clarifyKind") or clar.get("clarify_kind")
    if kind != "harness_data_query":
        return answer
    rewrite = str(clar.get("suggested_rewrite") or "").strip()
    if rewrite:
        return rewrite
    pending = pending_clarify_payload if isinstance(pending_clarify_payload, dict) else {}
    original = str(cc.get("originalQuestion") or pending.get("originalQuestion") or "").strip()
    if original and original != answer.strip():
        return f"{original}\n\nNgười dùng trả lời câu hỏi làm rõ: {answer}"
    return answer


def _clarification_response(request: ChatRequest) -> dict[str, Any] | None:
    clar = getattr(request.options, "clarification", None)
    if clar is None:
        return None
    if isinstance(clar, dict):
        return dict(clar)
    if hasattr(clar, "model_dump"):
        dumped = clar.model_dump(mode="json")
        return dict(dumped) if isinstance(dumped, dict) else None
    return None


def _pending_hitl_key(request: ChatRequest, *, correlation_id: str) -> str:
    return request.metadata.thread_id or correlation_id


def _tool_name_from_hitl_event(event_name: str) -> str | None:
    if event_name == "draft":
        return "catalog_draft"
    if event_name == "inventory_draft":
        return "inventory_draft"
    return None


def _harness_update_chunk(payload: dict[str, Any]) -> dict[str, Any]:
    """Wrap an SSE-bearing payload under a node key.

    ``routes._extract_partial_update`` flattens one level to unwrap LangGraph node
    names, so a bare ``{"query_table_sse": ...}`` would be flattened into its inner
    keys and the top-level key lost. Nesting under ``"harness"`` makes the payload
    survive that flatten exactly like a legacy ``{node: {state}}`` update.
    """
    return {"harness": payload}


def _event_to_stream_chunk(event: Any) -> Any:
    if isinstance(event, ProgressEvent):
        return ("custom", {"progress_text": event.text})
    if isinstance(event, FinalAnswerEvent):
        return ("custom", {"final_answer": event.text})
    if isinstance(event, ErrorEvent):
        return _harness_update_chunk({"error_payload": {"code": event.code, "message": event.message}})
    if isinstance(event, SsePayloadEvent):
        if event.event_name == "draft":
            return _harness_update_chunk({"catalog_draft_sse": event.payload})
        if event.event_name == "inventory_draft":
            return _harness_update_chunk({"inventory_draft_sse": event.payload})
        if event.event_name == "data_table":
            return _harness_update_chunk({"query_table_sse": event.payload})
        if event.event_name == "chart":
            return _harness_update_chunk({"chart_spec_final": event.payload})
        return _harness_update_chunk({f"{event.event_name}_sse": event.payload})
    if isinstance(event, ClarifyEvent):
        return _harness_update_chunk({"domain_clarify_sse": _build_clarify_sse(event)})
    if isinstance(event, PendingHitlEvent):
        return ("harness_control", {"suppress_done": True})
    return {"data": json.dumps(event, default=str, ensure_ascii=False)}


def _build_clarify_sse(event: ClarifyEvent) -> dict[str, Any]:
    """Build the clarify SSE payload in the shape the frontend already consumes.

    Mirrors the legacy domain_guard ``domain_clarify_sse`` contract. The original
    question is stashed in ``continuationContext`` so a free-form reply can be
    recombined with it on resume (see ``_resume_scratchpad_message``).
    """
    clarify_id = uuid4().hex
    return {
        "clarifyId": clarify_id,
        "clarifyKind": "harness_data_query",
        "questions": list(event.questions),
        "issues": [],
        "guideRefs": [],
        "originalQuestion": event.original_question,
        "suggestedRewrite": event.suggested_rewrite,
        "suggestedNormalized": event.suggested_rewrite,
        "matchedModules": [],
        "continuationContext": {
            "clarifyId": clarify_id,
            "clarifyKind": "harness_data_query",
            "originalQuestion": event.original_question,
        },
    }


@lru_cache(maxsize=1)
def get_graph_runtime() -> GraphRuntime:
    deps = _build_graph_deps()
    compiled = compile_agent_graph(deps, use_checkpointer=True)
    if not bool(getattr(deps.settings, "harness_loop_enabled", False)):
        logger.info("runtime=LangGraphRuntime (harness_loop_enabled=False)")
        return LangGraphRuntime(compiled, graph_settings=deps.settings)
    if deps.llm_registry is None:
        logger.warning("HARNESS_LOOP_ENABLED=true but LLM registry is missing; using legacy graph runtime.")
        return LangGraphRuntime(compiled, graph_settings=deps.settings)
    orchestrator = HarnessOrchestrator(
        llm_registry=deps.llm_registry,
        tool_registry=_build_tool_registry(deps),
        policy=HarnessPolicy(),
        settings=deps.settings,
        harness=deps.harness,
        plan_template_store=_build_plan_template_store(deps.settings),
        history_store=_build_history_store(deps.settings),
        memory_store=_build_conversation_memory_store(deps.settings),
    )
    logger.info("runtime=LangHarnessRuntime harness_loop_enabled=True intents=%s", HARNESS_LOOP_INTENTS)
    return LangHarnessRuntime(compiled, orchestrator, graph_settings=deps.settings)


def _build_plan_template_store(settings: Any) -> Any | None:
    if not bool(getattr(settings, "agentic_v3_plan_template_enabled", False)):
        return None
    path = getattr(settings, "agentic_v3_template_store_path", None)
    if path:
        return SqlitePlanTemplateStore(str(path))
    return InMemoryPlanTemplateStore()


def _build_history_store(settings: Any) -> Any | None:
    if not bool(getattr(settings, "agentic_v3_enabled", False)):
        return None
    path = getattr(settings, "agentic_v3_history_store_path", None)
    if path:
        return SqliteIntentHistoryStore(str(path))
    return InMemoryIntentHistoryStore()


def _build_conversation_memory_store(settings: Any) -> Any | None:
    if not bool(getattr(settings, "conversation_memory_enabled", True)):
        return None
    path = getattr(settings, "conversation_memory_store_path", None)
    if path:
        from app.harness.memory_store import SqliteConversationMemoryStore
        return SqliteConversationMemoryStore(str(path))
    from app.harness.memory_store import InMemoryConversationMemoryStore
    return InMemoryConversationMemoryStore()
