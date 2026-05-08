"""LangGraph assembly for Task003 read slice (ADR topology, no interrupt)."""

from __future__ import annotations

import operator
import time
import uuid
from typing import Annotated, Any, Literal, NotRequired, TypedDict, cast

from langgraph.graph import END, START, StateGraph

from ..contracts import McpToolError, QueryReadonlyIn, SearchDocsIn
from ..contracts.sse_envelope import (
    ErrorPayload,
    TokenPayload,
    ToolCallPayload,
    ToolResultPayload,
    map_guard_refusal,
    sse_error_message_for_mcp,
)
from ..mcp.db_readonly_port import DbReadonlyMcpPort
from ..mcp.vector_rag_port import VectorRagMcpPort
from ..observability import ToolAuditRecord, log_tool_audit
from ..registry.templates import validate_template_params
from ..tools.db_readonly_tool import run_query_readonly_once
from .policy import (
    policy_probe_message,
    should_route_db_numeric,
    slice_intent_for_message,
    wants_clarify_branch,
)


class Task003GraphState(TypedDict, total=False):
    user_message: str
    correlation_id: str
    user_id: NotRequired[str | None]
    session_id: NotRequired[str | None]

    refusal_code: NotRequired[str | None]
    clarify_only: NotRequired[bool]
    rag_failed: NotRequired[bool]
    last_mcp_error: NotRequired[McpToolError | None]

    needs_db: NotRequired[bool]
    readonly_gate_reason: NotRequired[str | None]

    rag_summary: NotRequired[str]
    rag_chunk_ids: NotRequired[list[str]]
    rag_namespaces: NotRequired[list[str]]

    db_summary: NotRequired[str | None]
    db_template_id: NotRequired[str | None]
    db_param_keys: NotRequired[list[str] | None]

    synthesis_directive: NotRequired[Literal["refuse", "clarify", "mcp_fail", "grounded"]]

    sse_out: Annotated[list[dict[str, Any]], operator.add]


def _redact_rag_args(body: SearchDocsIn) -> dict[str, Any]:
    return {"query_len": len(body.query), "top_k": body.top_k}


def _uuid() -> str:
    return str(uuid.uuid4())


async def node_ingest(state: Task003GraphState) -> dict[str, Any]:
    corr = state.get("correlation_id") or _uuid()
    return {"correlation_id": corr}


async def node_policy(state: Task003GraphState) -> dict[str, Any]:
    msg = state.get("user_message", "").strip()
    lowered = msg.lower()
    refusal = policy_probe_message(msg)
    if refusal:
        return {
            "refusal_code": refusal,
            "synthesis_directive": "refuse",
            "readonly_gate_reason": "policy_guard",
        }
    clarify = wants_clarify_branch(lowered)
    return {
        "clarify_only": clarify,
        "synthesis_directive": "clarify" if clarify else "grounded",
        "readonly_gate_reason": "ambiguous_sku_vs_order" if clarify else None,
    }


