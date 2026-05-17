"""SQL subgraph nodes."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.graph.agent_trace import emit_agent_trace
from app.graph.dbmeta import SchemaArtifact
from app.graph.deps import GraphDeps
from app.graph.feedback import (
    FeedbackSource,
    append_feedback,
    bump_attempts,
    empty_feedback,
    render_for_prompt,
)
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
from app.graph.logging_policy import safe_log_sql
from app.graph.chart_calendar import resolve_month_calendar
from app.graph.enum_literals import enum_literals_prompt_block
from app.prompts.load import load_agent_json_contract, load_agent_prompt
from app.graph.chart_schema_merge import (
    allowed_tables_prompt_line,
    infer_tables_from_chart_context,
    merge_tables_into_artifact,
)
from app.graph.sql_prompts import build_gen_sql_user_prompt, format_schema_block
from app.graph.sql_similarity import max_pool_similarity
from app.graph.sql_table_selection import select_tables_for_question
from app.graph.validate_sql import (
    check_ledger_metric_policy,
    is_llm_select_sql_shape,
    normalize_llm_sql_output,
    strip_trailing_semicolons,
    validate_sql_deterministic,
)
from app.llm.schemas import SqlReviewOutput

logger = logging.getLogger(__name__)

MAX_RESULT_ROWS = 50_000

_POLICY_ISSUE_HINT = re.compile(
    r"\b(limit|select|ddl|dml|insert|update|delete|drop)\b",
    re.IGNORECASE,
)
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


def _load_schema_artifact(
    deps: GraphDeps, _state: AgentState, *, user_q: str
) -> tuple[SchemaArtifact | None, Exception | None]:
    """Build schema from Postgres: ai_table_description registry + live catalog (no YAML)."""
    from app.graph.pg_schema_context import build_schema_artifact_from_postgres

    art, err = build_schema_artifact_from_postgres(deps.settings, user_q)
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
            fb_render = render_for_prompt(empty_feedback(), latest_only=True)
        else:
            fb_render = render_for_prompt(prev_fb, latest_only=True)
        mode: str = "explore" if nxt == 1 else ("exploit" if deps.settings.sql_exploit_on_retry else "explore")
        reg = deps.llm_registry
        ver = state.get("schema_version")
        user_q = _last_user_message(state)
        pre_err = state.get("error_payload")
        if isinstance(pre_err, dict) and pre_err.get("error") in (
            "schema_load_failed",
            "schema_catalog_failed",
        ):
            if not state.get("runtime_schema_artifact"):
                return {
                    "sql_attempt_count": prev,
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
                "sql_attempt_count": prev,
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
        extra_tables = infer_tables_from_chart_context(user_q, idea_req if isinstance(idea_req, dict) else None)
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
                user_q=user_q,
                artifact=artifact,
                max_tables=int(deps.settings.sql_max_selected_tables),
                use_llm=bool(deps.settings.sql_table_pick_use_llm),
                min_tables_for_llm=int(deps.settings.sql_table_pick_min_tables_for_llm),
            )
        enriched = (
            bool(deps.settings.sql_enriched_schema_prompt)
            or bool(schema_plan)
            or bool(deps.settings.sql_schema_explorer_enabled)
        )
        ledger_first = _effective_ledger_first_prompts(state, deps.settings)
        multi_table_plan = bool(selected_tables and len(selected_tables) > 1)
        schema_block = format_schema_block(
            artifact,
            selected_tables=selected_tables,
            enriched=enriched,
        )
        dialog_tail = format_dialog_tail_for_sql(
            state.get("messages"),
            max_messages=int(deps.settings.sql_dialog_tail_max_messages),
            max_chars=int(deps.settings.sql_dialog_tail_max_chars),
        )
        planner_json: str | None = None
        if isinstance(idea_req, dict) and idea_req:
            try:
                planner_json = json.dumps(idea_req, ensure_ascii=False)[:8000]
            except Exception:
                planner_json = None
        chart_ctx = (state.get("chart_thread_context") or "").strip() or None
        month_cal = resolve_month_calendar(
            user_q,
            idea_req if isinstance(idea_req, dict) else None,
        )
        allow_line = allowed_tables_prompt_line(artifact)
        domain_block = format_domain_context_block(
            state.get("domain_context") if isinstance(state.get("domain_context"), dict) else None
        )
        prompt = build_gen_sql_user_prompt(
            mode=mode,  # type: ignore[arg-type]
            schema_block=schema_block,
            feedback_render=fb_render,
            user_q=user_q,
            seed_sql=seed_sql if mode == "exploit" else None,
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
                "sql_attempt_count": nxt,
                "generated_sql": sql,
                "validation_feedback": bumped,
                "sql_gen_mode": mode,
                "runtime_schema_artifact": artifact_dump,
            }
            if selected_tables is not None:
                out_none["selected_tables"] = selected_tables
            return out_none
        allow_names = artifact.allowlist_table_names()
        _gen_sql_system = _build_gen_sql_system(
            allow_names,
            ledger_first=ledger_first,
            month_calendar=month_cal is not None,
        )
        client = reg.get("sql_gen")
        sql = client.invoke_text(prompt, system=_gen_sql_system)
        sql_stripped = normalize_llm_sql_output(sql)
        fb_for_append = bumped
        pool = list(state.get("sql_local_pool") or [])
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
                f"câu_hỏi:\n{user_q[:800]}{'…' if len(user_q) > 800 else ''}\n"
                f"SQL:\n{safe_log_sql(sql_stripped, settings=deps.settings)}"
            ),
        )
        out: dict = {
            "sql_attempt_count": nxt,
            "generated_sql": sql_stripped,
            "validation_feedback": fb_for_append,
            "sql_gen_mode": mode,
            "sql_local_pool": pool,
            "sql_attempt_history": hist[-32:],
            "runtime_schema_artifact": artifact_dump,
        }
        if selected_tables is not None:
            out["selected_tables"] = selected_tables
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
            return {"sql_review_ok": True}
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
                "sql_review_ok": False,
                "validation_feedback": append_feedback(state, "policy", msg),
            }
        client = reg.get("sql_review")
        review_body = (
            "Review this SELECT-only SQL for safety and relevance. "
            "Use the JSON contract only in your reply.\n\n"
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
                max_retries=5,
            )
        except Exception:
            logger.warning("sql_review structured_predict failed; passing review", exc_info=True)
            return {"sql_review_ok": True}
        issues_raw = list(out.issues or [])
        severe = [
            i
            for i in issues_raw
            if not _benign_sql_review_issue(i) and not _spurious_structured_parse_echo(i)
        ]
        ok = len(severe) == 0
        issues_txt = "\n".join(f"- {i}" for i in issues_raw) if issues_raw else "(no issues)"
        if issues_raw and ok and any(_benign_sql_review_issue(i) for i in issues_raw):
            issues_txt += "\n(bỏ qua cảnh báo nhẹ: LIMIT + aggregate — hợp lệ với executor read-only)"
        emit_agent_trace(
            logger,
            deps.settings,
            agent="sql_review",
            phase="Đánh giá SQL (LLM)",
            detail=f"ok={ok}\n{issues_txt}",
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
            for issue in issues:
                src: FeedbackSource = (
                    "policy" if _POLICY_ISSUE_HINT.search(issue) else "intent_review"
                )
                synthetic["validation_feedback"] = append_feedback(synthetic, src, issue)
            upd["validation_feedback"] = synthetic["validation_feedback"]
        return upd

    return sql_review


def make_validate_sql_node(deps: GraphDeps):
    def validate_sql(state: AgentState) -> dict:
        logger.info("node=validate_sql action=start")
        raw = state.get("generated_sql")
        allowlist = None
        table_cols = None
        art: SchemaArtifact | None = None
        snap = state.get("runtime_schema_artifact")
        if isinstance(snap, dict):
            try:
                art = SchemaArtifact.model_validate(snap)
            except Exception:
                art = None
        if art is not None:
            try:
                allowlist = art.allowlist_table_names()
                table_cols = art.allowlist_columns_map()
                sel = state.get("selected_tables")
                if deps.settings.sql_table_selection_enabled and isinstance(sel, list) and sel:
                    picked = {str(x).strip().lower() for x in sel if str(x).strip()}
                    narrowed = picked & allowlist
                    if narrowed:
                        allowlist = narrowed
                        table_cols = {t: cols for t, cols in table_cols.items() if t in allowlist}
            except Exception:
                allowlist = None
                table_cols = None
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
            if allowlist is not None and detail and "allowlist" in detail.lower():
                msg = (
                    f"{msg}. Rewrite using ONLY these tables: {', '.join(sorted(allowlist))}. "
                    "Do not reference any other table name."
                )
            synthetic["validation_feedback"] = append_feedback(synthetic, "policy", msg)
        if notes or not ok:
            upd["validation_feedback"] = synthetic["validation_feedback"]
        return upd

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
        try:
            result = deps.sql_executor.execute(
                sql,
                tenant_id=str(tenant_id) if tenant_id is not None else None,
                correlation_id=str(cid) if cid is not None else None,
                schema_version=str(schema_ver) if schema_ver is not None else None,
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
                detail=f"row_count≈{nrows} mode={mode}",
            )
            return {"query_result": result}
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
                "query_result": None,
                "validation_feedback": append_feedback(state, "exec", str(exc)),
            }

    return execute_sql


def make_validate_result_node(deps: GraphDeps):
    def validate_result(state: AgentState) -> dict:
        logger.info("node=validate_result action=start")
        qr = state.get("query_result")
        if qr is None:
            return {
                "result_ok": False,
                "validation_feedback": append_feedback(
                    state,
                    "result",
                    "empty or failed execution",
                ),
            }
        rows = qr.get("rows") if isinstance(qr, dict) else None
        if isinstance(qr, dict) and rows == []:
            return {"result_ok": True, "result_empty": True}
        if rows is not None and len(rows) > MAX_RESULT_ROWS:
            return {
                "result_ok": False,
                "validation_feedback": append_feedback(
                    state,
                    "result",
                    "too many rows",
                ),
            }
        return {"result_ok": True, "result_empty": False}

    return validate_result


def make_fail_max_attempts_node(deps: GraphDeps):
    def fail_max_attempts(state: AgentState) -> dict:
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
        return out

    return fail_max_attempts


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
    if state.get("intent") != "system_data_chart":
        return True
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


def route_after_validate_result(state: AgentState) -> str:
    from app.graph.nodes.chart_readiness import route_after_sql_subgraph_for_chart

    chart_next = route_after_sql_subgraph_for_chart(state)
    if chart_next == "chart_readiness":
        return "chart_readiness"
    if state.get("result_ok"):
        return "done"
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
