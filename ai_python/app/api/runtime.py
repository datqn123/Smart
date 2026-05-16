"""Thin adapter from API layer to compiled LangGraph runtime."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any, Protocol

from langchain_core.messages import HumanMessage

from app.api.schemas import ChatRequest
from app.graph.feedback import empty_feedback
from app.config.graph_settings import load_graph_settings
from app.config.settings import load_llm_settings
from app.graph import compile_agent_graph, default_initial_state, iter_graph_stream
from app.graph.deps import GraphDeps
from app.graph.sql_executor import build_sql_executor
from app.llm.registry import LlmRegistry, build_llm_registry

logger = logging.getLogger(__name__)


class GraphRuntime(Protocol):
    def invoke(self, request: ChatRequest, *, correlation_id: str) -> dict[str, Any]:
        ...

    def stream(self, request: ChatRequest, *, correlation_id: str) -> Any:
        ...


class LangGraphRuntime:
    def __init__(self, compiled: Any) -> None:
        self._compiled = compiled

    def invoke(self, request: ChatRequest, *, correlation_id: str) -> dict[str, Any]:
        state = _build_state(request=request, correlation_id=correlation_id)
        config = _build_graph_config(request, correlation_id=correlation_id)
        out = self._compiled.invoke(state, config)
        return dict(out or {})

    def stream(self, request: ChatRequest, *, correlation_id: str) -> Any:
        state = _build_state(request=request, correlation_id=correlation_id)
        config = _build_graph_config(request, correlation_id=correlation_id)
        return iter_graph_stream(
            self._compiled,
            state,
            config=config,
            correlation_id=correlation_id,
        )


def _build_state(*, request: ChatRequest, correlation_id: str) -> dict[str, Any]:
    state = dict(default_initial_state())
    state["messages"] = [HumanMessage(content=request.message)]
    state["correlation_id"] = correlation_id
    state["user_id"] = request.metadata.user_id
    state["tenant_id"] = request.metadata.tenant_id
    state["thread_id"] = request.metadata.thread_id
    state["schema_version"] = request.metadata.schema_version
    # Fresh turn: do not let checkpointed SQL channel bleed into this answer.
    state["query_result"] = None
    state["generated_sql"] = None
    state["final_answer"] = None
    state["error_payload"] = None
    state["intent"] = None
    state["sql_review_ok"] = None
    state["sql_valid"] = None
    state["result_ok"] = None
    state["result_empty"] = None
    state["runtime_schema_artifact"] = None
    state["selected_tables"] = None
    state["sql_gen_mode"] = None
    state["sql_attempt_history"] = None
    state["sql_local_pool"] = None
    state["validation_feedback"] = empty_feedback()
    state["idea_data_request"] = None
    state["idea_chart_idea"] = None
    state["chart_spec_draft"] = None
    state["chart_spec_final"] = None
    state["schema_plan"] = None
    state["ledger_metric_id"] = None
    state["schema_join_hints"] = None
    state["chart_brief"] = None
    state["chart_thread_context"] = None
    state["chart_data_ok"] = None
    state["chart_data_issues"] = None
    state["chart_warnings"] = None
    state["chart_retry_hint"] = None
    state["chart_result_profile"] = None
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
        settings=graph_settings,
    )


@lru_cache(maxsize=1)
def get_graph_runtime() -> GraphRuntime:
    deps = _build_graph_deps()
    compiled = compile_agent_graph(deps, use_checkpointer=True)
    return LangGraphRuntime(compiled)
