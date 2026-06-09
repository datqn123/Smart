"""SQL subgraph nodes."""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.graph.agent_trace import emit_agent_trace
from app.graph.dbmeta import SchemaArtifact
from app.graph.deps import GraphDeps
from app.graph.feedback import (
    FeedbackSource,
    append_feedback,
    append_failure_signature,
    bump_attempts,
    empty_feedback,
    has_sql_fix_feedback,
    render_for_prompt,
    render_for_retry_prompt,
)
from app.graph.sql_review_hints import (
    compose_sql_review_fix_message,
    infer_retry_extra_tables,
)
from app.graph.progress import emit_progress
from app.graph.retry_policy import (
    RetryAction,
    chart_degrade_eligible,
    chart_degrade_state_patch,
    decide_sql_retry,
)
from app.graph.state import AgentState
from app.graph.erp_guide.format_context import format_domain_context_block
from app.graph.message_utils import (
    effective_user_question,
    format_dialog_tail_for_sql,
    latest_human_question,
)
from app.graph.logging_policy import safe_log_query_result, safe_log_sql
from app.graph.chart_calendar import resolve_month_calendar
from app.graph.enum_literals import enum_literals_prompt_block
from app.prompts.load import load_agent_json_contract, load_agent_prompt
from app.graph.chart_schema_merge import infer_tables_from_chart_context, merge_tables_into_artifact
from app.graph.sql_allowlist import (
    allowlist_tables_prompt_line,
    resolve_sql_allowlist,
    validation_allowlist_from_state,
)
from app.graph.interaction_mode import should_route_query_table
from app.graph.sql_prompts import (
    build_gen_sql_user_prompt,
    build_retry_rewrite_block,
    format_schema_block,
)
from app.graph.sql_similarity import max_pool_similarity
from app.graph.sql_query_domain import (
    detect_sql_query_domain,
    should_use_ledger_first_prompts,
    sql_hints_for_domain,
)
from app.graph.business_scope import (
    build_last_data_answer_context,
    check_sql_against_scope,
    ledger_metric_id_from_scope,
    merge_scope_reconcile_meta,
    reconcile_detail_rows_with_previous_total,
    render_business_scope_sql_block,
    render_last_data_answer_sql_block,
    resolve_business_scope,
    scope_effective_question,
)
from app.graph.sql_table_selection import (
    ensure_context_tables_for_question,
    ensure_domain_tables_for_question,
    ensure_price_tables_for_question,
    select_tables_for_question,
)
from app.graph.validate_sql import (
    check_ledger_metric_policy,
    is_llm_select_sql_shape,
    normalize_llm_sql_output,
    strip_trailing_semicolons,
    validate_sql_deterministic,
)
from app.llm.schemas import SqlReviewOutput
from app.harness import ToolCallContext

logger = logging.getLogger(__name__)

MAX_RESULT_ROWS = 50_000

_POLICY_ISSUE_HINT = re.compile(
    r"\b(limit|select|ddl|dml|insert|update|delete|drop)\b",
    re.IGNORECASE,
)
_DIVISION_ZERO_HINT = re.compile(r"division\s+by\s+zero", re.IGNORECASE)
_DATE_FILTER_HINT = re.compile(
    r"date\s+range|date\s+filter|explicit\s+date|time\s+range|temporal\s+filter|lack\s+of\s+.*date",
    re.IGNORECASE,
)
_STOCK_SNAPSHOT_Q = re.compile(
    r"hết\s*hàng|het\s*hang|tồn\s*kho|ton\s*kho|out\s+of\s+stock|low\s+stock|"
    r"sắp\s*hết|sap\s*het|inventory\s+level|stock\s+level|"
    r"còn\s*bao\s*nhiêu.*(tồn|hàng)|bao\s*nhiêu.*(hết|tồn)",
    re.IGNORECASE,
)
_COST_PRICE_Q = re.compile(
    r"giá\s*vốn|gia\s*von|cost\s*price|cost_price",
    re.IGNORECASE,
)
_FAKE_PPH_TABLE_HINT = re.compile(
    r"product_price_history|product_stock_prices|product-price-history",
    re.IGNORECASE,
)
_CANONICAL_PPH_IN_SQL = re.compile(r"\bproductpricehistory\b", re.IGNORECASE)
_JOIN_ON_IN_SQL = re.compile(r"\bjoin\b[\s\S]{0,400}?\bon\b", re.IGNORECASE)
# LLM sometimes echoes our structured-retry hint into `issues[]` — do not treat as SQL defects.
_STRUCTURED_PARSE_ECHO = re.compile(
    r"^Parse error:\s*Expecting value",
    re.IGNORECASE,
)

_SQL_REVIEW_SYSTEM = load_agent_prompt("sql_review")
_SQL_REVIEW_JSON_CONTRACT = load_agent_json_contract("sql_review") or ""


def _spurious_structured_parse_echo(issue: str) -> bool:
    t = issue.strip()
    if not t:
        return True
    if _STRUCTURED_PARSE_ECHO.match(t):
        return True
    return False


def _spurious_sql_review_issue(issue: str, sql: str, user_q: str = "") -> bool:
    """Drop common LLM reviewer false positives."""
    t = issue.lower()
    if _DIVISION_ZERO_HINT.search(issue) and "/" not in sql:
        return True
    if _DATE_FILTER_HINT.search(issue) and (
        _STOCK_SNAPSHOT_Q.search(user_q) or _COST_PRICE_Q.search(user_q)
    ):
        return True
    # Reviewer invents snake_case / alternate price tables; ERP canonical name is productpricehistory.
    if _FAKE_PPH_TABLE_HINT.search(issue) and _CANONICAL_PPH_IN_SQL.search(sql):
        return True
    if "productpricehistory" in t and "product_price_history" in t:
        return True
    if "join without on" in t.replace("-", " ") and _JOIN_ON_IN_SQL.search(sql):
        return True
    if re.search(r"latest\s+price\s+only|missing\s+filter\s+for\s+latest", issue, re.IGNORECASE):
        return True
    if "allowlisted table check needed" in t or (
        "allowlist" in t and "check needed" in t
    ):
        return True
    if "incorrect column name" in t and "product_stock_prices" in t:
        return True
    return False


