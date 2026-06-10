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
