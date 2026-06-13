# ai_python/tests/eval/test_golden_sql.py
"""Golden set eval — tang re: cham SQL ngay tai executor, khong cham DB.

Moi case = 1 test:
  YAML history -> memory_context gia -> analyze() SM THAT     (1 LLM call)
      assert sm_tool, sm_require_contains
  -> dispatch('sql_execute') qua subgraph THAT, executor=FakeExecutor
     (SqlDraft + SemanticCheck = 2 LLM call)
      assert sql_contains / sql_not_contains / sql_regex / sql_not_regex
SQL duoc cham la SQL SAU semantic self-check va SAU assert_read_only —
dung chuoi se cham DB trong production (executor chi nhan SQL da qua guard).
"""
import re
from pathlib import Path

import pytest
import yaml

from app.graph.dispatcher import dispatch
from app.graph.state import new_session_state
from app.tools.session_manager import analyze

pytestmark = pytest.mark.llm

_CASES = yaml.safe_load(
    (Path(__file__).parent / "golden.yaml").read_text(encoding="utf-8"))


def _norm(text: str) -> str:
    """Chuan hoa de so barem: lowercase + collapse whitespace (quy uoc golden.yaml)."""
    return " ".join(text.split()).lower()


@pytest.mark.parametrize("case", _CASES, ids=[c["id"] for c in _CASES])
def test_golden(case, llm_sm, llm_tool, fake_executor):
    expect = case["expect"]

    # --- Muc B: do tu Session Manager tro di ---
    state = new_session_state(raw_require=case["require"],
                              thread_id=f"eval-{case['id']}")
    memory_context = {"turns": case.get("history") or [], "summary": None}
    decision = analyze(state, llm=llm_sm, memory_context=memory_context)

    actual_tool = decision.tool_name or decision.action
    assert actual_tool == expect["sm_tool"], (
        f"SM chon {actual_tool!r} thay vi {expect['sm_tool']!r} "
        f"(reasoning: {decision.reasoning})")

    if expect["sm_tool"] != "sql_execute":
        return  # case clarify/finish: barem chi co quyet dinh SM

    # require SM gui tool — dung cong thuc orchestrator (orchestrator.py:99)
    require = decision.resolved_require or state["raw_require"]
    for sub in expect.get("sm_require_contains") or []:
        assert sub.lower() in require.lower(), (
            f"require SM gui tool thieu {sub!r}: {require!r}")

    # --- Tang re: chay sql_execute that voi DB gia, dung tai executor ---
    result = dispatch("sql_execute", raw_require=require, upstream_data={},
                      llm=llm_tool, deps={"executor": fake_executor})
    sql = fake_executor.captured_sql
    assert sql, (f"SQL khong cham executor — "
                 f"error: {(result['output'] or {}).get('error')!r}")

    n = _norm(sql)
    for sub in expect.get("sql_contains") or []:
        assert _norm(sub) in n, f"SQL thieu {sub!r}:\n{sql}"
    for sub in expect.get("sql_not_contains") or []:
        assert _norm(sub) not in n, f"SQL chua chuoi cam {sub!r}:\n{sql}"
    if expect.get("sql_regex"):
        assert re.search(expect["sql_regex"], n), (
            f"SQL khong khop pattern {expect['sql_regex']!r}:\n{sql}")
    if expect.get("sql_not_regex"):
        assert not re.search(expect["sql_not_regex"], n), (
            f"SQL khop pattern cam {expect['sql_not_regex']!r}:\n{sql}")