def _benign_sql_review_issue(issue: str) -> bool:
    """
    sqlparse/Spring inject LIMIT on SELECT; reviewers often flag LIMIT+aggregate as 'redundant'.
    That is stylistic only — not a correctness or policy failure for our read-only executor.
    """
    t = issue.lower()
    if "limit" not in t:
        return False
    if not any(
        k in t
        for k in (
            "redundant",
            "unnecessary",
            "illogical",
            "incorrect",
            "single row",
            "only one row",
            "exactly one row",
        )
    ):
        return False
    return any(
        k in t
        for k in (
            "aggregate",
            "sum(",
            "count(",
            "avg(",
            "min(",
            "max(",
            "stddev",
            "variance",
        )
    )


def _last_user_message(state: AgentState) -> str:
    """Current user turn only (last HumanMessage), not prior assistant text."""
    return effective_user_question(
        state.get("messages"), state.get("normalized_user_question")
    )


def _build_failure_signature(kind: str, detail: str) -> str:
    text = " ".join(str(detail or "").strip().split())
    return f"{kind}:{text[:320]}".lower()


def _classify_sql_repair_kind(*, detail: str, source: FeedbackSource) -> str:
    d = (detail or "").lower()
    if "table not in allowlist" in d or "column not in allowlist" in d or "allowlist" in d:
        return "allowlist"
    if "parse" in d or "syntax" in d or "not a single postgresql select" in d:
        return "parse"
    if source == "exec":
        return "exec_upstream"
    if source == "result":
        return "empty_result"
    return "policy"


def _append_sql_repair_feedback(
    state: AgentState,
    *,
    source: FeedbackSource,
    detail: str,
    hint: str | None = None,
) -> dict[str, Any]:
    """Append source + structured sql_fix + failure signature."""
    kind = _classify_sql_repair_kind(detail=detail, source=source)
    out = append_feedback(state, source, detail)
    synthetic: AgentState = {**state, "validation_feedback": out}
    fix = (
        f"SQL repair [{kind}]: {detail}\n"
        "Rewrite previous SQL with minimal edits, keep SELECT-only, stay in allowlist, and keep LIMIT.\n"
    )
    if hint:
        fix += f"Retry hint: {hint.strip()}\n"
    out = append_feedback(synthetic, "sql_fix", fix.strip())
    synthetic = {**state, "validation_feedback": out}
    return append_failure_signature(
        synthetic,
        signature=_build_failure_signature(kind, detail),
    )


def _deterministic_validation_context(
    state: AgentState,
    deps: GraphDeps,
) -> tuple[list[str] | None, dict[str, set[str]] | None]:
    allowlist = None
    table_cols = None
    snap = state.get("runtime_schema_artifact")
    if isinstance(snap, dict):
        try:
            art = SchemaArtifact.model_validate(snap)
        except Exception:
            art = None
        if art is not None:
            try:
                full_cols = art.allowlist_columns_map()
                if deps.settings.sql_table_selection_enabled:
                    cap = int(deps.settings.sql_max_selected_tables) + int(
                        deps.settings.sql_allowlist_fk_extra_slots
                    )
                    allowlist = validation_allowlist_from_state(
                        art,
                        state,
                        fk_expand=bool(deps.settings.sql_allowlist_fk_expand),
                        fk_hops=int(deps.settings.sql_allowlist_fk_hops),
                        max_tables=cap,
                    )
                else:
                    allowlist = art.allowlist_table_names()
                if allowlist is not None:
                    table_cols = {t: cols for t, cols in full_cols.items() if t in allowlist}
            except Exception:
                allowlist = None
                table_cols = None
    return allowlist, table_cols


def _should_skip_sql_review_llm(
    *,
    deps: GraphDeps,
    state: AgentState,
    sql: str,
    user_q: str,
) -> tuple[bool, str]:
    if not deps.settings.sql_review_skip_low_risk:
        return False, ""
    if state.get("intent") != "system_data_query":
        return False, ""
    if detect_sql_query_domain(user_q) != "generic":
        return False, ""
    allowlist, table_cols = _deterministic_validation_context(state, deps)
    ok, detail, _, notes = validate_sql_deterministic(
        sql,
        deps.settings,
        allowlist_tables=allowlist,
        table_columns=table_cols,
    )
    if not ok:
        return False, detail or "deterministic check failed"
    if notes:
        return False, "; ".join(notes)
    return True, "deterministic pass + low-risk generic domain"


def _load_schema_artifact(
    deps: GraphDeps, _state: AgentState, *, user_q: str
) -> tuple[SchemaArtifact | None, Exception | None]:
    """Build schema from Postgres: ai_table_description registry + live catalog (no YAML)."""
    from app.graph.pg_schema_context import build_schema_artifact_from_postgres

    art, err = deps.harness.run_tool(
        tool_name="schema.build_artifact_from_postgres",
        tool=lambda: build_schema_artifact_from_postgres(deps.settings, user_q),
        context=ToolCallContext(tool_name="schema.build_artifact_from_postgres"),
    )
    if art is not None:
        return art, None
    msg = (err or "unknown postgres schema error").strip() or "unknown postgres schema error"
    return None, RuntimeError(msg)


def _build_gen_sql_system(
    allow_names: set[str],
    *,
    ledger_first: bool,
    month_calendar: bool = False,
) -> str:
    parts = [load_agent_prompt("gen_sql") + "\n"]
    if ledger_first and "financeledger" in allow_names:
        parts.append(
            "Revenue/expense/cashflow: use financeledger with transaction_type filters; "
            "transaction_date for periods.\n"
        )
    if "inventory" in allow_names:
        parts.append(
            "Stock level / out-of-stock / low-stock: use inventory as the fact table (current quantity). "
            "Join products for sku_code and name. Do NOT use products.status = 'Inactive' for out-of-stock. "
            "Do NOT derive stock from stockreceiptdetails or stockdispatch_lines.\n"
        )
    if "productpricehistory" in allow_names:
        parts.append(
            "Cost/sale price filters: table name is exactly **productpricehistory** "
            "(not product_price_history). Join productunits (is_base_unit) when matching unit_id. "
            "For «giá vốn > N» list products: join pph and filter pph.cost_price; "
            "use LATERAL/DISTINCT ON for latest price when needed.\n"
        )
    if "salesorders" in allow_names:
        parts.append(
            "Order counts by channel: use salesorders; filter order_channel = 'Retail' only when the "
            "brief explicitly targets retail/POS/bán lẻ. Use created_at for order date unless schema "
            "shows another date column.\n"
        )
    elif "stockdispatches" in allow_names:
        parts.append(
            "Shipment/dispatch metrics: use stockdispatches (e.g. dispatch_date), not salesorders.\n"
        )
    if month_calendar:
        parts.append(
            "Month calendar: when the prompt requires include_zero_months / calendar spine, "
            "you MUST use generate_series + LEFT JOIN so every month in range appears; "
            "use COALESCE(COUNT(...), 0) for empty months.\n"
        )
    now = datetime.now()
    parts.append(
        f"\nCurrent date: {now.strftime('%Y-%m-%d')} (current year = {now.year}). "
        f"When the user says \"năm nay\"/\"this year\", or names a month/quarter without a year "
        f"(e.g. \"tháng 2 đến tháng 5\"), the year is {now.year}. "
        f"Do NOT default to 2024 or any year other than {now.year} unless the user writes an "
        f"explicit different year. Example: \"doanh thu từ tháng 2 đến tháng 5 năm nay\" → "
        f"transaction_date BETWEEN '{now.year}-02-01' AND '{now.year}-05-31'.\n"
    )
    parts.append("\n" + enum_literals_prompt_block())
    return "".join(parts)


