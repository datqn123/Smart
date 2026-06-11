from app.config.llm_client import StructuredOutputError
from app.tools.answer_composer import execute, self_validate
from app.graph.state import new_tool_state
from tests.conftest import FakeLLM


def _llm(answer):
    return FakeLLM(structured=[{"answer": answer}])


def test_composer_builds_answer_with_next_step():  # fact-composer (next-step)
    st = new_tool_state(tool_name="answer_composer", raw_require="5 khach hang",
                        upstream_data={"rows": [{"id": 1, "name": "Acme"}]})
    st["skill"] = "S"
    out = execute(st, llm=_llm("Day la khach hang.\nGợi ý: xem don hang?"))
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


def test_composer_handles_structured_failure():  # resilience
    # complete_structured het 2 attempt -> execute KHONG raise; answer=""
    # -> self_validate fail -> SM retry.
    st = new_tool_state(tool_name="answer_composer", raw_require="x",
                        upstream_data={})
    st["skill"] = "S"
    out = execute(st, llm=FakeLLM(structured=[StructuredOutputError("2 attempts")]))
    assert out["answer"] == ""
    st["output"] = out
    ok, _ = self_validate(st)
    assert ok is False


def test_prompt_has_memory_block_when_summary():
    llm = _llm("X.\nGợi ý: tiep?")
    st = new_tool_state(tool_name="answer_composer", raw_require="con thang truoc?",
                        upstream_data={"rows": []},
                        memory_summary="User dang xem doanh thu thang 5/2026")
    st["skill"] = "S"
    execute(st, llm=llm)
    assert ("[Boi canh hoi thoai truoc]: User dang xem doanh thu thang 5/2026"
            in llm.structured_calls[0]["user"])


def test_prompt_no_memory_block_when_none():
    llm = _llm("X.\nGợi ý: tiep?")
    st = new_tool_state(tool_name="answer_composer", raw_require="x")
    st["skill"] = "S"
    execute(st, llm=llm)
    assert "[Boi canh hoi thoai truoc]" not in llm.structured_calls[0]["user"]
