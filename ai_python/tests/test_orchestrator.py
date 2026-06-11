import pytest
from app.graph.orchestrator import run_session
from app.harness.turn_context import TurnContext
from tests.conftest import FakeLLM


async def _collect(gen):
    return [e async for e in gen]


def _deps_with_fake_dispatch(monkeypatch, results_by_tool):
    calls = []
    def fake_dispatch(tool_name, *, raw_require, upstream_data, llm, deps,
                      validator_ran=False, memory_summary=None):
        calls.append(tool_name)
        return results_by_tool[tool_name]
    monkeypatch.setattr("app.graph.orchestrator.dispatch", fake_dispatch)
    return calls


def _sm(*selects):
    return FakeLLM(tool_selects=list(selects))


@pytest.mark.asyncio
async def test_happy_path_order_sql_validate_compose(monkeypatch):
    calls = _deps_with_fake_dispatch(monkeypatch, {
        "sql_execute": {"output": {"rows": [{"id": 1}]}, "valid": True, "validation_error": None},
        "data_validator": {"output": {"verdict": "pass", "reason": "ok"}, "valid": True, "validation_error": None},
        "answer_composer": {"output": {"answer": "Tra loi.\nGợi ý: tiep?"}, "valid": True, "validation_error": None},
    })
    llm = _sm(("sql_execute", {"reasoning": "r", "require": "liet ke khach hang"}),
              ("data_validator", {"reasoning": "r"}),
              ("answer_composer", {"reasoning": "r"}))
    ctx = TurnContext(raw_require="liet ke khach hang", user_id="u", thread_id="t")
    events = await _collect(run_session(ctx, llm_sm=llm, llm_tool=llm, deps={},
                                        max_steps=6, retry_cap=2))
    assert calls == ["sql_execute", "data_validator", "answer_composer"]
    types = [e["type"] for e in events]
    assert "answer" in types and "done" in types


@pytest.mark.asyncio
async def test_validator_fail_triggers_clarify_and_pause(monkeypatch):
    _deps_with_fake_dispatch(monkeypatch, {
        "sql_execute": {"output": {"rows": []}, "valid": True, "validation_error": None},
        "data_validator": {"output": {"verdict": "fail", "reason": "rong"}, "valid": True, "validation_error": None},
    })
    llm = _sm(("sql_execute", {"reasoning": "r", "require": "doanh thu"}),
              ("data_validator", {"reasoning": "r"}),
              ("request_clarification", {"reasoning": "fail",
                                         "message": "Khoang thoi gian nao?"}))
    ctx = TurnContext(raw_require="doanh thu", user_id="u", thread_id="t")
    events = await _collect(run_session(ctx, llm_sm=llm, llm_tool=llm, deps={},
                                        max_steps=6, retry_cap=2))
    clarify = [e for e in events if e["type"] == "clarify"]
    assert clarify and clarify[0]["data"]["message"] == "Khoang thoi gian nao?"


@pytest.mark.asyncio
async def test_budget_exhaustion_aborts_safely(monkeypatch):
    _deps_with_fake_dispatch(monkeypatch, {
        "sql_execute": {"output": {"rows": [{"id": 1}]}, "valid": True, "validation_error": None},
    })
    llm = _sm(*[("sql_execute", {"reasoning": "loop", "require": "x"})
                for _ in range(20)])
    ctx = TurnContext(raw_require="x", user_id="u", thread_id="t")
    events = await _collect(run_session(ctx, llm_sm=llm, llm_tool=llm, deps={},
                                        max_steps=3, retry_cap=2))
    err = [e for e in events if e["type"] == "error"]
    assert err and "gioi han" in err[0]["data"]["message"].lower()


@pytest.mark.asyncio
async def test_retry_cap_blocks_infinite_retry(monkeypatch):
    # tool fail lien tuc -> SM goi lai cung tool (retry) -> cham cap thi
    # orchestrator KHONG dispatch nua, tra quyen ve SM.
    calls = _deps_with_fake_dispatch(monkeypatch, {
        "sql_execute": {"output": {"rows": [], "error": "loi"}, "valid": False,
                        "validation_error": "loi"},
    })
    llm = _sm(*[("sql_execute", {"reasoning": "thu lai", "require": "x"})
                for _ in range(6)])
    ctx = TurnContext(raw_require="x", user_id="u", thread_id="t")
    await _collect(run_session(ctx, llm_sm=llm, llm_tool=llm, deps={},
                               max_steps=6, retry_cap=2))
    # 1 lan dau (call_tool) + 2 retry trong cap = 3 lan dispatch toi da
    assert calls.count("sql_execute") == 3


@pytest.mark.asyncio
async def test_resume_continues_from_snapshot(monkeypatch):  # fact-validator-hitl
    _deps_with_fake_dispatch(monkeypatch, {
        "data_validator": {"output": {"verdict": "pass", "reason": "ok"}, "valid": True, "validation_error": None},
        "answer_composer": {"output": {"answer": "OK.\nGợi ý: tiep?"}, "valid": True, "validation_error": None},
    })
    llm = _sm(("data_validator", {"reasoning": "revalidate"}),
              ("answer_composer", {"reasoning": "compose"}))
    ctx = TurnContext(raw_require="doanh thu", user_id="u", thread_id="t",
                      clarification_response="Quy 1 nam 2026")
    snapshot = {"raw_require": "doanh thu", "thread_id": "t",
                "tool_results": {"sql_execute": {"rows": [{"rev": 100}]}},
                "history": [], "retry_counts": {},
                "pending_clarification": {"message": "Khi nao?"}}
    events = await _collect(run_session(ctx, llm_sm=llm, llm_tool=llm, deps={},
                                        max_steps=6, retry_cap=2,
                                        resume_snapshot=snapshot))
    assert "sql_execute" in snapshot["tool_results"]   # data cu giu nguyen
    assert any(e["type"] == "answer" for e in events)