def _resolve_schema_artifact(
    deps: GraphDeps, state: AgentState, *, user_q: str
) -> tuple[SchemaArtifact | None, Exception | None]:
    """Prefer runtime_schema_artifact from schema_explore when present."""
    snap = state.get("runtime_schema_artifact")
    if isinstance(snap, dict):
        try:
            return SchemaArtifact.model_validate(snap), None
        except Exception as exc:
            logger.warning("runtime_schema_artifact invalid: %s", exc)
    return _load_schema_artifact(deps, state, user_q=user_q)


def make_gen_sql_node(deps: GraphDeps):
    """TASK-LG-09: increment sql_attempt_count at start of each gen_sql."""

    def gen_sql(state: AgentState) -> dict:
        logger.info("node=gen_sql action=start")
        prev = int(state.get("sql_attempt_count") or 0)
        seed_sql = normalize_llm_sql_output(state.get("generated_sql")) or None
        nxt = prev + 1
        bumped = bump_attempts(state)
        prev_fb = state.get("validation_feedback")
        if not isinstance(prev_fb, dict):
            fb_render = render_for_prompt(empty_feedback())
        elif nxt > 1:
            fb_render = render_for_retry_prompt(prev_fb)
        else:
            fb_render = render_for_prompt(prev_fb, max_items_per_bucket=8)
        force_exploit = nxt > 1 and (
            deps.settings.sql_exploit_on_retry
            or has_sql_fix_feedback(prev_fb if isinstance(prev_fb, dict) else None)
        )
        mode: str = "explore" if nxt == 1 else ("exploit" if force_exploit else "explore")
        reg = deps.llm_registry
        ver = state.get("schema_version")
        user_q = _last_user_message(state)
        previous_scope = state.get("last_business_scope") if isinstance(state.get("last_business_scope"), dict) else None
        previous_data_answer = state.get("last_data_answer") if isinstance(state.get("last_data_answer"), dict) else None
        clarification_ctx = (
            state.get("clarification_applied_context")
            if isinstance(state.get("clarification_applied_context"), dict)
            else None
        )
        clarification_scope = (
            clarification_ctx.get("scope_snapshot")
            if isinstance(clarification_ctx, dict) and isinstance(clarification_ctx.get("scope_snapshot"), dict)
            else None
        )
        clarification_prev_answer = (
            clarification_ctx.get("previous_data_answer")
            if isinstance(clarification_ctx, dict) and isinstance(clarification_ctx.get("previous_data_answer"), dict)
            else None
        )
        effective_previous_data_answer = clarification_prev_answer or previous_data_answer
        force_followup_inherit = bool(clarification_scope) and (
            str(clarification_ctx.get("clarify_kind") or "") == "data_followup_detail"
            if isinstance(clarification_ctx, dict)
            else False
        )
        scope = resolve_business_scope(
            user_q,
            intent=str(state.get("intent") or "") or None,
            previous_scope=clarification_scope or previous_scope,
            previous_data_answer=effective_previous_data_answer,
            force_followup_inherit=force_followup_inherit,
        )
        user_q_effective = scope_effective_question(user_q, scope)
        pre_err = state.get("error_payload")
        if isinstance(pre_err, dict) and pre_err.get("error") in (
            "schema_load_failed",
            "schema_catalog_failed",
        ):
            if not state.get("runtime_schema_artifact"):
                return {
                    **emit_progress(state, "gen_sql"),
                    "sql_attempt_count": prev,
                    "sql_repair_max_attempts": int(deps.settings.sql_repair_max_attempts),
                    "generated_sql": None,
                    "error_payload": pre_err,
                    "validation_feedback": bumped,
                }
        artifact, load_exc = _resolve_schema_artifact(deps, state, user_q=user_q)
        if load_exc is not None:
            logger.warning("schema load failed in gen_sql: %s", load_exc)
            fb = append_feedback(state, "policy", f"schema load failed: {load_exc}")
            emit_agent_trace(
                logger,
                deps.settings,
                agent="gen_sql",
                phase="Không tạo được SQL — lỗi schema",
                detail=f"schema_version={ver}\n{load_exc}",
            )
            return {
                **emit_progress(state, "gen_sql"),
                "sql_attempt_count": prev,
                "sql_repair_max_attempts": int(deps.settings.sql_repair_max_attempts),
                "generated_sql": None,
                "error_payload": {
                    "error": "schema_load_failed",
                    "schema_version": ver,
                    "detail": str(load_exc),
                },
                "validation_feedback": fb,
                "runtime_schema_artifact": None,
            }
        assert artifact is not None  # guaranteed when load_exc is None
        idea_req = state.get("idea_data_request")
        if not isinstance(idea_req, dict) or not idea_req:
            brief = state.get("chart_brief")
            if isinstance(brief, dict) and brief.get("data_request"):
                idea_req = dict(brief["data_request"])
        extra_tables = infer_tables_from_chart_context(user_q_effective, idea_req if isinstance(idea_req, dict) else None)
        if nxt > 1 and isinstance(prev_fb, dict):
            last_fix = (prev_fb.get("sql_fix") or [])[-1] if prev_fb.get("sql_fix") else ""
            retry_issues = list(prev_fb.get("intent_review") or [])[-3:]
            extra_tables = [
                *extra_tables,
                *infer_retry_extra_tables(
                    user_q=user_q_effective,
                    sql=seed_sql or "",
                    issues=retry_issues,
                    suggested_tables=None,
                ),
            ]
        if extra_tables or state.get("intent") == "system_data_chart":
            artifact = merge_tables_into_artifact(deps.settings, artifact, extra_tables)
        artifact_dump = artifact.model_dump(mode="json")
        selected_tables: list[str] | None = None
        schema_plan = state.get("schema_plan") if isinstance(state.get("schema_plan"), dict) else None
        if schema_plan and schema_plan.get("tables"):
            selected_tables = [str(t) for t in schema_plan["tables"] if str(t).strip()]
        elif extra_tables or state.get("intent") == "system_data_chart":
            selected_tables = [t.name for t in artifact.tables]
        elif deps.settings.sql_table_selection_enabled and not deps.settings.sql_schema_explorer_enabled:
            selected_tables = select_tables_for_question(
                deps=deps,
                user_q=user_q_effective,
                artifact=artifact,
                max_tables=int(deps.settings.sql_max_selected_tables),
                use_llm=bool(deps.settings.sql_table_pick_use_llm),
                min_tables_for_llm=int(deps.settings.sql_table_pick_min_tables_for_llm),
            )
        if selected_tables is not None:
            known_tbl = {t.name for t in artifact.tables}
            selected_tables = ensure_domain_tables_for_question(
                user_q_effective,
                selected_tables,
                max_tables=int(deps.settings.sql_max_selected_tables),
                known_tables=known_tbl,
            )
            selected_tables = ensure_context_tables_for_question(
                user_q_effective,
                selected_tables,
                max_tables=int(deps.settings.sql_max_selected_tables),
                known_tables=known_tbl,
            )
            selected_tables = ensure_price_tables_for_question(
                user_q_effective,
                selected_tables,
                max_tables=int(deps.settings.sql_max_selected_tables),
                known_tables=known_tbl,
            )
        sql_allowlist_tables: list[str] | None = None
        if selected_tables is not None and deps.settings.sql_table_selection_enabled:
            cap = int(deps.settings.sql_max_selected_tables) + int(
                deps.settings.sql_allowlist_fk_extra_slots
            )
            sql_allowlist_tables = resolve_sql_allowlist(
                artifact,
                selected_tables,
                fk_expand=bool(deps.settings.sql_allowlist_fk_expand),
                fk_hops=int(deps.settings.sql_allowlist_fk_hops),
                max_tables=cap,
            )
        query_domain = detect_sql_query_domain(user_q_effective)
        domain_hint_lines = sql_hints_for_domain(query_domain)
        enriched = (
            bool(deps.settings.sql_enriched_schema_prompt)
            or bool(schema_plan)
            or bool(deps.settings.sql_schema_explorer_enabled)
        )
        ledger_first = _effective_ledger_first_prompts(state, deps.settings)
        multi_table_plan = bool(selected_tables and len(selected_tables) > 1)
        schema_tables = (
            sql_allowlist_tables if sql_allowlist_tables else selected_tables
        )
        schema_block = format_schema_block(
            artifact,
            selected_tables=schema_tables,
            enriched=enriched,
        )
        dialog_tail = format_dialog_tail_for_sql(
            state.get("messages"),
            max_messages=int(deps.settings.sql_dialog_tail_max_messages),
            max_chars=int(deps.settings.sql_dialog_tail_max_chars),
            summary=state.get("conversation_summary"),
        )
        planner_json: str | None = None
        if isinstance(idea_req, dict) and idea_req:
            try:
                planner_json = json.dumps(idea_req, ensure_ascii=False)[:8000]
            except Exception:
                planner_json = None
        chart_ctx = (state.get("chart_thread_context") or "").strip() or None
        month_cal = resolve_month_calendar(
            user_q_effective,
            idea_req if isinstance(idea_req, dict) else None,
        )
        allow_line = allowlist_tables_prompt_line(sql_allowlist_tables, artifact)
        domain_block = format_domain_context_block(
            state.get("domain_context") if isinstance(state.get("domain_context"), dict) else None
        )
        if domain_hint_lines:
            extra = "Query domain hints:\n" + "\n".join(f"- {h}" for h in domain_hint_lines) + "\n\n"
            domain_block = (domain_block or "") + extra
        scope_block = render_business_scope_sql_block(scope)
        data_context_block = render_last_data_answer_sql_block(effective_previous_data_answer, scope)
        query_table_mode = should_route_query_table(state)
        pool = list(state.get("sql_local_pool") or [])
        dup_warn = False
        if nxt > 1 and seed_sql and pool:
            mx = max_pool_similarity(
                seed_sql,
                pool,
                token_weight=float(deps.settings.sql_similarity_token_weight),
            )
            dup_warn = mx >= float(deps.settings.sql_similarity_threshold)
        retry_rewrite = build_retry_rewrite_block(
            attempt=nxt,
            prior_sql=seed_sql if nxt > 1 else None,
            feedback_render=fb_render,
            duplicate_warning=dup_warn,
        )
        prompt = build_gen_sql_user_prompt(
            mode=mode,  # type: ignore[arg-type]
            schema_block=schema_block,
            feedback_render=fb_render,
            user_q=user_q_effective,
            seed_sql=seed_sql if mode == "exploit" else None,
            retry_rewrite_block=retry_rewrite or None,
            sql_limit_max=int(deps.settings.sql_limit_max),
            dialog_tail=dialog_tail or None,
            planner_data_request_json=planner_json,
            schema_plan=schema_plan,
            ledger_first=ledger_first,
            multi_table_plan=multi_table_plan,
            chart_thread_context=chart_ctx,
            allowed_tables_line=allow_line,
            month_calendar=month_cal,
            domain_context_block=domain_block,
            business_scope_block=scope_block or None,
            data_context_block=data_context_block or None,
            query_table_mode=query_table_mode,
        )
        if reg is None:
            sql = f"SELECT 1 AS ok LIMIT {deps.settings.sql_limit_max}"
            emit_agent_trace(
                logger,
                deps.settings,
                agent="gen_sql",
                phase="Sinh SQL (stub registry — SELECT cố định)",
                detail=f"lần_thử={nxt}\n{safe_log_sql(sql, settings=deps.settings)}",
            )
            out_none: dict = {
                **emit_progress(state, "gen_sql"),
                "sql_attempt_count": nxt,
                "sql_repair_max_attempts": int(deps.settings.sql_repair_max_attempts),
                "generated_sql": sql,
                "validation_feedback": bumped,
                "sql_gen_mode": mode,
                "runtime_schema_artifact": artifact_dump,
                "business_scope": scope,
                "last_business_scope": scope,
            }
            if selected_tables is not None:
                out_none["selected_tables"] = selected_tables
            if sql_allowlist_tables is not None:
                out_none["sql_allowlist_tables"] = sql_allowlist_tables
            return out_none
        allow_names = artifact.allowlist_table_names()
        _gen_sql_system = _build_gen_sql_system(
            allow_names,
            ledger_first=ledger_first,
            month_calendar=month_cal is not None,
        )
        entity_section = _build_entity_context_section(state)
        if entity_section:
            _gen_sql_system += "\n\n" + entity_section
        client = reg.get("sql_gen")
        sql = client.invoke_text(prompt, system=_gen_sql_system)
        sql_stripped = normalize_llm_sql_output(sql)
        fb_for_append = bumped
        if deps.settings.sql_hybrid_similarity_enabled and pool and sql_stripped:
            mx = max_pool_similarity(
                sql_stripped,
                pool,
                token_weight=float(deps.settings.sql_similarity_token_weight),
            )
            if mx >= float(deps.settings.sql_similarity_threshold):
                syn: AgentState = {**state, "validation_feedback": bumped}
                fb_for_append = append_feedback(
                    syn,
                    "policy",
                    (
                        "generated_sql is highly similar to a prior attempt in this thread "
                        f"(hybrid score≈{mx:.3f}); change structure or filters meaningfully."
                    ),
                )
        pool = (pool + [sql_stripped])[-int(deps.settings.sql_local_pool_max) :]
        hist = list(state.get("sql_attempt_history") or [])
        hist.append(sql_stripped[:2000])
        fb_note = fb_render if len(fb_render) <= 600 else fb_render[:600] + "…"
        emit_agent_trace(
            logger,
            deps.settings,
            agent="gen_sql",
            phase="Sinh SQL (LLM sql_gen)",
            detail=(
                f"lần_thử={nxt} schema_version={ver or '(none)'} mode={mode}\n"
                f"ngữ_cảnh_feedback:\n{fb_note}\n"
                f"câu_hỏi:\n{user_q_effective[:800]}{'…' if len(user_q_effective) > 800 else ''}\n"
                f"SQL:\n{safe_log_sql(sql_stripped, settings=deps.settings)}"
            ),
        )
        scope_metric_id = ledger_metric_id_from_scope(scope)
        out: dict = {
            **emit_progress(state, "gen_sql"),
            "sql_attempt_count": nxt,
            "sql_repair_max_attempts": int(deps.settings.sql_repair_max_attempts),
            "generated_sql": sql_stripped,
            "validation_feedback": fb_for_append,
            "sql_gen_mode": mode,
            "sql_local_pool": pool,
            "sql_attempt_history": hist[-32:],
            "runtime_schema_artifact": artifact_dump,
            "business_scope": scope,
            "last_business_scope": scope,
        }
        if (
            state.get("intent") == "system_data_query"
            and scope_metric_id
            and not state.get("ledger_metric_id")
        ):
            out["ledger_metric_id"] = scope_metric_id
        if selected_tables is not None:
            out["selected_tables"] = selected_tables
        if sql_allowlist_tables is not None:
            out["sql_allowlist_tables"] = sql_allowlist_tables
        return out

    return gen_sql


