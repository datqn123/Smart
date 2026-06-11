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


def test_sse_frontend_single_line():
    from app.harness.sse_emitter import sse_frontend
    frame = sse_frontend("progress", "Dang xu ly")
    assert frame == "event: progress\ndata: Dang xu ly\n\n"


def test_sse_frontend_multiline_splits_data_lines():
    # Regression: answer nhieu dong nhet sau 1 'data:' duy nhat lam
    # EventSource/browser bo qua moi dong sau dong dau (answer bi cat).
    from app.harness.sse_emitter import sse_frontend
    frame = sse_frontend("delta_full", "Dong 1:\n1. SP A: 120\n2. SP B: 90")
    assert frame == ("event: delta_full\n"
                     "data: Dong 1:\n"
                     "data: 1. SP A: 120\n"
                     "data: 2. SP B: 90\n\n")


def test_sse_frontend_normalizes_crlf():
    from app.harness.sse_emitter import sse_frontend
    frame = sse_frontend("delta_full", "a\r\nb\rc")
    assert frame == "event: delta_full\ndata: a\ndata: b\ndata: c\n\n"
