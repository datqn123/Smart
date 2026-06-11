from __future__ import annotations
import json
import logging
from app.graph.state import ToolState
from app.sql.guard import assert_read_only, SqlGuardError
from app.tools import memory_block

log = logging.getLogger(__name__)

_PROMPT = ("{skill}\n\n--- YEU CAU ---\nraw_require: {raw_require}\n"
           "upstream_data: {upstream}\n{memory}\nTra ve JSON {{\"sql\": \"...\"}}.")


def _parse_sql(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        raw = raw[raw.find("{"):]
    return json.loads(raw)["sql"]


def execute(state: ToolState, *, llm, executor, row_limit: int = 100, **_) -> dict:
    user = _PROMPT.format(skill=state["skill"], raw_require=state["raw_require"],
                          upstream=json.dumps(state["upstream_data"], ensure_ascii=False),
                          memory=memory_block(state))
    raw = llm.complete(system=state["skill"], user=user, role="default")
    log.debug("sql_execute LLM raw: %.300s", raw)
    try:
        sql = _parse_sql(raw)
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        log.warning("sql_execute LLM output malformed: %s raw_preview=%.200s", exc, raw[:200])
        return {"sql": "", "columns": [], "rows": [],
                "error": f"LLM output khong hop le: {exc}"}
    log.info("sql_execute SQL: %.300s", sql)
    try:
        assert_read_only(sql)                                  # guard TRUOC khi cham executor
        result = executor.run(sql, row_limit=row_limit)
        log.info("sql_execute rows=%d columns=%s", len(result["rows"]), result["columns"])
        return {"sql": sql, "columns": result["columns"],
                "rows": result["rows"], "error": None}
    except SqlGuardError as exc:
        log.warning("sql_execute guard blocked: %s sql=%.200s", exc, sql)
        return {"sql": sql, "columns": [], "rows": [], "error": f"SQL guard: {exc}"}
    except Exception as exc:
        log.error("sql_execute DB error: %s sql=%.200s", exc, sql)
        return {"sql": sql, "columns": [], "rows": [], "error": f"DB error: {exc}"}


def self_validate(state: ToolState):
    out = state.get("output") or {}
    if out.get("error"):
        return False, out["error"]
    if not isinstance(out.get("rows"), list):
        return False, "thieu rows trong output"
    return True, None