async def node_rag_mandatory(state: Task003GraphState, config: Any) -> dict[str, Any]:
    if state.get("synthesis_directive") == "refuse":
        return {}

    cmap = cast(dict[str, Any], config)
    cfg = cast(dict[str, Any], cmap.get("configurable") or {})
    rag: VectorRagMcpPort = cfg["rag"]
    corr = state["correlation_id"]
    user_id = state.get("user_id")
    session_id = state.get("session_id")
    msg = state.get("user_message", "")
    in_body = SearchDocsIn(query=msg, top_k=5)

    events: list[dict[str, Any]] = []

    # Schema MCP call
    events.append(
        {
            "event": "tool_call",
            "payload": ToolCallPayload(
                name="vector-rag.rag.search_schema",
                args=_redact_rag_args(in_body),
                status="started",
            ).model_dump(),
        }
    )
    t_s0 = time.perf_counter()
    schema_out, schema_err = await rag.rag_search_schema(in_body, correlation_id=corr)
    log_tool_audit(
        ToolAuditRecord(
            user_id=user_id,
            session_id=session_id,
            tool_name="vector-rag.rag.search_schema",
            correlation_id=corr,
            duration_ms=(time.perf_counter() - t_s0) * 1000,
        ),
        summary="redacted",
    )
    sch_ids: list[str] = []
    sch_sum = ""
    if schema_out:
        sch_ids = [c.id for c in schema_out.chunks]
        sch_sum = schema_out.summary
        events.append(
            {
                "event": "tool_result",
                "payload": ToolResultPayload(
                    name="vector-rag.rag.search_schema",
                    ok=True,
                    summary=schema_out.summary,
                ).model_dump(),
            }
        )
    elif schema_err:
        events.append(
            {
                "event": "tool_result",
                "payload": ToolResultPayload(
                    name="vector-rag.rag.search_schema",
                    ok=False,
                    summary=schema_err.message,
                ).model_dump(),
            }
        )

    # Docs MCP call
    events.append(
        {
            "event": "tool_call",
            "payload": ToolCallPayload(
                name="vector-rag.rag.search_docs",
                args=_redact_rag_args(in_body),
                status="started",
            ).model_dump(),
        }
    )
    t_d0 = time.perf_counter()
    docs_out, docs_err = await rag.rag_search_docs(in_body, correlation_id=corr)
    log_tool_audit(
        ToolAuditRecord(
            user_id=user_id,
            session_id=session_id,
            tool_name="vector-rag.rag.search_docs",
            correlation_id=corr,
            duration_ms=(time.perf_counter() - t_d0) * 1000,
        ),
        summary="redacted",
    )
    doc_ids: list[str] = []
    doc_sum = ""
    if docs_out:
        doc_ids = [c.id for c in docs_out.chunks]
        doc_sum = docs_out.summary
        events.append(
            {
                "event": "tool_result",
                "payload": ToolResultPayload(
                    name="vector-rag.rag.search_docs",
                    ok=True,
                    summary=docs_out.summary,
                ).model_dump(),
            }
        )
    elif docs_err:
        events.append(
            {
                "event": "tool_result",
                "payload": ToolResultPayload(
                    name="vector-rag.rag.search_docs",
                    ok=False,
                    summary=docs_err.message,
                ).model_dump(),
            }
        )

    namespaces = ["schema", "docs"]
    rag_ids = [*sch_ids, *doc_ids]
    rag_summary = f"{sch_sum}|{doc_sum}"

    if schema_err or docs_err:
        err = (
            schema_err
            or docs_err
            or McpToolError(
                code="RAG_UPSTREAM_ERROR",
                message="rag_failed",
                correlation_id=corr,
            )
        )
        return {
            "rag_failed": True,
            "last_mcp_error": err,
            "synthesis_directive": "mcp_fail",
            "rag_summary": rag_summary,
            "rag_chunk_ids": rag_ids,
            "rag_namespaces": namespaces,
            "sse_out": events,
            "needs_db": False,
            "readonly_gate_reason": "rag_error",
        }

    lowered = msg.lower()
    clarify = bool(state.get("clarify_only"))
    numeric = should_route_db_numeric(lowered)

    gate = "rag_only"
    needs_db = (not clarify) and numeric
    if clarify:
        gate = "clarify_branch"
        needs_db = False
    elif needs_db:
        gate = "rag_plus_db_aggregate"

    return {
        "rag_failed": False,
        "last_mcp_error": None,
        "rag_summary": rag_summary,
        "rag_chunk_ids": rag_ids,
        "rag_namespaces": namespaces,
        "needs_db": needs_db,
        "readonly_gate_reason": gate,
        "sse_out": events,
    }


