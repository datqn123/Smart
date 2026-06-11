from app.config.llm_client import StructuredOutputError
from app.tools.data_validator import execute, self_validate
from app.graph.state import new_tool_state
from tests.conftest import FakeLLM


def _llm(verdict, reason="ok"):
    return FakeLLM(structured=[{"verdict": verdict, "reason": reason}])


def test_validator_pass_when_data_matches():  # fact-validator-check
    st = new_tool_state(tool_name="data_validator", raw_require="5 khach hang",
                        upstream_data={"rows": [{"id": 1}]})
    st["skill"] = "S"
    out = execute(st, llm=_llm("pass", "du data"))
    assert out["verdict"] == "pass"


def test_validator_fail_when_data_mismatch():  # fact-validator-check
    st = new_tool_state(tool_name="data_validator", raw_require="doanh thu",
                        upstream_data={"rows": []})
    st["skill"] = "S"
    out = execute(st, llm=_llm("fail", "rong"))
    assert out["verdict"] == "fail"
    assert out["reason"] == "rong"


def test_validator_reads_raw_require_and_data_in_prompt():
    llm = _llm("pass")
    st = new_tool_state(tool_name="data_validator", raw_require="REQ-XYZ",
                        upstream_data={"rows": [{"id": 1}]})
    st["skill"] = "S"
    execute(st, llm=llm)
    assert "REQ-XYZ" in llm.structured_calls[0]["user"]


def test_self_validate_rejects_unknown_verdict():
    st = new_tool_state(tool_name="data_validator", raw_require="x")
    st["output"] = {"verdict": "maybe", "reason": "?"}
    ok, err = self_validate(st)
    assert ok is False


def test_validator_handles_structured_failure():  # resilience
    # complete_structured het 2 attempt -> execute KHONG raise; verdict=None
    # -> self_validate fail -> SM retry.
    st = new_tool_state(tool_name="data_validator", raw_require="x",
                        upstream_data={"rows": []})
    st["skill"] = "S"
    out = execute(st, llm=FakeLLM(structured=[StructuredOutputError("2 attempts failed")]))
    assert out["verdict"] is None
    st["output"] = out
    ok, _ = self_validate(st)
    assert ok is False


def test_prompt_has_memory_block_when_summary():
    llm = _llm("pass")
    st = new_tool_state(tool_name="data_validator", raw_require="con thang truoc?",
                        upstream_data={"rows": [{"id": 1}]},
                        memory_summary="User dang xem doanh thu thang 5/2026")
    st["skill"] = "S"
    execute(st, llm=llm)
    assert ("[Boi canh hoi thoai truoc]: User dang xem doanh thu thang 5/2026"
            in llm.structured_calls[0]["user"])


def test_prompt_no_memory_block_when_none():
    llm = _llm("pass")
    st = new_tool_state(tool_name="data_validator", raw_require="x",
                        upstream_data={"rows": []})
    st["skill"] = "S"
    execute(st, llm=llm)
    assert "[Boi canh hoi thoai truoc]" not in llm.structured_calls[0]["user"]
