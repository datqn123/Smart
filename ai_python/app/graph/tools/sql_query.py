"""Harness tool adapter for the SQL subgraph."""

from __future__ import annotations

import asyncio
import hashlib
import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from app.graph.deps import GraphDeps
from app.graph.sql_subgraph import build_sql_subgraph
from app.graph.tools._state import build_tool_config, build_tool_state
from app.graph.validate_sql import is_llm_select_sql_shape
from app.harness.capability import CapabilityMatrix, sanitize_user_data
from app.harness.tool_registry import ToolManifest, ToolResult, TurnContext


def _format_rows_observation(rows: list[Any], *, sql: str = "") -> str:
    if not rows:
        sql_hint = f" Executed SQL: {sql.strip()}" if sql.strip() else ""
        return (
            "SQL query returned 0 rows. The query ran fine, so this usually means the "
            "filter value does not exist or is not spelled exactly as in the database "
            "(e.g. a category/product name that only partially matches). Do NOT re-run "
            "the same query — either broaden the filter (case-insensitive partial "
            "match) or ask the user to confirm the exact value." + sql_hint
        )
    head = rows[:5]
    suffix = f" ... {len(rows)} rows total" if len(rows) > 5 else ""
    return f"SQL rows: {json.dumps(head, ensure_ascii=False, default=str)}{suffix}"


@dataclass
class SelfCorrectingSqlResult:
    ok: bool
    rows: list[dict[str, Any]] = field(default_factory=list)
    sql: str = ""
    regen_count: int = 0
    empty_retry_count: int = 0
    degraded: bool = False
    deduped: bool = False
    warning: str = ""


class SelfCorrectingSqlRunner:
    def __init__(
        self,
        *,
        sql_regen_max: int,
        sql_empty_retry_max: int,
        generate: Callable[[str | None], Awaitable[str]],
        review: Callable[[str], Awaitable[dict[str, Any]]],
        execute: Callable[[str], Awaitable[list[dict[str, Any]]]],
    ) -> None:
        self._sql_regen_max = max(0, int(sql_regen_max))
        self._sql_empty_retry_max = max(0, int(sql_empty_retry_max))
        self._generate = generate
        self._review = review
        self._execute = execute

    async def run(self) -> SelfCorrectingSqlResult:
        seen: set[str] = set()
        regen = 0
        empty_retry = 0
        hint: str | None = None
        last_sql = ""
        last_rows: list[dict[str, Any]] = []
        while True:
            sql = (await self._generate(hint)).strip()
            last_sql = sql
            if not is_llm_select_sql_shape(sql):
                return SelfCorrectingSqlResult(
                    ok=False,
                    sql=sql,
                    regen_count=regen,
                    empty_retry_count=empty_retry,
                    warning="read-only SQL policy blocked non-SELECT statement",
                )
            review = await self._review(sql)
            issues = [str(item) for item in review.get("issues", [])]
            if not bool(review.get("ok")):
                signature = _sql_failure_signature(sql, issues)
                if signature in seen:
                    return SelfCorrectingSqlResult(
                        ok=True,
                        rows=last_rows,
                        sql=last_sql,
                        regen_count=regen,
                        empty_retry_count=empty_retry,
                        degraded=True,
                        deduped=True,
                        warning="Cảnh báo: dừng vì SQL/lý do lỗi bị lặp.",
                    )
                seen.add(signature)
                if regen >= self._sql_regen_max:
                    return SelfCorrectingSqlResult(
                        ok=True,
                        rows=last_rows,
                        sql=last_sql,
                        regen_count=regen,
                        empty_retry_count=empty_retry,
                        degraded=True,
                        warning="Cảnh báo: đã hết ngân sách tự sửa SQL.",
                    )
                regen += 1
                hint = str(review.get("retry_hint") or "")
                continue
            rows = await self._execute(sql)
            last_rows = list(rows or [])
            if not last_rows:
                if empty_retry >= self._sql_empty_retry_max:
                    return SelfCorrectingSqlResult(
                        ok=True,
                        rows=last_rows,
                        sql=last_sql,
                        regen_count=regen,
                        empty_retry_count=empty_retry,
                        degraded=True,
                        warning="Cảnh báo: không tìm thấy dữ liệu sau khi retry.",
                    )
                empty_retry += 1
                hint = "empty result; broaden filter or ask for clarification"
                continue
            return SelfCorrectingSqlResult(
                ok=True,
                rows=last_rows,
                sql=last_sql,
                regen_count=regen,
                empty_retry_count=empty_retry,
            )


def _mask_sse_rows(
    sse: Any, role: str | None, capability: CapabilityMatrix
) -> Any:
    """Mask sensitive columns inside a data_table SSE payload for non-owner roles."""
    if not isinstance(sse, dict):
        return sse
    masked = dict(sse)
    for key, value in sse.items():
        if isinstance(value, list) and value and all(isinstance(item, dict) for item in value):
            masked[key] = capability.mask_columns(role, value)
    return masked


def _sql_failure_signature(sql: str, issues: list[str]) -> str:
    raw = json.dumps({"sql": sql, "issues": issues}, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class SqlQueryTool:
    manifest = ToolManifest(
        name="sql_query",
        description="Read ERP data using the SQL subgraph. Input can be a natural-language data question.",
        args_schema='{"query": "string"}',
    )

    def __init__(self, deps: GraphDeps, compiled: Any | None = None) -> None:
        self._deps = deps
        self._compiled = compiled or build_sql_subgraph(deps).compile()
        self._capability = CapabilityMatrix()

    async def invoke(self, args: dict[str, Any], ctx: TurnContext) -> ToolResult:
        query = str(args.get("query") or args.get("sql") or "").strip()
        state = build_tool_state(query, ctx, self._deps.settings)
        out = await asyncio.to_thread(self._compiled.invoke, state, build_tool_config(ctx))
        result = out.get("query_result") if isinstance(out, dict) else None
        rows = result.get("rows", []) if isinstance(result, dict) else []
        rows = rows if isinstance(rows, list) else []
        sse = out.get("query_table_sse") if isinstance(out, dict) else None
        executed_sql = str(out.get("generated_sql") or "") if isinstance(out, dict) else ""

        # P6 — role-based sensitive-column masking applied at the tool OUTPUT, so a
        # `SELECT *` cannot leak cost/margin/debt columns to a non-owner role.
        guard_on = bool(getattr(self._deps.settings, "agentic_capability_guard_enabled", False))
        if guard_on:
            rows = self._capability.mask_columns(ctx.role, rows)
            sse = _mask_sse_rows(sse, ctx.role, self._capability)

        if isinstance(sse, dict):
            sse = {"_event": "data_table", **sse}

        observation = _format_rows_observation(rows, sql=executed_sql)
        if guard_on:
            # P6 — strip embedded prompt-injection instructions carried inside data.
            observation = sanitize_user_data(observation)
        return ToolResult(
            ok=bool(out.get("result_ok")) if isinstance(out, dict) else False,
            output=dict(out or {}),
            observation_text=observation,
            sse_payload=sse if isinstance(sse, dict) else None,
        )
