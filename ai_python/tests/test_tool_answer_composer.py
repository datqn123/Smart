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