def make_sql_review_node(deps: GraphDeps):
    def sql_review(state: AgentState) -> dict:
        logger.info("node=sql_review action=start")
        reg = deps.llm_registry
        sql = state.get("generated_sql") or ""
        if reg is None:
            emit_agent_trace(
                logger,
                deps.settings,
                agent="sql_review",
                phase="Bỏ qua review (không có LLM registry)",
                detail="ok=True (mặc định)",
            )
            return {**emit_progress(state, "sql_review"), "sql_review_ok": True}
        if not is_llm_select_sql_shape(sql):
            msg = (
                "Output is not a single PostgreSQL SELECT. "
                "Return only one SELECT … statement with LIMIT; no Vietnamese/English prose."
            )
            emit_agent_trace(
                logger,
                deps.settings,
                agent="sql_review",
                phase="Từ chối — không phải SELECT (kiểm tra tĩnh)",
                detail=f"snippet:\n{safe_log_sql(sql, settings=deps.settings)[:800]}",
            )
            return {
                **emit_progress(state, "sql_review"),
                "sql_review_ok": False,
                "validation_feedback": _append_sql_repair_feedback(
                    state,
                    source="policy",
                    detail=msg,
                ),
            }
        client = reg.get("sql_review")
        user_q = scope_effective_question(
            _last_user_message(state),
            state.get("business_scope") if isinstance(state.get("business_scope"), dict) else None,
        )
        skip_review, skip_reason = _should_skip_sql_review_llm(
            deps=deps,
            state=state,
            sql=sql,
            user_q=user_q,
        )
        if skip_review:
            emit_agent_trace(
                logger,
                deps.settings,
                agent="sql_review",
                phase="Bỏ qua review LLM (low-risk)",
                detail=f"ok=True; reason={skip_reason}",
            )
            return {**emit_progress(state, "sql_review"), "sql_review_ok": True}
        allow_block = ""
        snap = state.get("runtime_schema_artifact")
        if isinstance(snap, dict):
            try:
                art = SchemaArtifact.model_validate(snap)
                eff = state.get("sql_allowlist_tables")
                if isinstance(eff, list) and eff:
                    names = sorted({str(x) for x in eff if str(x).strip()})
                else:
                    names = sorted(art.allowlist_table_names())
                if names:
                    allow_block = (
                        "Allowlisted table names (use exact spelling from this list):\n"
                        + ", ".join(names[:100])
                        + "\n\n"
                    )
            except Exception:
                pass
        intent_line = ""
        if state.get("intent"):
            intent_line = f"Pipeline intent: {state.get('intent')}\n\n"
        review_body = (
            f"{allow_block}"
            f"{intent_line}"
            "Review this SELECT-only SQL for safety and relevance to the user question. "
            "When rejecting, fill retry_hint with concrete tables, columns, filters, and GROUP BY. "
            "Use the JSON contract only in your reply.\n\n"
            f"User question:\n{user_q[:1200]}\n\n"
            f"```sql\n{sql}\n```"
        )
        try:
            out = client.structured_predict(
                [
                    SystemMessage(content=_SQL_REVIEW_SYSTEM),
                    HumanMessage(content=review_body),
                ],
                SqlReviewOutput,
                json_output_contract=_SQL_REVIEW_JSON_CONTRACT,
                max_retries=int(deps.settings.sql_review_max_retries),
            )
        except Exception:
            logger.warning("sql_review structured_predict failed; passing review", exc_info=True)
            return {**emit_progress(state, "sql_review"), "sql_review_ok": True}
        issues_raw = list(out.issues or [])
        severe = [
            i
            for i in issues_raw
            if not _benign_sql_review_issue(i)
            and not _spurious_structured_parse_echo(i)
            and not _spurious_sql_review_issue(i, sql, user_q)
        ]
        ok = len(severe) == 0
        issues_txt = "\n".join(f"- {i}" for i in issues_raw) if issues_raw else "(no issues)"
        if issues_raw and ok and any(_benign_sql_review_issue(i) for i in issues_raw):
            issues_txt += "\n(bỏ qua cảnh báo nhẹ: LIMIT + aggregate — hợp lệ với executor read-only)"
        hint_preview = (out.retry_hint or "").strip()
        trace_detail = f"ok={ok}\n{issues_txt}"
        if hint_preview:
            trace_detail += f"\nretry_hint: {hint_preview[:500]}"
        emit_agent_trace(
            logger,
            deps.settings,
            agent="sql_review",
            phase="Đánh giá SQL (LLM)",
            detail=trace_detail,
        )
        upd: dict = {"sql_review_ok": ok}
        if not ok:
            issues = severe if severe else ["review failed"]
            cur_fb = state.get("validation_feedback")
            synthetic: AgentState = dict(state)
            if not isinstance(cur_fb, dict):
                synthetic["validation_feedback"] = empty_feedback()
            else:
                synthetic["validation_feedback"] = cur_fb
            allow_names: list[str] | None = None
            if isinstance(snap, dict):
                try:
                    art_rev = SchemaArtifact.model_validate(snap)
                    eff = state.get("sql_allowlist_tables")
                    if isinstance(eff, list) and eff:
                        allow_names = [str(x) for x in eff if str(x).strip()]
                    else:
                        allow_names = art_rev.allowlist_table_names()
                except Exception:
                    allow_names = None
            fix_msg = compose_sql_review_fix_message(
                user_q=user_q,
                sql=sql,
                review=out,
                severe_issues=issues,
                allowlist=allow_names,
                intent=str(state.get("intent") or ""),
            )
            synthetic["validation_feedback"] = append_feedback(synthetic, "sql_fix", fix_msg)
            summary = "; ".join(issues[:4])
            if hint_preview and hint_preview not in summary:
                summary = f"{summary}; hint: {hint_preview[:200]}"
            src: FeedbackSource = (
                "policy" if any(_POLICY_ISSUE_HINT.search(i) for i in issues) else "intent_review"
            )
            synthetic["validation_feedback"] = append_feedback(synthetic, src, summary)
            synthetic = {
                **state,
                "validation_feedback": append_failure_signature(
                    synthetic,
                    signature=_build_failure_signature(src, summary),
                ),
            }
            upd["validation_feedback"] = synthetic["validation_feedback"]
        return upd

    return sql_review


