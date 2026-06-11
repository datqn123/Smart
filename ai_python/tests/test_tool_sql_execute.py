import json
from app.tools.sql_execute import execute, self_validate
from app.graph.state import new_tool_state


class _LLM:
    def __init__(self, sql): self._sql = sql; self.seen = []
    def complete(self, *, system, user, role="default", temperature=None):
        self.seen.append({"system": system, "user": user})
        return json.dumps({"sql": self._sql})


def test_execute_generates_sql_and_runs_on_executor(stub_sql):  # fact-sql-execute
    llm = _LLM("SELECT id, name FROM customers LIMIT 5")
    st = new_tool_state(tool_name="sql_execute", raw_require="liet ke khach hang")
    st["skill"] = "SKILL"
    out = execute(st, llm=llm, executor=stub_sql, row_limit=100)
    assert out["sql"].lower().startswith("select")
    assert out["rows"][0] == {"id": 1, "name": "Acme"}
    assert "SKILL" in llm.seen[0]["system"] or "SKILL" in llm.seen[0]["user"]


def test_execute_non_select_is_blocked(stub_sql):  # fact-sql-guard
    llm = _LLM("DELETE FROM customers")
    st = new_tool_state(tool_name="sql_execute", raw_require="xoa het")
    out = execute(st, llm=llm, executor=stub_sql, row_limit=100)
    assert out["error"] is not None
    assert out["rows"] == []
    assert stub_sql.executed == []   # khong thuc thi


def test_self_validate_passes_on_rows():
    st = new_tool_state(tool_name="sql_execute", raw_require="x")
    st["output"] = {"sql": "SELECT 1", "rows": [{"a": 1}], "columns": ["a"], "error": None}
    ok, err = self_validate(st)
    assert ok is True and err is None


def test_self_validate_fails_when_error_present():
    st = new_tool_state(tool_name="sql_execute", raw_require="x")
    st["output"] = {"sql": "", "rows": [], "columns": [], "error": "guard blocked"}
    ok, err = self_validate(st)
    assert ok is False and "guard" in err


class _BadJsonLLM:
    def complete(self, *, system, user, role="default", temperature=None):
        return "Xin loi, toi khong the giup."  # khong phai JSON


def test_execute_handles_malformed_llm_json(stub_sql):  # resilience
    # LLM tra output khong phai JSON -> execute KHONG raise, tra error,
    # khong cham executor; self_validate fail -> SM retry.
    st = new_tool_state(tool_name="sql_execute", raw_require="x")
    st["skill"] = "S"
    out = execute(st, llm=_BadJsonLLM(), executor=stub_sql, row_limit=100)
    assert out["error"] is not None
    assert out["rows"] == []
    assert stub_sql.executed == []
    st["output"] = out
    ok, _ = self_validate(st)
    assert ok is False


def test_prompt_has_memory_block_when_summary(stub_sql):
    llm = _LLM("SELECT 1")
    st = new_tool_state(tool_name="sql_execute", raw_require="con thang truoc?",
                        memory_summary="User dang xem doanh thu thang 5/2026")
    st["skill"] = "SKILL"
    execute(st, llm=llm, executor=stub_sql)
    assert "[Boi canh hoi thoai truoc]: User dang xem doanh thu thang 5/2026" in llm.seen[0]["user"]


def test_prompt_no_memory_block_when_none(stub_sql):
    llm = _LLM("SELECT 1")
    st = new_tool_state(tool_name="sql_execute", raw_require="x")
    st["skill"] = "SKILL"
    execute(st, llm=llm, executor=stub_sql)
    assert "[Boi canh hoi thoai truoc]" not in llm.seen[0]["user"]
