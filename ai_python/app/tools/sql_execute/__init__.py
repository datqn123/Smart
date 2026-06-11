from __future__ import annotations
import json
import logging
from pydantic import BaseModel
from app.config.llm_client import StructuredOutputError
from app.graph.state import ToolState
from app.harness.think_log import think
from app.sql.guard import assert_read_only, SqlGuardError
from app.tools import memory_block

log = logging.getLogger(__name__)


class SqlDraft(BaseModel):
    """Cau SQL SELECT read-only tra loi raw_require."""
    sql: str


class SemanticCheck(BaseModel):
    """Ket qua tu kiem tra ngu nghia JOIN cua SQL vua sinh.
    ok=false thi sql = ban viet lai."""
    ok: bool
    sql: str | None = None
    reason: str | None = None


_PROMPT = ("{skill}\n\n--- YEU CAU ---\nraw_require: {raw_require}\n"
           "upstream_data: {upstream}\n{memory}")

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
    "3. Neu cau hoi khong thuoc loai do, hoac SQL da dung ngu nghia, tra ok=true.\n\n"
    "raw_require: {raw_require}\nsql: {sql}")


def _semantic_check(*, llm, skill: str, raw_require: str, sql: str) -> str:
    """Self-check 1 lan sau khi sinh SQL: bat lop loi 'absence semantics'
    (INNER JOIN nuot mat dong 0-su-kien) ma guard/validator khong the thay
    — validator chi nhin rows tra ve, khong biet dong nao bi join loai.
    Fail-open: check loi thi giu SQL goc."""
    think("sql_execute", "tu kiem tra lai SQL vua sinh: cau hoi co ngu nghia "
          "vang mat (chua/khong co/e) ma minh lo dung INNER JOIN khong?")
    user = _CHECK_PROMPT.format(raw_require=raw_require, sql=sql)
    try:
        verdict = llm.complete_structured(system=skill, user=user,
                                          output_model=SemanticCheck)
        if verdict.ok is False and (verdict.sql or "").strip():
            fixed = verdict.sql.strip()
            log.info("sql_execute semantic check REWROTE sql reason=%.150s\n  cu : %.200s\n  moi: %.200s",
                     verdict.reason, sql, fixed)
            think("sql_execute", "-> phat hien SQL sai ngu nghia: %s. Viet lai: %.200s",
                  verdict.reason, fixed)
            return fixed
        log.debug("sql_execute semantic check ok")
        think("sql_execute", "-> SQL on, khong can sua")
    except Exception as exc:
        log.warning("sql_execute semantic check fail-open: %s", exc)
        think("sql_execute", "-> buoc tu kiem tra gap loi (%s), giu SQL goc va di tiep", exc)
    return sql


def execute(state: ToolState, *, llm, executor, row_limit: int = 100, **_) -> dict:
    retry_err = (state["upstream_data"] or {}).get("error")
    if retry_err:
        think("sql_execute", 'lan truoc chay loi "%.150s" — doc lai schema de viet lai SQL '
              'cho "%.100s"', retry_err, state["raw_require"])
    else:
        think("sql_execute", 'bat dau dich yeu cau "%.100s" sang SQL, tra cuu schema',
              state["raw_require"])
    user = _PROMPT.format(skill=state["skill"], raw_require=state["raw_require"],
                          upstream=json.dumps(state["upstream_data"], ensure_ascii=False),
                          memory=memory_block(state))
    try:
        draft = llm.complete_structured(system=state["skill"], user=user,
                                        output_model=SqlDraft)
        sql = draft.sql
    except StructuredOutputError as exc:
        log.warning("sql_execute structured draft failed: %s", exc)
        think("sql_execute", "-> LLM tra output khong doc duoc, bao loi de SM quyet dinh thu lai")
        return {"sql": "", "columns": [], "rows": [],
                "error": f"LLM output khong hop le: {exc}"}
    think("sql_execute", "SQL nhap: %.250s", sql)
    sql = _semantic_check(llm=llm, skill=state["skill"],
                          raw_require=state["raw_require"], sql=sql)
    log.info("sql_execute SQL: %.300s", sql)
    try:
        assert_read_only(sql)                                  # guard TRUOC khi cham executor
        result = executor.run(sql, row_limit=row_limit)
        log.info("sql_execute rows=%d columns=%s", len(result["rows"]), result["columns"])
        think("sql_execute", "-> chay xong: %d dong, cot %s",
              len(result["rows"]), result["columns"])
        return {"sql": sql, "columns": result["columns"],
                "rows": result["rows"], "error": None}
    except SqlGuardError as exc:
        log.warning("sql_execute guard blocked: %s sql=%.200s", exc, sql)
        think("sql_execute", "-> guard chan SQL khong phai SELECT: %s", exc)
        return {"sql": sql, "columns": [], "rows": [], "error": f"SQL guard: {exc}"}
    except Exception as exc:
        log.error("sql_execute DB error: %s sql=%.200s", exc, sql)
        think("sql_execute", "-> DB bao loi: %.150s — tra loi ve cho SM xu ly", exc)
        return {"sql": sql, "columns": [], "rows": [], "error": f"DB error: {exc}"}


def self_validate(state: ToolState):
    out = state.get("output") or {}
    if out.get("error"):
        return False, out["error"]
    if not isinstance(out.get("rows"), list):
        return False, "thieu rows trong output"
    return True, None