def make_validate_sql_node(deps: GraphDeps):
    def validate_sql(state: AgentState) -> dict:
        logger.info("node=validate_sql action=start")
        raw = state.get("generated_sql")
        allowlist, table_cols = _deterministic_validation_context(state, deps)
        ok, detail, sanitized, notes = validate_sql_deterministic(
            raw,
            deps.settings,
            allowlist_tables=allowlist,
            table_columns=table_cols,
        )
        metric_id = state.get("ledger_metric_id")
        if isinstance(state.get("schema_plan"), dict) and not metric_id:
            metric_id = state["schema_plan"].get("metric_id")
        user_q = _last_user_message(state)
        check_sql = sanitized if sanitized and ok else (raw or "")
        pol_ok, pol_detail = check_ledger_metric_policy(
            check_sql,
            metric_id=str(metric_id) if metric_id else None,
            user_q=user_q,
            enabled=bool(deps.settings.sql_validate_ledger_metric),
        )
        if ok and not pol_ok:
            ok = False
            detail = pol_detail
        if state.get("intent") == "system_data_query":
            scope_ok, scope_detail = check_sql_against_scope(
                sanitized if sanitized and ok else (raw or ""),
                state.get("business_scope") if isinstance(state.get("business_scope"), dict) else None,
            )
            if ok and not scope_ok:
                ok = False
                detail = scope_detail
        notes_joined = "; ".join(notes) if notes else "(none)"
        final_sql = (sanitized if sanitized and ok else (raw or "")) or ""
        emit_agent_trace(
            logger,
            deps.settings,
            agent="validate_sql",
            phase="Kiểm tra tĩnh (policy + allowlist)",
            detail=(
                f"sql_valid={ok}\n"
                f"detail={detail or '(none)'}\n"
                f"notes={notes_joined}\n"
                f"SQL:\n{safe_log_sql(final_sql, settings=deps.settings)}"
            ),
        )
        upd: dict = {"sql_valid": ok}
        synthetic: AgentState = dict(state)
        if sanitized and ok:
            upd["generated_sql"] = sanitized
        cur_fb = synthetic.get("validation_feedback")
        if not isinstance(cur_fb, dict):
            synthetic["validation_feedback"] = empty_feedback()
        for note in notes:
            synthetic["validation_feedback"] = append_feedback(synthetic, "policy", note)
        if not ok:
            msg = detail or "invalid sql"
            dlow = (detail or "").lower()
            if allowlist is not None and detail:
                if "table not in allowlist" in dlow:
                    msg = (
                        f"{msg}. Rewrite using ONLY these tables: {', '.join(sorted(allowlist))}. "
                        "Do not reference any other table name."
                    )
                elif "column not in allowlist" in dlow:
                    msg = (
                        f"{msg}. Fix column names per schema (qualified table.column). "
                        "Do not invent columns; productunits uses id not unit_id."
                    )
            synthetic["validation_feedback"] = _append_sql_repair_feedback(
                synthetic,
                source="policy",
                detail=msg,
            )
        if notes or not ok:
            upd["validation_feedback"] = synthetic["validation_feedback"]
        return {**emit_progress(state, "validate_sql"), **upd}

    return validate_sql


