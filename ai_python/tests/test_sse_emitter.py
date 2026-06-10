import json
from app.harness.sse_emitter import sse_format, SSEEvent


def test_sse_format_nests_under_harness_key():  # R6 chong flatten
    line = sse_format("tool_call", {"tool_name": "sql_execute"})
    assert line.startswith("data: ")
    assert line.endswith("\n\n")
    body = json.loads(line[len("data: "):].strip())
    assert set(body.keys()) == {"harness"}            # chi 1 key goc
    assert body["harness"]["type"] == "tool_call"
    assert body["harness"]["data"]["tool_name"] == "sql_execute"


def test_sse_event_types_enum():
    assert SSEEvent.CLARIFY == "clarify"
    assert SSEEvent.ANSWER == "answer"
    assert SSEEvent.DONE == "done"
    assert SSEEvent.ERROR == "error"


def test_unicode_preserved():
    line = sse_format("answer", {"text": "Doanh thu quy 1"})
    assert "Doanh thu quy 1" in line  # ensure_ascii=False
