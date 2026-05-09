from __future__ import annotations

import json
from typing import Any

from .catalog import allowlist_lower, catalog_snapshot
from .intent import intent_analyze
from .observability import redact_hitl_token, with_timing
from .rag_stub import rag_retrieve
from .sql_execute import sql_execute_read
from .sql_validate import (
    SqlValidationError,
    referenced_tables,
    transpile_to_sqlite,
    validate_select,
)
from .ui import ui_build_form_spec, ui_build_table_spec, viz_build_chart_spec

MIN_HITL_LEN = 16


def handle_read_catalog_snapshot() -> dict[str, Any]:
    return with_timing("read_catalog_snapshot", catalog_snapshot)


def handle_intent_analyze(user_text: str, session_id: str = "") -> dict[str, Any]:
    return with_timing("intent_analyze", lambda: intent_analyze(user_text, session_id))


def handle_rag_retrieve(query: str, top_k: int = 5) -> dict[str, Any]:
    return with_timing("rag_retrieve", lambda: rag_retrieve(query, top_k))


def handle_sql_propose_select(
    draft_sql: str,
    rag_table_hints: list[str] | None = None,
) -> dict[str, Any]:
    def _go() -> dict[str, Any]:
        allowed = allowlist_lower()
        try:
            tree = validate_select(draft_sql.strip(), allowed)
            refs = referenced_tables(tree)
            normalized = transpile_to_sqlite(draft_sql)
        except SqlValidationError as e:
            return {"ok": False, "error": {"code": e.code, "message": e.message}}
        warnings: list[str] = []
        if rag_table_hints:
            hints = {h.lower() for h in rag_table_hints}
            unused = hints - refs
            if unused:
                warnings.append(f"unused_rag_hints:{sorted(unused)}")
        return {
            "ok": True,
            "normalized_sql": normalized,
            "merged_tables": sorted(refs),
            "warnings": warnings,
        }

    return with_timing("sql_propose_select", _go)


def handle_sql_execute_read(sql: str) -> dict[str, Any]:
    return with_timing("sql_execute_read", lambda: sql_execute_read(sql))


def handle_ui_build_form_spec(
    title: str,
    fields: list[dict[str, Any]],
    defaults: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return with_timing(
        "ui_build_form_spec",
        lambda: ui_build_form_spec(title, fields, defaults),
    )


def handle_ui_build_table_spec(
    title: str,
    columns: list[str],
    rows: list[list[Any]],
) -> dict[str, Any]:
    return with_timing(
        "ui_build_table_spec",
        lambda: ui_build_table_spec(title, columns, rows),
    )


def handle_viz_build_chart_spec(
    chart_type: str,
    labels: list[str],
    series: dict[str, list[float]],
) -> dict[str, Any]:
    return with_timing(
        "viz_build_chart_spec",
        lambda: viz_build_chart_spec(chart_type, labels, series),
    )


def handle_write_commit(
    proposal_id: str,
    hitl_token: str,
    idempotency_key: str,
    payload_json: str,
) -> dict[str, Any]:
    def _go() -> dict[str, Any]:
        if not idempotency_key.strip():
            return {
                "ok": False,
                "error": {"code": "VALIDATION_FAILED", "message": "idempotency_key required"},
            }
        if len(hitl_token.strip()) < MIN_HITL_LEN:
            return {
                "ok": False,
                "error": {"code": "FORBIDDEN", "message": "hitl_token too short"},
            }
        try:
            json.loads(payload_json)
        except json.JSONDecodeError as e:
            return {
                "ok": False,
                "error": {"code": "VALIDATION_FAILED", "message": f"payload_json: {e}"},
            }
        _ = redact_hitl_token(hitl_token)
        return {
            "ok": True,
            "status": "accepted_stub",
            "proposal_id": proposal_id,
            "idempotency_key": idempotency_key,
            "note": "No ERP mutation in ai_python slice; integrate Spring in later task.",
        }

    return with_timing("write_commit", _go)