def make_execute_sql_node(deps: GraphDeps):
    def execute_sql(state: AgentState) -> dict:
        logger.info("node=execute_sql action=start")
        sql = strip_trailing_semicolons(state.get("generated_sql") or "")
        emit_agent_trace(
            logger,
            deps.settings,
            agent="execute_sql",
            phase="Thực thi SQL — gửi tới executor",
            detail=f"SQL:\n{safe_log_sql(sql, settings=deps.settings)}",
        )
        tenant_id = state.get("tenant_id")
        cid = state.get("correlation_id")
        schema_ver = state.get("schema_version")
        bearer_token = state.get("spring_bearer_token")
        try:
            result = deps.harness.run_tool(
                tool_name="sql.execute_readonly",
                tool=lambda: deps.sql_executor.execute(
                    sql,
                    tenant_id=str(tenant_id) if tenant_id is not None else None,
                    correlation_id=str(cid) if cid is not None else None,
                    schema_version=str(schema_ver) if schema_ver is not None else None,
                    bearer_token=str(bearer_token) if bearer_token is not None else None,
                ),
                context=ToolCallContext(
                    tool_name="sql.execute_readonly",
                    correlation_id=str(cid) if cid is not None else None,
                    tenant_id=str(tenant_id) if tenant_id is not None else None,
                    thread_id=str(state.get("thread_id") or "") or None,
                ),
            )
            rows = result.get("rows") if isinstance(result, dict) else None
            nrows = len(rows) if isinstance(rows, list) else "?"
            meta = result.get("meta") if isinstance(result, dict) else {}
            mode = meta.get("mode", "?") if isinstance(meta, dict) else "?"
            emit_agent_trace(
                logger,
                deps.settings,
                agent="execute_sql",
                phase="Executor trả về",
                detail=(
                    f"row_count≈{nrows} mode={mode}\n"
                    f"{safe_log_query_result(result if isinstance(result, dict) else None)}"
                ),
            )
            return {**emit_progress(state, "execute_sql"), "query_result": result}
        except Exception as exc:  # noqa: BLE001 — surface as retry feedback
            logger.warning("execute_sql failed: %s", exc)
            emit_agent_trace(
                logger,
                deps.settings,
                agent="execute_sql",
                phase="Executor lỗi",
                detail=str(exc),
            )
            return {
                **emit_progress(state, "execute_sql"),
                "query_result": None,
                "validation_feedback": _append_sql_repair_feedback(
                    state,
                    source="exec",
                    detail=str(exc),
                ),
            }

    return execute_sql