def test_build_upstream_merges_all_tool_results():
    # Regression bai hoc cu: composer phai thay ca rows (sql_execute) lan
    # verdict (data_validator) — khong mat data khi nhieu tool da chay.
    from app.graph.orchestrator import _build_upstream
    state = {"tool_results": {
        "sql_execute": {"rows": [{"name": "A", "tong_ton": 9}], "columns": ["name", "tong_ton"], "error": None},
        "data_validator": {"verdict": "pass", "reason": "ok"},
    }}
    up = _build_upstream(state)
    assert up["rows"] == [{"name": "A", "tong_ton": 9}]
    assert up["verdict"] == "pass"


@pytest.mark.asyncio
async def test_dispatch_uses_resolved_require_and_memory_summary(monkeypatch):
    captured = {}

    def fake_dispatch(tool_name, *, raw_require, upstream_data, llm, deps,
                      validator_ran=False, memory_summary=None):
        captured["raw_require"] = raw_require
        captured["memory_summary"] = memory_summary
        return {"output": {"rows": [{"x": 1}]}, "valid": True,
                "validation_error": None}

    monkeypatch.setattr("app.graph.orchestrator.dispatch", fake_dispatch)
    llm = _sm(("sql_execute", {"reasoning": "r",
                               "require": "doanh thu thang 4/2026"}),
              ("finish", {"reasoning": "done", "message": "xong"}))
    ctx = TurnContext(raw_require="con thang truoc?", user_id="u", thread_id="t")
    mem = {"summary": "dang xem doanh thu thang 5/2026", "turns": []}
    await _collect(run_session(ctx, llm_sm=llm, llm_tool=llm, deps={},
                               memory_context=mem))
    assert captured["raw_require"] == "doanh thu thang 4/2026"
    assert captured["memory_summary"] == "dang xem doanh thu thang 5/2026"


@pytest.mark.asyncio
async def test_done_event_contains_raw_require():
    llm = _sm(("finish", {"reasoning": "x", "message": "tra loi"}))
    ctx = TurnContext(raw_require="cau hoi goc", user_id="u", thread_id="t")
    events = await _collect(run_session(ctx, llm_sm=llm, llm_tool=llm, deps={}))
    done = [e for e in events if e["type"] == "done"][0]
    assert done["data"]["raw_require"] == "cau hoi goc"


@pytest.mark.asyncio
async def test_resume_restores_raw_require_from_snapshot():
    llm = _sm(("finish", {"reasoning": "x", "message": "ok"}))
    ctx = TurnContext(raw_require="thang 4", user_id="u", thread_id="t",
                      clarification_response="thang 4")
    snap = {"raw_require": "doanh thu", "tool_results": {}, "history": [],
            "retry_counts": {}}
    events = await _collect(run_session(ctx, llm_sm=llm, llm_tool=llm, deps={},
                                        resume_snapshot=snap))
    done = [e for e in events if e["type"] == "done"][0]
    assert done["data"]["raw_require"].startswith("doanh thu")
    assert "[Bo sung tu user]: thang 4" in done["data"]["raw_require"]


@pytest.mark.asyncio
async def test_validator_fail_still_allows_composer(monkeypatch):
    # Regression absence-case ("gao te 5kg da ban duoc don nao chua"):
    # rows=[] -> verdict=fail la cau tra loi dung — SM phai compose duoc
    # cau "chua co don nao", khong bi guard chan den het budget.
    flags = {}

    def fake_dispatch(tool_name, *, raw_require, upstream_data, llm, deps,
                      validator_ran=False, memory_summary=None):
        flags[tool_name] = validator_ran
        results = {
            "sql_execute": {"output": {"rows": [], "columns": ["id"], "error": None},
                            "valid": True, "validation_error": None},
            "data_validator": {"output": {"verdict": "fail", "reason": "rong"},
                               "valid": True, "validation_error": None},
            "answer_composer": {"output": {"answer": "Chua co don nao.\nGợi ý: xem ton kho?"},
                                "valid": True, "validation_error": None},
        }
        return results[tool_name]

    monkeypatch.setattr("app.graph.orchestrator.dispatch", fake_dispatch)
    llm = _sm(("sql_execute", {"reasoning": "r", "require": "don hang gao te 5kg"}),
              ("data_validator", {"reasoning": "r"}),
              ("answer_composer", {"reasoning": "rows rong la ket qua hop le"}))
    ctx = TurnContext(raw_require="gao te 5kg da ban duoc don nao chua",
                      user_id="u", thread_id="t")
    events = await _collect(run_session(ctx, llm_sm=llm, llm_tool=llm, deps={},
                                        max_steps=6, retry_cap=2))
    assert flags["answer_composer"] is True   # validator da chay -> duoc phep
    answer = [e for e in events if e["type"] == "answer"]
    assert answer and "Chua co don nao" in answer[0]["data"]["text"]
