"""Simplified SQL query tool — no retry loop, LLM manages retry via conversation."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from app.graph.deps import GraphDeps
from app.graph.pg_schema_context import build_schema_artifact_from_postgres
from app.graph.sql_prompts import format_schema_block
from app.graph.sql_safety import enforce_read_only_sql, SqlSafetyError
from app.harness.tool_registry import ToolManifest, ToolResult, TurnContext

logger = logging.getLogger(__name__)


class SqlQueryTool:
    manifest = ToolManifest(
        name="sql_query",
        description="Execute read-only SQL query against ERP database. Returns rows or error.",
        args_schema='{"question": "string"}',
        capability="data_read",
        output_schema='{"rows": "list[dict]", "generated_sql": "string", "explanation": "string"}',
        when_to_use="Need actual ERP data: numbers, lists, rows, aggregates from the database.",
        when_not_to_use="User only wants schema/structure (use schema_explore) or only wants to create a record.",
        risk_level="low",
        side_effect_class="read_only",
        produces=("rows",),
        result_ref_policy="result_ref",
        examples=("doanh thu tháng này", "liệt kê sản phẩm sắp hết hàng"),
    )

    def __init__(self, deps: GraphDeps) -> None:
        self._deps = deps

    async def invoke(self, args: dict[str, Any], ctx: TurnContext) -> ToolResult:
        _invoke_start = time.monotonic()
        logger.info("tool_invoke_start tool=sql_query question_preview=%s", args.get("question", "")[:120])

        question = str(args.get("question") or "").strip()
        if not question:
            return ToolResult(
                ok=False,
                output={"generated_sql": ""},
                observation_text="Question is required",
                error_message="Question is required",
            )

        # 1. Load schema from Postgres
        try:
            artifact, err = await asyncio.to_thread(
                build_schema_artifact_from_postgres, self._deps.settings, question
            )
            if err:
                logger.warning("schema load failed: %s", err)
                return ToolResult(
                    ok=False,
                    output={"generated_sql": ""},
                    observation_text=f"Schema load failed: {err}",
                    error_message=f"Schema load failed: {err}",
                )
        except Exception as exc:
            logger.exception("schema load exception")
            return ToolResult(
                ok=False,
                output={"generated_sql": ""},
                observation_text=f"Schema load exception: {exc}",
                error_message=f"Schema load exception: {exc}",
            )

        # 2. Build system prompt with gen_sql.md skill + schema block
        # Lazy imports to avoid circular dependency
        from app.prompts.load import load_agent_prompt

        skill_prompt = load_agent_prompt("gen_sql")
        schema_block = format_schema_block(artifact, selected_tables=None, enriched=True)
        system_prompt = f"{skill_prompt}\n\n## SCHEMA\n{schema_block}"

        # 3. Call LLM to generate SQL
        try:
            from app.llm.schemas import SqlGenerationOutput

            client = self._deps.llm_registry.get("sql_gen")
            llm_result = await asyncio.to_thread(
                client.structured_predict,
                [{"role": "user", "content": question}],
                SqlGenerationOutput,
                system=system_prompt,
            )
            sql = llm_result.sql.strip()
            explanation = llm_result.explanation or ""
        except Exception as exc:
            logger.exception("LLM generation failed")
            return ToolResult(
                ok=False,
                output={"generated_sql": sql if "sql" in dir() else ""},
                observation_text=f"LLM generation failed: {exc}",
                error_message=f"LLM generation failed: {exc}",
            )

        # 4. Safety check
        try:
            enforce_read_only_sql(sql)
        except SqlSafetyError as exc:
            logger.warning("SQL safety check failed: %s", exc)
            return ToolResult(
                ok=False,
                output={"generated_sql": sql},
                observation_text=f"SQL safety check failed: {exc}",
                error_message=f"SQL safety check failed: {exc}",
            )

        # 5. Execute SQL
        try:
            result = await self._deps.sql_executor.aexecute(
                sql.rstrip("; \t\n"),
                tenant_id=ctx.tenant_id,
                correlation_id=ctx.correlation_id,
                bearer_token=ctx.bearer_token,
            )
            rows = result.get("rows", []) if isinstance(result, dict) else []
        except Exception as exc:
            logger.exception("SQL execution failed")
            return ToolResult(
                ok=False,
                output={"generated_sql": sql},
                observation_text=f"SQL execution failed: {exc}",
                error_message=f"SQL execution failed: {exc}",
            )

        # 6. Return result
        logger.info("tool_invoke_end tool=sql_query latency_ms=%.0f rows=%s", (time.monotonic() - _invoke_start) * 1000, len(rows))

        observation = f"SQL rows: {len(rows)} rows returned" if rows else "No rows returned"

        return ToolResult(
            ok=True,
            output={
                "rows": rows,
                "generated_sql": sql,
                "explanation": explanation,
            },
            sse_payload={"_event": "data_table", "rows": rows} if rows else None,
            observation_text=observation,
        )
