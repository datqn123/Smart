"""SQL subgraph nodes."""

from __future__ import annotations

import logging
import re

from langchain_core.messages import HumanMessage

from app.graph.dbmeta import SchemaArtifact
from app.graph.deps import GraphDeps
from app.graph.feedback import (
    FeedbackSource,
    append_feedback,
    bump_attempts,
    empty_feedback,
    render_for_prompt,
)
from app.graph.retry import can_regen_sql
from app.graph.state import AgentState
from app.graph.validate_sql import validate_sql_deterministic
from app.llm.schemas import SqlReviewOutput

logger = logging.getLogger(__name__)

MAX_RESULT_ROWS = 50_000

_POLICY_ISSUE_HINT = re.compile(
    r"\b(limit|select|ddl|dml|insert|update|delete|drop)\b",
    re.IGNORECASE,
)


def _last_user_message(state: AgentState) -> str:
    for m in reversed(state.get("messages") or []):
        c = getattr(m, "content", "")
        if c:
            return str(c)
    return ""


def _format_schema_lines(artifact: SchemaArtifact) -> str:
    lines: list[str] = []
    for t in artifact.tables:
        col_names = ", ".join(c.name for c in t.columns)
        lines.append(f"- {t.name}({col_names})")
    return "\n".join(lines)


def make_gen_sql_node(deps: GraphDeps):
    """TASK-LG-09: increment sql_attempt_count at start of each gen_sql."""

    def gen_sql(state: AgentState) -> dict:
        logger.info("node=gen_sql action=start")
        prev = int(state.get("sql_attempt_count") or 0)
        nxt = prev + 1
        bumped = bump_attempts(state)
        prev_fb = state.get("validation_feedback")
        if not isinstance(prev_fb, dict):
            fb_render = render_for_prompt(empty_feedback())
        else:
            fb_render = render_for_prompt(prev_fb)
        reg = deps.llm_registry
        ver = state.get("schema_version")
        artifact: SchemaArtifact | None = None
        if deps.schema_loader and ver:
            try:
                artifact = deps.schema_loader.load(ver)
            except Exception as exc:
                logger.warning("schema_loader.load failed in gen_sql: %s", exc)
                fb = append_feedback(state, "policy", f"schema load failed: {exc}")
                return {
                    "sql_attempt_count": prev,
                    "generated_sql": None,
                    "error_payload": {
                        "error": "schema_load_failed",
                        "schema_version": ver,
                        "detail": str(exc),
                    },
                    "validation_feedback": fb,
                }
        schema_block = (
            _format_schema_lines(artifact) if artifact else "(minimal mode — no schema_version or loader)"
        )
        user_q = _last_user_message(state)
        prompt = (
            f"Schema (allowlist tables):\n{schema_block}\n\n"
            f"Prior feedback (only buckets with content):\n{fb_render}\n\n"
            f"User question: {user_q}\n\n"
            "Respond with EXACTLY ONE SELECT statement. Include a LIMIT clause."
        )
        if reg is None:
            sql = f"SELECT 1 AS ok LIMIT {deps.settings.sql_limit_max}"
            return {
                "sql_attempt_count": nxt,
                "generated_sql": sql,
                "validation_feedback": bumped,
            }
        client = reg.get("sql_gen")
        sql = client.invoke_text(prompt, system="SQL only. SELECT-only.")
        return {"sql_attempt_count": nxt, "generated_sql": sql.strip(), "validation_feedback": bumped}

    return gen_sql


def make_sql_review_node(deps: GraphDeps):
    def sql_review(state: AgentState) -> dict:
        logger.info("node=sql_review action=start")
        reg = deps.llm_registry
        sql = state.get("generated_sql") or ""
        if reg is None:
            return {"sql_review_ok": True}
        client = reg.get("sql_review")
        try:
            out = client.structured_predict([HumanMessage(content=sql)], SqlReviewOutput)
        except Exception:
            logger.warning("sql_review structured_predict failed; passing review", exc_info=True)
            return {"sql_review_ok": True}
        ok = bool(out.ok)
        upd: dict = {"sql_review_ok": ok}
        if not ok:
            issues = list(out.issues or [])
            if not issues:
                issues = ["review failed"]
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
        if deps.schema_loader and state.get("schema_version"):
            try:
                art = deps.schema_loader.load(state["schema_version"])  # type: ignore[arg-type]
                allowlist = art.allowlist_table_names()
                table_cols = art.allowlist_columns_map()
            except Exception:
                allowlist = None
                table_cols = None
        ok, detail, sanitized, notes = validate_sql_deterministic(
            raw,
            deps.settings,
            allowlist_tables=allowlist,
            table_columns=table_cols,
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
            synthetic["validation_feedback"] = append_feedback(
                synthetic,
                "policy",
                detail or "invalid sql",
            )
        if notes or not ok:
            upd["validation_feedback"] = synthetic["validation_feedback"]
        return upd

    return validate_sql


def make_execute_sql_node(deps: GraphDeps):
    def execute_sql(state: AgentState) -> dict:
        logger.info("node=execute_sql action=start")
        sql = state.get("generated_sql") or ""
        tenant_id = state.get("tenant_id")
        try:
            result = deps.sql_executor.execute(sql, tenant_id=tenant_id)
            return {"query_result": result}
        except Exception as exc:  # noqa: BLE001 — surface as retry feedback
            logger.warning("execute_sql failed: %s", exc)
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
        return {
            "error_payload": {
                "error": "max_sql_attempts",
                "attempts": n,
                "validation_feedback": state.get("validation_feedback"),
            },
            "query_result": None,
        }

    return fail_max_attempts


def route_after_gen_sql(state: AgentState) -> str:
    err = state.get("error_payload")
    if err and err.get("error") == "schema_load_failed":
        return "fail_max_attempts"
    return "sql_review"


def route_after_sql_review(state: AgentState) -> str:
    if state.get("sql_review_ok"):
        return "validate_sql"
    if can_regen_sql(state):
        return "gen_sql"
    return "fail_max_attempts"


def route_after_validate_sql(state: AgentState) -> str:
    if state.get("sql_valid"):
        return "execute_sql"
    if can_regen_sql(state):
        return "gen_sql"
    return "fail_max_attempts"


def route_after_validate_result(state: AgentState) -> str:
    if state.get("result_ok"):
        return "done"
    if can_regen_sql(state):
        return "gen_sql"
    return "fail_max_attempts"
