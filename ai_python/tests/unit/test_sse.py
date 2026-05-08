from app.core.sse import sse_event


def test_sse_single_line() -> None:
    out = sse_event("delta", "hello")
    assert out.endswith("\n")
    assert out == "event: delta\ndata: hello\n\n"


def test_sse_multiline_splits_into_data_lines() -> None:
    out = sse_event("delta", "a\nb")
    assert out == "event: delta\ndata: a\ndata: b\n\n"


def test_sse_empty_string_emits_blank_data_line() -> None:
    out = sse_event("ping", "")
    assert out.endswith("\n")
    assert out == "event: ping\ndata: \n\n"
