from __future__ import annotations
import json
import logging
from app.graph.state import ToolState
from app.sql.guard import assert_read_only, SqlGuardError
from app.tools import memory_block

log = logging.getLogger(__name__)

_PROMPT = ("{skill}\n\n--- YEU CAU ---\nraw_require: {raw_require}\n"
           "upstream_data: {upstream}\n{memory}\nTra ve JSON {{\"sql\": \"...\"}}.")

_CHECK_PROMPT = (
    "Ban vua sinh cau SQL duoi day cho yeu cau cua user. Tu kiem tra NGU NGHIA JOIN "
    "truoc khi chay:\n"
    "1. Cau hoi co hoi ve doi tuong KHONG CO / CHUA TUNG CO du lieu su kien khong? "
    "(dau hieu: 'chua', 'khong co', 'chua tung', 'e', 'ban cham', 'it nhat', 'thap nhat', "
    "'chua duoc dung', 'khong ban duoc')\n"
    "2. Neu CO ma SQL dang INNER JOIN sang bang su kien (orderdetails, salesorders, "
    "stockreceipts...) thi cac dong 0-su-kien — chinh la doi tuong user hoi — bi loai mat. "
    "SQL SAI. Viet lai: FROM bang chu the, LEFT JOIN bang su kien, "
    "COALESCE(SUM(...), 0) / COUNT(x.id).\n"
    "3. Neu cau hoi khong thuoc loai do, hoac SQL da dung ngu nghia, tra ve ok.\n\n"
    "raw_require: {raw_require}\nsql: {sql}\n\n"
    "Tra ve DUY NHAT JSON mot dong:\n"
    '{{"ok": true}}\n'
    'hoac {{"ok": false, "sql": "<SQL viet lai>", "reason": "<ly do ngan>"}}'
)


def _coerce_json(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        raw = raw[raw.find("{"):]
    return json.loads(raw)


def _parse_sql(raw: str) -> str:
    return _coerce_json(raw)["sql"]


def _semantic_check(*, llm, skill: str, raw_require: str, sql: str) -> str:
    """Self-check 1 lan sau khi sinh SQL: bat lop loi 'absence semantics'
    (INNER JOIN nuot mat dong 0-su-kien) ma guard/validator khong the thay
    — validator chi nhin rows tra ve, khong biet dong nao bi join loai.
    Fail-open: check loi/khong parse duoc thi giu SQL goc."""
    user = _CHECK_PROMPT.format(raw_require=raw_require, sql=sql)
    try:
        raw = llm.complete(system=skill, user=user, role="default")
        verdict = _coerce_json(raw)
        if verdict.get("ok") is False and str(verdict.get("sql") or "").strip():
            fixed = verdict["sql"].strip()
            log.info("sql_execute semantic check REWROTE sql reason=%.150s\n  cu : %.200s\n  moi: %.200s",
                     verdict.get("reason"), sql, fixed)
            return fixed
        log.debug("sql_execute semantic check ok")
    except Exception as exc:
        log.warning("sql_execute semantic check fail-open: %s", exc)
    return sql


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
    sql = _semantic_check(llm=llm, skill=state["skill"],
                          raw_require=state["raw_require"], sql=sql)
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
