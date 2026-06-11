import json
from app.tools.answer_composer import execute, self_validate
from app.graph.state import new_tool_state


class _LLM:
    def __init__(self, answer): self._a = answer
    def complete(self, *, system, user, role="default", temperature=None):
        return json.dumps({"answer": self._a})


def test_composer_builds_answer_with_next_step():  # fact-composer (next-step)
    st = new_tool_state(tool_name="answer_composer", raw_require="5 khach hang",
                        upstream_data={"rows": [{"id": 1, "name": "Acme"}]})
    st["skill"] = "S"
    out = execute(st, llm=_LLM("Day la khach hang.\nGợi ý: xem don hang?"))
    assert "Gợi ý:" in out["answer"]


def test_self_validate_requires_next_step_marker():  # fact-composer
    st = new_tool_state(tool_name="answer_composer", raw_require="x")
    st["output"] = {"answer": "Tra loi nhung thieu goi y."}
    ok, err = self_validate(st)
    assert ok is False and "gợi ý" in err.lower()


def test_self_validate_passes_with_marker():
    st = new_tool_state(tool_name="answer_composer", raw_require="x")
    st["output"] = {"answer": "Tra loi.\nGợi ý: lam tiep X?"}
    ok, err = self_validate(st)
    assert ok is True


class _BadJsonLLM:
    def complete(self, *, system, user, role="default", temperature=None):
        return "oops not json"


def test_composer_handles_malformed_llm_json():  # resilience
    # LLM tra output khong parse duoc -> execute KHONG raise; answer=""
    # -> self_validate fail -> SM retry.
    st = new_tool_state(tool_name="answer_composer", raw_require="x",
                        upstream_data={})
    st["skill"] = "S"
    out = execute(st, llm=_BadJsonLLM())
    assert out["answer"] == ""
    st["output"] = out
    ok, _ = self_validate(st)
    assert ok is False


class _RecLLM:
    def __init__(self, answer): self._a = answer; self.seen = []
    def complete(self, *, system, user, role="default", temperature=None):
        self.seen.append(user)
        return json.dumps({"answer": self._a})


def test_prompt_has_memory_block_when_summary():
    llm = _RecLLM("X.\nGợi ý: tiep?")
    st = new_tool_state(tool_name="answer_composer", raw_require="con thang truoc?",
                        upstream_data={"rows": []},
                        memory_summary="User dang xem doanh thu thang 5/2026")
    st["skill"] = "S"
    execute(st, llm=llm)
    assert "[Boi canh hoi thoai truoc]: User dang xem doanh thu thang 5/2026" in llm.seen[0]


def test_prompt_no_memory_block_when_none():
    llm = _RecLLM("X.\nGợi ý: tiep?")
    st = new_tool_state(tool_name="answer_composer", raw_require="x")
    st["skill"] = "S"
    execute(st, llm=llm)
    assert "[Boi canh hoi thoai truoc]" not in llm.seen[0]
