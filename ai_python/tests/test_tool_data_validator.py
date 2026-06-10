import json
from app.tools.data_validator import execute, self_validate
from app.graph.state import new_tool_state


class _LLM:
    def __init__(self, verdict, reason="ok"):
        self._v = verdict; self._r = reason; self.seen = []
    def complete(self, *, system, user, role="default", temperature=None):
        self.seen.append(user)
        return json.dumps({"verdict": self._v, "reason": self._r})


def test_validator_pass_when_data_matches():  # fact-validator-check
    st = new_tool_state(tool_name="data_validator", raw_require="5 khach hang",
                        upstream_data={"rows": [{"id": 1}]})
    st["skill"] = "S"
    out = execute(st, llm=_LLM("pass", "du data"))
    assert out["verdict"] == "pass"


def test_validator_fail_when_data_mismatch():  # fact-validator-check
    st = new_tool_state(tool_name="data_validator", raw_require="doanh thu",
                        upstream_data={"rows": []})
    st["skill"] = "S"
    out = execute(st, llm=_LLM("fail", "rong"))
    assert out["verdict"] == "fail"
    assert out["reason"] == "rong"


def test_validator_reads_raw_require_and_data_in_prompt():
    llm = _LLM("pass")
    st = new_tool_state(tool_name="data_validator", raw_require="REQ-XYZ",
                        upstream_data={"rows": [{"id": 1}]})
    st["skill"] = "S"
    execute(st, llm=llm)
    assert "REQ-XYZ" in llm.seen[0]


def test_self_validate_rejects_unknown_verdict():
    st = new_tool_state(tool_name="data_validator", raw_require="x")
    st["output"] = {"verdict": "maybe", "reason": "?"}
    ok, err = self_validate(st)
    assert ok is False


class _BadJsonLLM:
    def complete(self, *, system, user, role="default", temperature=None):
        return "khong phai JSON"


def test_validator_handles_malformed_llm_json():  # resilience
    # LLM tra output khong parse duoc -> execute KHONG raise; verdict=None
    # -> self_validate fail -> SM retry.
    st = new_tool_state(tool_name="data_validator", raw_require="x",
                        upstream_data={"rows": []})
    st["skill"] = "S"
    out = execute(st, llm=_BadJsonLLM())
    assert out["verdict"] is None
    st["output"] = out
    ok, _ = self_validate(st)
    assert ok is False
