"""Thin adapter from API layer to compiled LangGraph runtime."""

from __future__ import annotations

import asyncio
import json
import logging
from functools import lru_cache
from collections.abc import AsyncIterator, Iterator
from typing import Any, Protocol

from langchain_core.messages import HumanMessage

from app.api.schemas import ChatRequest
from app.graph.feedback import empty_feedback
from app.config.graph_settings import load_graph_settings
from app.config.settings import load_llm_settings
from app.graph import compile_agent_graph, default_initial_state, iter_graph_stream
from app.graph.deps import GraphDeps
from app.graph.state import fresh_turn_overlay
from app.graph.tools import CatalogDraftTool, InventoryDraftTool, SchemaExploreTool, SqlQueryTool
from app.harness import (
    AgentHarness,
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
from app.llm.registry import LlmRegistry, build_llm_registry

logger = logging.getLogger(__name__)

HARNESS_LOOP_INTENTS = frozenset(
    {
        "sql_query",
        "data_query",
        "schema_explore",
        "catalog_draft",
        "inventory_draft",
        "system_data_query",
        "catalog_data_entry",
        "inventory_data_entry",
    }
)


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
    ) -> None:
        self._legacy = LangGraphRuntime(compiled, graph_settings=graph_settings)
        self._orchestrator = orchestrator
        self._graph_settings = graph_settings

    def invoke(
        self,
        request: ChatRequest,
        *,
        correlation_id: str,
        bearer_token: str | None = None,
    ) -> dict[str, Any]:
        return self._legacy.invoke(request, correlation_id=correlation_id, bearer_token=bearer_token)

    def stream(
        self,
        request: ChatRequest,
        *,
        correlation_id: str,
        bearer_token: str | None = None,
    ) -> Any:
        if not _should_use_harness_loop(request, self._graph_settings):
            return self._legacy.stream(request, correlation_id=correlation_id, bearer_token=bearer_token)
        return _iter_harness_stream(
            self._orchestrator,
            request,
            graph_settings=self._graph_settings,
            correlation_id=correlation_id,
            bearer_token=bearer_token,
        )


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
    for tool in (
        SqlQueryTool(deps),
        SchemaExploreTool(deps),
        CatalogDraftTool(deps),
        InventoryDraftTool(deps),
    ):
        registry.register(tool.manifest, tool)
    return registry


def _should_use_harness_loop(request: ChatRequest, graph_settings: Any) -> bool:
    if not bool(getattr(graph_settings, "harness_loop_enabled", False)):
        return False
    allowed = {
        str(item).strip()
        for item in (getattr(graph_settings, "harness_loop_intents", None) or HARNESS_LOOP_INTENTS)
        if str(item).strip()
    }
    intent = _quick_classify_harness_intent(request.message)
    return intent in allowed


def _quick_classify_harness_intent(message: str) -> str:
    text = (message or "").lower()
    if any(token in text for token in ("tạo phiếu", "nhập kho", "xuất kho", "inventory draft", "stock receipt")):
        return "inventory_draft"
    if any(token in text for token in ("tạo sản phẩm", "tạo danh mục", "catalog", "product draft")):
        return "catalog_draft"
    if any(token in text for token in ("schema", "bảng nào", "cột nào", "join")):
        return "schema_explore"
    if any(token in text for token in ("doanh thu", "chi phí", "tồn kho", "báo cáo", "thống kê", "danh sách")):
        return "data_query"
    return "chat_normal"


def _build_turn_context(
    request: ChatRequest,
    *,
    correlation_id: str,
    bearer_token: str | None,
) -> TurnContext:
    return TurnContext(
        tenant_id=request.metadata.tenant_id,
        user_id=request.metadata.user_id,
        thread_id=request.metadata.thread_id,
        correlation_id=correlation_id,
        bearer_token=bearer_token,
        schema_version=request.metadata.schema_version,
    )


async def _harness_events(
    orchestrator: HarnessOrchestrator,
    request: ChatRequest,
    *,
    correlation_id: str,
    bearer_token: str | None,
) -> AsyncIterator[Any]:
    scratchpad = TurnScratchpad(messages=[HumanMessage(content=request.message)])
    ctx = _build_turn_context(request, correlation_id=correlation_id, bearer_token=bearer_token)
    async for event in orchestrator.run(scratchpad, ctx):
        yield event


def _iter_harness_stream(
    orchestrator: HarnessOrchestrator,
    request: ChatRequest,
    *,
    graph_settings: Any,
    correlation_id: str,
    bearer_token: str | None,
) -> Iterator[Any]:
    _ = graph_settings
    agen = _harness_events(
        orchestrator,
        request,
        correlation_id=correlation_id,
        bearer_token=bearer_token,
    )
    loop = asyncio.new_event_loop()
    try:
        while True:
            try:
                event = loop.run_until_complete(agen.__anext__())
            except StopAsyncIteration:
                break
            yield _event_to_stream_chunk(event)
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()


def _event_to_stream_chunk(event: Any) -> Any:
    if isinstance(event, ProgressEvent):
        return ("custom", {"progress_text": event.text})
    if isinstance(event, FinalAnswerEvent):
        return ("custom", {"final_answer": event.text})
    if isinstance(event, ErrorEvent):
        return {"error_payload": {"code": event.code, "message": event.message}}
    if isinstance(event, SsePayloadEvent):
        if event.event_name == "draft":
            return {"catalog_draft_sse": event.payload}
        if event.event_name == "inventory_draft":
            return {"inventory_draft_sse": event.payload}
        if event.event_name == "data_table":
            return {"query_table_sse": event.payload}
        if event.event_name == "chart":
            return {"chart_spec_final": event.payload}
        return {f"{event.event_name}_sse": event.payload}
    if isinstance(event, PendingHitlEvent):
        return ("harness_control", {"suppress_done": True})
    return {"data": json.dumps(event, default=str, ensure_ascii=False)}


@lru_cache(maxsize=1)
def get_graph_runtime() -> GraphRuntime:
    deps = _build_graph_deps()
    compiled = compile_agent_graph(deps, use_checkpointer=True)
    if not bool(getattr(deps.settings, "harness_loop_enabled", False)):
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
    )
    return LangHarnessRuntime(compiled, orchestrator, graph_settings=deps.settings)
