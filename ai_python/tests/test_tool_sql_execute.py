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


class _SeqLLM:
    """Tra lan luot tung response cho moi lan complete() — mo phong
    call 1 = sinh SQL, call 2 = semantic self-check."""
    def __init__(self, *responses):
        self._responses = list(responses); self.seen = []
    def complete(self, *, system, user, role="default", temperature=None):
        self.seen.append({"system": system, "user": user})
        return self._responses.pop(0)


_INNER = "SELECT p.name, SUM(od.quantity) AS tong_ban FROM products p JOIN orderdetails od ON od.product_id = p.id GROUP BY p.id, p.name ORDER BY tong_ban ASC LIMIT 10"
_LEFT = "SELECT p.name, COALESCE(SUM(od.quantity), 0) AS tong_ban FROM products p LEFT JOIN orderdetails od ON od.product_id = p.id GROUP BY p.id, p.name ORDER BY tong_ban ASC LIMIT 10"


def test_semantic_check_rewrites_absence_question_sql(stub_sql):
    # Cau hoi "vang mat" (e/chua/khong co) ma SQL dung INNER JOIN ->
    # self-check phai viet lai LEFT JOIN va executor chay SQL DA SUA.
    llm = _SeqLLM(json.dumps({"sql": _INNER}),
                  json.dumps({"ok": False, "sql": _LEFT,
                              "reason": "INNER JOIN loai mat san pham 0 don"}))
    st = new_tool_state(tool_name="sql_execute", raw_require="san pham nao dang e")
    st["skill"] = "SKILL"
    out = execute(st, llm=llm, executor=stub_sql)
    assert out["sql"] == _LEFT
    assert stub_sql.executed == [_LEFT]
    assert len(llm.seen) == 2
    assert _INNER in llm.seen[1]["user"]          # check nhin thay SQL vua sinh


def test_semantic_check_ok_keeps_original_sql(stub_sql):
    llm = _SeqLLM(json.dumps({"sql": "SELECT id, name FROM customers LIMIT 5"}),
                  json.dumps({"ok": True}))
    st = new_tool_state(tool_name="sql_execute", raw_require="liet ke khach hang")
    st["skill"] = "SKILL"
    out = execute(st, llm=llm, executor=stub_sql)
    assert out["sql"] == "SELECT id, name FROM customers LIMIT 5"
    assert len(llm.seen) == 2


def test_semantic_check_fails_open_on_garbage(stub_sql):
    # Check call tra rac -> giu SQL goc, KHONG lam hong happy path.
    llm = _SeqLLM(json.dumps({"sql": "SELECT id, name FROM customers LIMIT 5"}),
                  "toi khong chac lam")
    st = new_tool_state(tool_name="sql_execute", raw_require="liet ke khach hang")
    st["skill"] = "SKILL"
    out = execute(st, llm=llm, executor=stub_sql)
    assert out["error"] is None
    assert out["sql"] == "SELECT id, name FROM customers LIMIT 5"


def test_semantic_check_rewrite_still_goes_through_guard(stub_sql):
    # SQL sua lai van phai qua guard read-only nhu thuong.
    llm = _SeqLLM(json.dumps({"sql": "SELECT 1"}),
                  json.dumps({"ok": False, "sql": "DELETE FROM products"}))
    st = new_tool_state(tool_name="sql_execute", raw_require="x")
    st["skill"] = "SKILL"
    out = execute(st, llm=llm, executor=stub_sql)
    assert out["error"] is not None
    assert stub_sql.executed == []
