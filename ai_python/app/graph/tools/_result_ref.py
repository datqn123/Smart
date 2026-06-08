"""Helpers for artifact tools that consume Harness-held result_ref handles."""

from __future__ import annotations

from typing import Any

from app.harness.tool_registry import TurnContext


def rows_from_args_or_ref(args: dict[str, Any], ctx: TurnContext) -> tuple[list[dict[str, Any]], str | None]:
    rows = [row for row in (args.get("rows") or []) if isinstance(row, dict)]
    if rows:
        return rows, None

    result_ref = str(args.get("result_ref") or "").strip()
    if result_ref:
        store = getattr(ctx, "result_store", None)
        if store is None or not hasattr(store, "get"):
            return [], "result_ref store is unavailable"
        record = store.get(result_ref, ctx=ctx)
        if record is None:
            return [], "result_ref is missing, expired, or outside tenant scope"
        data = record.data if isinstance(record.data, dict) else {}
        stored_rows = data.get("rows")
        if not isinstance(stored_rows, list):
            query_result = data.get("query_result")
            if isinstance(query_result, dict):
                stored_rows = query_result.get("rows")
        if not isinstance(stored_rows, list):
            return [], "result_ref does not contain tabular rows"
        return [row for row in stored_rows if isinstance(row, dict)], None

    # An explicit (possibly empty) `rows` key is a valid zero-row input; but if the
    # planner bound neither real rows nor a result_ref, surface it as a failure so
    # the turn replans instead of silently rendering an empty artifact (LOW-5).
    if "rows" in args:
        return [], None
    return [], "no input rows or result_ref provided"
