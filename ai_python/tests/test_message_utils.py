"""message_utils — current user question extraction."""

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage

from app.graph.message_utils import (
    format_dialog_tail_for_sql,
    latest_human_question,
    strip_embedded_chat_transcript,
)


def test_latest_human_question_prefers_last_human() -> None:
    msgs = [
        HumanMessage(content="câu một"),
        AIMessage(content="trả lời một"),
        HumanMessage(content="xuất bao nhiêu lô hàng"),
    ]
    assert latest_human_question(msgs) == "xuất bao nhiêu lô hàng"


def test_latest_human_question_skips_trailing_ai() -> None:
    msgs = [
        HumanMessage(content="hỏi A"),
        HumanMessage(content="hỏi B"),
        AIMessage(content="đáp B"),
    ]
    assert latest_human_question(msgs) == "hỏi B"


def test_format_dialog_tail_orders_and_truncates() -> None:
    msgs = [
        HumanMessage(content="câu một"),
        AIMessage(content="trả lời một có 103"),
        HumanMessage(content="đơn đó bao nhiêu tiền"),
    ]
    full = format_dialog_tail_for_sql(msgs, max_messages=10, max_chars=500)
    assert "User: câu một" in full
    assert "Assistant: trả lời một" in full
    assert "đơn đó" in full
    long_a = "x" * 3000
    msgs2 = [HumanMessage(content="a"), AIMessage(content=long_a), HumanMessage(content="b")]
    t = format_dialog_tail_for_sql(msgs2, max_messages=6, max_chars=100)
    assert len(t) <= 100
    assert "b" in t


def test_strip_embedded_transcript() -> None:
    blob = (
        "User: nhập bao nhiêu đơn\n"
        "Assistant: Trong tháng này đã nhập 103 đơn.\n"
        "User: xuất bao nhiêu lô hàng"
    )
    assert strip_embedded_chat_transcript(blob) == "xuất bao nhiêu lô hàng"
