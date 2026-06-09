"""Harness tool adapter for the SQL subgraph."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

from app.graph.deps import GraphDeps
from app.graph.tools._state import build_tool_state
from app.graph.validate_sql import is_llm_select_sql_shape
from app.harness.capability import CapabilityMatrix, sanitize_user_data
from app.harness.tool_registry import ToolManifest, ToolResult, TurnContext


def _format_rows_observation(rows: list[Any], *, sql: str = "") -> str:
    if not rows:
        return "Không có dữ liệu phù hợp với điều kiện bạn yêu cầu."
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
        analyze: Callable[[str, str], Awaitable[dict[str, Any]]] | None = None,
        query: str = "",
    ) -> None:
        self._sql_regen_max = max(0, int(sql_regen_max))
        self._sql_empty_retry_max = max(0, int(sql_empty_retry_max))
        self._generate = generate
        self._review = review
        self._execute = execute
        self._analyze = analyze
        self._query = query
        self._last_analyze_result: dict[str, Any] = {}

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
            if not sql:
                if empty_retry >= self._sql_empty_retry_max:
                    return SelfCorrectingSqlResult(
                        ok=False,
                        sql=sql,
                        regen_count=regen,
                        empty_retry_count=empty_retry,
                        warning="Intent verification requested regeneration but retry budget exhausted.",
                    )
                empty_retry += 1
                continue
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
                # SQL passed review — analyze empty result for suspicious patterns
                analyze_warning = ""
                if self._analyze is not None:
                    try:
                        analyze_result = await self._analyze(sql, self._query)
                        analyze_warning = (analyze_result or {}).get("warning", "")
                        self._last_analyze_result = analyze_result or {}
                    except Exception as exc:
                        logger.warning("analyze_empty_result failed: %s", exc)
                return SelfCorrectingSqlResult(
                    ok=True,
                    rows=last_rows,
                    sql=last_sql,
                    regen_count=regen,
                    empty_retry_count=empty_retry,
                    degraded=False,
                    warning=analyze_warning,
                )
            return SelfCorrectingSqlResult(
                ok=True,
                rows=last_rows,
                sql=last_sql,
                regen_count=regen,
                empty_retry_count=empty_retry,
            )


def _sql_failure_signature(sql: str, issues: list[str]) -> str:
    raw = json.dumps({"sql": sql, "issues": issues}, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class SqlQueryTool:
    manifest = ToolManifest(
        name="sql_query",
        description="Read ERP data using the SQL subgraph. Input can be a natural-language data question.",
        args_schema='{"query": "string"}',
        capability="data_read",
        output_schema='{"rows": "list[dict]", "generated_sql": "string"}',
        when_to_use="Need actual ERP data: numbers, lists, rows, aggregates from the database.",
        when_not_to_use="User only wants schema/structure (use schema_explore) or only wants to create a record (use a draft tool).",
        risk_level="low",
        side_effect_class="read_only",
        produces=("rows",),
        result_ref_policy="result_ref",
        examples=("doanh thu tháng này", "liệt kê sản phẩm sắp hết hàng"),
    )

    def __init__(
        self,
        deps: GraphDeps,
        *,
        _test_generate: Any | None = None,
        _test_review: Any | None = None,
        _test_execute: Any | None = None,
    ) -> None:
        self._deps = deps
        self._capability = CapabilityMatrix()
        self._test_generate = _test_generate
        self._test_review = _test_review
        self._test_execute = _test_execute

    def _make_callables(self, query: str, ctx: TurnContext):
        """Return (generate, review, execute, analyze) async callables for the runner."""
        if self._test_generate is not None:
            return self._test_generate, self._test_review, self._test_execute

        from app.graph.feedback import append_feedback
        from app.graph.nodes.sql_pipeline import make_gen_sql_node, make_sql_review_node

        gen_node = make_gen_sql_node(self._deps)
        review_node = make_sql_review_node(self._deps)
        shared: dict[str, Any] = dict(build_tool_state(query, ctx, self._deps.settings))

        async def generate(hint: str | None) -> str:
            nonlocal shared
            if hint:
                shared = {**shared, "validation_feedback": append_feedback(shared, "sql_fix", str(hint))}
            if deps.settings.entity_resolution_enabled and "entity_context" not in shared:
                try:
                    from app.graph.entity_resolution import resolve_entities_for_domain
                    from app.graph.sql_query_domain import detect_sql_query_domain

                    domain = detect_sql_query_domain(query)
                    if domain != "generic":
                        entity_context = await resolve_entities_for_domain(
                            deps, ctx.tenant_id, query, domain
                        )
                        if entity_context:
                            shared = {**shared, "entity_context": entity_context}
                except Exception as exc:
                    logger.warning("entity resolution (thin adapter) failed: %s", exc)
            result = await asyncio.to_thread(gen_node, shared)
            shared = {**shared, **result}
            sql = str(shared.get("generated_sql") or "")
            # Lightweight intent check after generation (verify_sql_intent heuristic)
            if sql:
                from app.graph.sql_query_domain import detect_sql_query_domain
                from app.graph.verify_sql_intent import _fallback_verify
                domain = detect_sql_query_domain(query)
                verify = _fallback_verify(sql, domain)
                if verify.get("action") == "regen":
                    reason = verify.get("reason", "SQL does not match intent")
                    logger.warning("intent check triggered regen: %s", reason)
                    shared["validation_feedback"] = append_feedback(shared, "sql_fix", reason)
                    return ""
            return sql

        async def review(sql: str) -> dict[str, Any]:
            nonlocal shared
            state_for_review = {**shared, "generated_sql": sql}
            result = await asyncio.to_thread(review_node, state_for_review)
            ok = bool(result.get("sql_review_ok", True))
            if ok:
                return {"ok": True, "issues": []}
            new_fb = result.get("validation_feedback") or {}
            issues: list[str] = []
            if isinstance(new_fb, dict):
                for bucket in ("policy", "exec", "sql_fix"):
                    items = new_fb.get(bucket, [])
                    if items:
                        issues.append(str(items[-1]))
                        break
            shared = {**shared, **result}
            return {"ok": False, "issues": issues or ["sql review failed"], "retry_hint": "; ".join(issues)}

        async def execute(sql: str) -> list[dict[str, Any]]:
            result = await self._deps.sql_executor.aexecute(
                sql.rstrip("; \t\n"),
                tenant_id=ctx.tenant_id,
                correlation_id=ctx.correlation_id,
                bearer_token=ctx.bearer_token,
            )
            rows = result.get("rows", []) if isinstance(result, dict) else []
            return rows if isinstance(rows, list) else []

        async def analyze(sql: str, user_query: str) -> dict[str, Any]:
            """Run empty-result analysis when rows == 0."""
            from app.graph.analyze_empty_result import _analyze_empty_heuristic
            from app.graph.sql_query_domain import detect_sql_query_domain

            domain = detect_sql_query_domain(user_query)
            result = _analyze_empty_heuristic(sql, user_query, domain)
            return {
                "verdict": result.get("verdict", "legitimate"),
                "warning": result.get("warning", ""),
                "reason": result.get("reason", ""),
            }

        return generate, review, execute, analyze

    async def invoke(self, args: dict[str, Any], ctx: TurnContext) -> ToolResult:
        query = str(args.get("query") or args.get("sql") or "").strip()
        settings = self._deps.settings
        regen_max = int(getattr(settings, "sql_regen_max", 3))
        empty_retry_max = int(getattr(settings, "sql_empty_retry_max", 2))

        callables = self._make_callables(query, ctx)
        generate, review, execute = callables[:3]
        analyze = callables[3] if len(callables) > 3 else None
        runner = SelfCorrectingSqlRunner(
            sql_regen_max=regen_max,
            sql_empty_retry_max=empty_retry_max,
            generate=generate,
            review=review,
            execute=execute,
            analyze=analyze,
            query=query,
        )
        runner_result = await runner.run()

        rows = runner_result.rows
        sql = runner_result.sql

        sse: dict[str, Any] | None = {"_event": "data_table", "rows": rows} if rows else None

        # P6 — role-based sensitive-column masking at tool OUTPUT boundary.
        guard_on = bool(getattr(settings, "agentic_capability_guard_enabled", False))
        if guard_on:
            rows = self._capability.mask_columns(ctx.role, rows)
            sse = {"_event": "data_table", "rows": rows} if rows else None

        observation = _format_rows_observation(rows, sql=sql)
        if runner_result.warning:
            observation = f"{runner_result.warning}\n{observation}"
        if guard_on:
            observation = sanitize_user_data(observation)

        return ToolResult(
            ok=runner_result.ok,
            output={"query_result": {"rows": rows}, "generated_sql": sql},
            observation_text=observation,
            sse_payload=sse,
        )
