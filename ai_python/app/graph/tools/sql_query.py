"""Simplified SQL query tool — no retry loop, LLM manages retry via conversation."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.graph.deps import GraphDeps
from app.graph.pg_schema_context import build_schema_artifact_from_postgres
from app.graph.sql_prompts import format_schema_block
from app.graph.sql_safety import enforce_read_only_sql, SqlSafetyError
from app.harness.capability import CapabilityMatrix
from app.harness.tool_registry import ToolManifest, ToolResult, TurnContext
from app.llm.schemas import SqlGenerationOutput
from app.prompts.load import load_agent_prompt

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
        self._capability = CapabilityMatrix()

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
                logger.warning("tool=sql_query schema_load_error=%s", err)
                return ToolResult(
                    ok=False,
                    output={"generated_sql": ""},
                    observation_text=f"Schema load failed: {err}",
                    error_message=f"Schema load failed: {err}",
                )
            schema_tables = list(artifact.tables.keys()) if hasattr(artifact, "tables") else []
            logger.info("tool=sql_query schema_loaded tables=%s table_names=%s",
                        len(schema_tables), schema_tables[:8])
        except Exception as exc:
            logger.exception("tool=sql_query schema_load_exception")
            return ToolResult(
                ok=False,
                output={"generated_sql": ""},
                observation_text=f"Schema load exception: {exc}",
                error_message=f"Schema load exception: {exc}",
            )

        # 2. Build system prompt with gen_sql.md skill + schema block
        skill_prompt = load_agent_prompt("gen_sql")
        schema_block = format_schema_block(artifact, selected_tables=None, enriched=True)
        system_prompt = f"{skill_prompt}\n\n## SCHEMA\n{schema_block}"
        logger.info("tool=sql_query prompt_built prompt_chars=%s schema_block_chars=%s",
                    len(system_prompt), len(schema_block))

        # 3. Call LLM to generate SQL
        sql = ""
        try:
            client = self._deps.llm_registry.get("sql_gen")
            llm_model = getattr(client, "_model", None) or getattr(client, "model", "?")
            logger.info("tool=sql_query llm_start model=%s question_chars=%s", llm_model, len(question))
            llm_result = await asyncio.to_thread(
                client.structured_predict,
                [SystemMessage(content=system_prompt), HumanMessage(content=question)],
                SqlGenerationOutput,
            )
            sql = (llm_result.sql or "").strip()
            explanation = llm_result.explanation or ""
            logger.info("tool=sql_query llm_done sql_preview=%s sql_len=%s explanation_preview=%s",
                        sql[:120].replace("\n", " "), len(sql), explanation[:80].replace("\n", " "))
        except Exception as exc:
            logger.exception("tool=sql_query llm_error")
            return ToolResult(
                ok=False,
                output={"generated_sql": sql},
                observation_text=f"LLM generation failed: {exc}",
                error_message=f"LLM generation failed: {exc}",
            )

        # 4. Safety check
        try:
            enforce_read_only_sql(sql)
            logger.info("tool=sql_query safety_check passed")
        except SqlSafetyError as exc:
            logger.warning("tool=sql_query safety_check blocked sql_preview=%s", sql[:80].replace("\n", " "))
            return ToolResult(
                ok=False,
                output={"generated_sql": sql},
                observation_text=f"SQL safety check failed: {exc}",
                error_message=f"SQL safety check failed: {exc}",
            )

        # 5. Execute SQL
        try:
            logger.info("tool=sql_query exec_start sql=%s", sql[:200].replace("\n", " "))
            result = await self._deps.sql_executor.aexecute(
                sql.rstrip("; \t\n"),
                tenant_id=ctx.tenant_id,
                correlation_id=ctx.correlation_id,
                bearer_token=ctx.bearer_token,
            )
            rows = result.get("rows", []) if isinstance(result, dict) else []
            logger.info("tool=sql_query exec_done rows=%s", len(rows))
        except Exception as exc:
            logger.exception("tool=sql_query exec_error")
            return ToolResult(
                ok=False,
                output={"generated_sql": sql},
                observation_text=f"SQL execution failed: {exc}",
                error_message=f"SQL execution failed: {exc}",
            )

        # 6. Mask sensitive columns for non-owner roles
        guard_on = bool(getattr(self._deps.settings, "agentic_capability_guard_enabled", False))
        if guard_on and rows:
            before_count = len(rows[0]) if rows else 0
            rows = self._capability.mask_columns(ctx.role, rows)
            after_count = len(rows[0]) if rows else 0
            logger.info("tool=sql_query column_mask role=%s guard_on=True cols_before=%s cols_after=%s",
                        ctx.role, before_count, after_count)
        elif guard_on:
            logger.info("tool=sql_query column_mask role=%s guard_on=True rows_empty=True", ctx.role)

        # 7. Return result
        total_ms = (time.monotonic() - _invoke_start) * 1000
        logger.info("tool_invoke_end tool=sql_query ok=True latency_ms=%.0f rows=%s",
                    total_ms, len(rows))
        observation = f"SQL trả về {len(rows)} dòng" if rows else "Không có dữ liệu (0 dòng)"

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
