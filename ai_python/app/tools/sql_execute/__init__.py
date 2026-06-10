from __future__ import annotations
import json
from app.graph.state import ToolState
from app.sql.guard import assert_read_only, SqlGuardError

_PROMPT = ("{skill}\n\n--- YEU CAU ---\nraw_require: {raw_require}\n"
           "upstream_data: {upstream}\n\nTra ve JSON {{\"sql\": \"...\"}}.")


def _parse_sql(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        raw = raw[raw.find("{"):]
    return json.loads(raw)["sql"]


def execute(state: ToolState, *, llm, executor, row_limit: int = 100, **_) -> dict:
    user = _PROMPT.format(skill=state["skill"], raw_require=state["raw_require"],
                          upstream=json.dumps(state["upstream_data"], ensure_ascii=False))
    sql = _parse_sql(llm.complete(system=state["skill"], user=user, role="default"))
    try:
        assert_read_only(sql)                                  # guard TRUOC khi cham executor
        result = executor.run(sql, row_limit=row_limit)
        return {"sql": sql, "columns": result["columns"],
                "rows": result["rows"], "error": None}
    except SqlGuardError as exc:
        return {"sql": sql, "columns": [], "rows": [], "error": f"SQL guard: {exc}"}
    except Exception as exc:                                    # loi DB -> loi tool (SM retry)
        return {"sql": sql, "columns": [], "rows": [], "error": f"DB error: {exc}"}


def self_validate(state: ToolState):
    out = state.get("output") or {}
    if out.get("error"):
        return False, out["error"]
    if not isinstance(out.get("rows"), list):
        return False, "thieu rows trong output"
    return True, None
