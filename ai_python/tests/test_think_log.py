import json
import logging
import pytest
from app.harness.think_log import think
from app.graph.state import new_tool_state


def test_think_writes_to_think_logger(caplog):
    with caplog.at_level(logging.INFO, logger="think"):
        think("SM", 'phan tich "%s"', "cau hoi")
    rec = caplog.records[-1]
    assert rec.name == "think"
    assert rec.getMessage() == '[SM] phan tich "cau hoi"'


def test_sql_execute_emits_thinking_trace(stub_sql, caplog):
    # Moi buoc cua tool phai ke lai duoc: bat dau -> SQL nhap ->
    # tu kiem tra -> ket qua. Day la yeu cau "log nhu agent dang suy nghi".
    from app.tools.sql_execute import execute

    class _LLM:
        def complete(self, *, system, user, role="default", temperature=None):
            return json.dumps({"sql": "SELECT id, name FROM customers LIMIT 5"})

    st = new_tool_state(tool_name="sql_execute", raw_require="liet ke khach hang")
    st["skill"] = "SKILL"
    with caplog.at_level(logging.INFO, logger="think"):
        execute(st, llm=_LLM(), executor=stub_sql)
    msgs = [r.getMessage() for r in caplog.records if r.name == "think"]
    assert any(m.startswith("[sql_execute] bat dau dich yeu cau") for m in msgs)
    assert any("SQL nhap" in m for m in msgs)
    assert any("tu kiem tra" in m for m in msgs)
    assert any("-> chay xong: 1 dong" in m for m in msgs)


def test_validator_emits_verdict_thinking(caplog):
    from app.tools.data_validator import execute
    from tests.conftest import FakeLLM

    _LLM = lambda: FakeLLM(  # noqa: E731
        structured=[{"verdict": "pass", "reason": "du lieu day du"}])

    st = new_tool_state(tool_name="data_validator", raw_require="x",
                        upstream_data={"rows": [{"a": 1}, {"a": 2}]})
    st["skill"] = "SKILL"
    with caplog.at_level(logging.INFO, logger="think"):
        execute(st, llm=_LLM())
    msgs = [r.getMessage() for r in caplog.records if r.name == "think"]
    assert any("soi ket qua (2 dong)" in m for m in msgs)
    assert any("-> dat: du lieu day du" in m for m in msgs)