def make_validate_result_node(deps: GraphDeps):
    def validate_result(state: AgentState) -> dict:
        logger.info("node=validate_result action=start")
        qr = state.get("query_result")
        scope = state.get("business_scope") if isinstance(state.get("business_scope"), dict) else None
        user_q_raw = _last_user_message(state)
        user_q_effective = scope_effective_question(user_q_raw, scope)
        if qr is None:
            return {
                **emit_progress(state, "validate_result"),
                "result_ok": False,
                "validation_feedback": _append_sql_repair_feedback(
                    state,
                    source="result",
                    detail="empty or failed execution",
                ),
            }
        rows = qr.get("rows") if isinstance(qr, dict) else None
        previous_data_answer = state.get("last_data_answer") if isinstance(state.get("last_data_answer"), dict) else None
        reconcile_ok, reconcile_detail, reconcile_meta = reconcile_detail_rows_with_previous_total(
            scope=scope,
            previous_data_answer=previous_data_answer,
            query_result=qr if isinstance(qr, dict) else None,
        )
        clarification_ctx = (
            state.get("clarification_applied_context")
            if isinstance(state.get("clarification_applied_context"), dict)
            else None
        )
        clarify_kind = str(clarification_ctx.get("clarify_kind") or "") if isinstance(clarification_ctx, dict) else ""
        if clarify_kind == "data_followup_detail" and not bool(reconcile_meta.get("required")):
            return {
                **emit_progress(state, "validate_result"),
                "result_ok": False,
                "validation_feedback": _append_sql_repair_feedback(
                    state,
                    source="result",
                    detail=(
                        "clarification follow-up detail query must reconcile with previous scalar total; "
                        "missing reconcile context."
                    ),
                ),
            }
        merged_scope = merge_scope_reconcile_meta(scope, reconcile_meta)
        if not reconcile_ok:
            detail = (
                f"{reconcile_detail} Keep previous scope filters consistent, and rewrite detail rows so "
                "their sum matches the prior scalar total."
            )
            return {
                **emit_progress(state, "validate_result"),
                "result_ok": False,
                "business_scope": merged_scope,
                "validation_feedback": _append_sql_repair_feedback(
                    state,
                    source="result",
                    detail=detail,
                ),
            }
        if isinstance(qr, dict) and rows == []:
            ctx = build_last_data_answer_context(
                intent=str(state.get("intent") or "") or None,
                user_question=user_q_raw,
                effective_question=user_q_effective,
                business_scope=merged_scope,
                query_result=qr,
                generated_sql=str(state.get("generated_sql") or ""),
                reconcile_meta=reconcile_meta,
            )
            out: dict[str, Any] = {
                **emit_progress(state, "validate_result"),
                "result_ok": True,
                "result_empty": True,
                "business_scope": merged_scope,
                "empty_warning": state.get("empty_warning") or "",
            }
            if isinstance(ctx, dict):
                out["last_data_answer"] = ctx
            return out
        if rows is not None and len(rows) > MAX_RESULT_ROWS:
            return {
                **emit_progress(state, "validate_result"),
                "result_ok": False,
                "validation_feedback": _append_sql_repair_feedback(
                    state,
                    source="result",
                    detail="too many rows",
                ),
            }
        ctx = build_last_data_answer_context(
            intent=str(state.get("intent") or "") or None,
            user_question=user_q_raw,
            effective_question=user_q_effective,
            business_scope=merged_scope,
            query_result=qr if isinstance(qr, dict) else None,
            generated_sql=str(state.get("generated_sql") or ""),
            reconcile_meta=reconcile_meta,
        )
        out = {
            **emit_progress(state, "validate_result"),
            "result_ok": True,
            "result_empty": False,
            "business_scope": merged_scope,
        }
        if isinstance(ctx, dict):
            out["last_data_answer"] = ctx
        return out

    return validate_result