async def node_db_maybe(state: Task003GraphState, config: Any) -> dict[str, Any]:
    if (
        state.get("rag_failed")
        or state.get("synthesis_directive") == "refuse"
        or not state.get("needs_db")
    ):
        return {}

    corr = state["correlation_id"]
    cmap = cast(dict[str, Any], config)
    cfg = cast(dict[str, Any], cmap.get("configurable") or {})
    db: DbReadonlyMcpPort | None = cfg.get("db")
    if db is None:
        return {
            "last_mcp_error": McpToolError(
                code="DB_UPSTREAM_ERROR",
                message="db-readonly MCP client not configured",
                retryable=False,
                correlation_id=corr,
            ),
            "readonly_gate_reason": "db_client_missing",
        }

    user_id = state.get("user_id")
    session_id = state.get("session_id")

    template_id = "sales_by_day_v1"
    params = {"days": 30}

    keys = frozenset(params.keys())
    ok_tpl, reason = validate_template_params(template_id, keys)
    if not ok_tpl:
        err_evt = ToolResultPayload(
            name="db-readonly.sql.query_readonly",
            ok=False,
            summary=f"TEMPLATE_VALIDATION::{reason}",
        )
        tc = ToolCallPayload(
            name="db-readonly.sql.query_readonly",
            args={"template_id": template_id, "param_keys": sorted(keys)},
            status="started",
        )
        return {
            "db_template_id": template_id,
            "db_param_keys": sorted(keys),
            "sse_out": [
                {"event": "tool_call", "payload": tc.model_dump()},
                {"event": "tool_result", "payload": err_evt.model_dump()},
            ],
            "readonly_gate_reason": state.get("readonly_gate_reason"),
        }

    call_args = {"template_id": template_id, "param_keys": sorted(keys)}
    qin = QueryReadonlyIn(template_id=template_id, params=params)

    events: list[dict[str, Any]] = []
    events.append(
        {
            "event": "tool_call",
            "payload": ToolCallPayload(
                name="db-readonly.sql.query_readonly",
                args=call_args,
                status="started",
            ).model_dump(),
        }
    )
    out, err = await run_query_readonly_once(
        db,
        qin,
        correlation_id=corr,
        user_id=user_id,
        session_id=session_id,
    )
    if err:
        events.append(
            {
                "event": "tool_result",
                "payload": ToolResultPayload(
                    name="db-readonly.sql.query_readonly",
                    ok=False,
                    summary=err.message,
                ).model_dump(),
            }
        )
        return {
            "last_mcp_error": err,
            "db_template_id": template_id,
            "db_param_keys": sorted(keys),
            "sse_out": events,
        }

    assert out is not None
    events.append(
        {
            "event": "tool_result",
            "payload": ToolResultPayload(
                name="db-readonly.sql.query_readonly",
                ok=True,
                summary=out.summary,
            ).model_dump(),
        }
    )
    return {
        "db_summary": out.summary,
        "db_template_id": template_id,
        "db_param_keys": sorted(keys),
        "sse_out": events,
        "last_mcp_error": None,
    }


def compile_task003_graph() -> Any:
    g = StateGraph(Task003GraphState)
    g.add_node("ingest", node_ingest)
    g.add_node("policy", node_policy)
    g.add_node("rag_mandatory", node_rag_mandatory)
    g.add_node("db_maybe", node_db_maybe)

    g.add_edge(START, "ingest")
    g.add_edge("ingest", "policy")
    g.add_edge("policy", "rag_mandatory")
    g.add_edge("rag_mandatory", "db_maybe")
    g.add_edge("db_maybe", END)
    return g.compile()


def summarize_public_side_effect(state: Task003GraphState) -> dict[str, Any]:
    lowered = state.get("user_message", "").lower()
    intent = slice_intent_for_message(lowered)
    return {
        "correlation_id": state.get("correlation_id"),
        "intent": intent,
        "needs_db_observed": bool(state.get("needs_db")),
        "readonly_gate_reason": state.get("readonly_gate_reason"),
        "rag_chunks": len(state.get("rag_chunk_ids") or []),
    }


def build_sse_error_event(code: str, message_fallback: str) -> dict[str, Any]:
    msg = sse_error_message_for_mcp(code, message_fallback)
    return {"event": "error", "payload": ErrorPayload(message=msg, code=code).model_dump()}


def build_sse_token(delta: str) -> dict[str, Any]:
    return {"event": "token", "payload": TokenPayload(delta=delta).model_dump()}


def refuse_token_event(code: str) -> dict[str, Any]:
    return build_sse_token(map_guard_refusal(code))