def make_fail_max_attempts_node(deps: GraphDeps):
    def fail_max_attempts(state: AgentState) -> dict:
        from langchain_core.messages import AIMessage

        from app.graph.sql_clarify import build_sql_failure_clarify

        logger.info("node=fail_max_attempts action=start")
        existing = state.get("error_payload")
        if existing and existing.get("error") == "schema_load_failed":
            return {}
        n = int(state.get("sql_attempt_count") or 0)
        if chart_degrade_eligible(state):
            emit_agent_trace(
                logger,
                deps.settings,
                agent="fail_max_attempts",
                phase="Chart degrade (giữ query_result)",
                detail=f"attempts={n}",
            )
            return chart_degrade_state_patch(
                state,
                reason="Hết lượt thử SQL — vẽ biểu đồ từ kết quả truy vấn cuối.",
            )
        out: dict = {
            "error_payload": {
                "error": "max_sql_attempts",
                "attempts": n,
                "validation_feedback": state.get("validation_feedback"),
            },
            "query_result": None,
        }
        if state.get("intent") == "system_data_chart":
            out["chart_data_ok"] = False
        clarify_pack = build_sql_failure_clarify(state)
        if clarify_pack:
            intro = str(clarify_pack.get("intro") or "")
            out["domain_clarify_sse"] = clarify_pack["sse"]
            out["final_answer"] = intro
            out["messages"] = [AIMessage(content=intro)]
            emit_agent_trace(
                logger,
                deps.settings,
                agent="fail_max_attempts",
                phase="SQL clarify (hỏi lại user)",
                detail=intro[:500],
            )
        return out

    return fail_max_attempts


def _build_entity_context_section(state: AgentState) -> str:
    ec = state.get("entity_context")
    if not ec:
        return ""
    lines = ["### Entity Name References (from database)"]
    for table, data in ec.items():
        if not isinstance(data, dict):
            continue
        names = data.get("exact_matches") or data.get("loaded_names", [])[:10]
        if names:
            lines.append(f"- {table}: {', '.join(names)}")
    return "\n".join(lines) if len(lines) > 1 else ""


def make_entity_resolution_node(deps: GraphDeps):
    """Return a node function that resolves entity names before gen_sql."""
    def entity_resolution_node(state: AgentState) -> dict[str, Any]:
        question = latest_human_question(state)
        if not question:
            return {}
        tenant_id = str(state.get("tenant_id") or "")
        if not tenant_id:
            return {}
        try:
            import asyncio
            from app.graph.entity_resolution import resolve_entities_for_domain

            domain = detect_sql_query_domain(question)
            if domain == "generic":
                return {}
            bearer_token = state.get("spring_bearer_token")
            entity_context = asyncio.get_event_loop().run_until_complete(
                resolve_entities_for_domain(
                    deps, tenant_id, question, domain,
                    bearer_token=bearer_token,
                )
            )
            return {"entity_context": entity_context}
        except Exception as exc:
            logger.warning("entity resolution node failed: %s", exc)
            return {}
    return entity_resolution_node


def route_after_gen_sql(state: AgentState) -> str:
    err = state.get("error_payload")
    if err and err.get("error") in ("schema_load_failed", "schema_catalog_failed"):
        return "fail_max_attempts"
    return "sql_review"


def _route_sql_retry(state: AgentState, kind: str) -> str:
    decision = decide_sql_retry(state, kind=kind)  # type: ignore[arg-type]
    if decision.action == RetryAction.REGEN_SQL:
        return "gen_sql"
    if decision.action == RetryAction.CHART_DEGRADE:
        if state.get("intent") == "system_data_chart":
            return "chart_readiness"
        return "done"
    return "fail_max_attempts"


def route_after_sql_review(state: AgentState) -> str:
    if state.get("sql_review_ok"):
        return "validate_sql"
    return _route_sql_retry(state, "intent_review")


def route_after_validate_sql(state: AgentState) -> str:
    if state.get("sql_valid"):
        return "execute_sql"
    return _route_sql_retry(state, "policy")


def _effective_ledger_first_prompts(state: AgentState, settings: Any) -> bool:
    if not settings.sql_ledger_first_prompts:
        return False
    if state.get("intent") == "system_data_chart":
        req = state.get("idea_data_request")
        if not isinstance(req, dict) or not req:
            brief = state.get("chart_brief")
            if isinstance(brief, dict):
                req = brief.get("data_request")
        if not isinstance(req, dict):
            return False
        blob = json.dumps(req, ensure_ascii=False).lower()
        keys = (
            "financeledger",
            "ledger",
            "doanh thu",
            "chi phí",
            "chi phi",
            "revenue",
            "expense",
            "cashflow",
            "sổ cái",
            "so cai",
            "salesrevenue",
        )
        return any(k in blob for k in keys)
    user_q = scope_effective_question(
        latest_human_question(state.get("messages")) or "",
        state.get("business_scope") if isinstance(state.get("business_scope"), dict) else None,
    )
    if not should_use_ledger_first_prompts(detect_sql_query_domain(user_q)):
        return False
    return detect_sql_query_domain(user_q) == "ledger"


def route_after_validate_result(state: AgentState) -> str:
    from app.graph.nodes.chart_readiness import route_after_sql_subgraph_for_chart

    chart_next = route_after_sql_subgraph_for_chart(state)
    if chart_next == "chart_readiness":
        return "chart_readiness"
    result_ok = state.get("result_ok")
    if result_ok is True:
        return "done"
    if result_ok is False:
        return _route_sql_retry(state, "result")
    # Belt-and-suspenders: if executor returned rows but result_ok was not set (stale merge), still finish.
    qr = state.get("query_result")
    if isinstance(qr, dict):
        rows = qr.get("rows")
        if isinstance(rows, list) and len(rows) > 0:
            return "done"
        meta = qr.get("meta") if isinstance(qr.get("meta"), dict) else {}
        rc = meta.get("row_count")
        if isinstance(rc, int) and rc > 0:
            return "done"
    return _route_sql_retry(state, "result")
