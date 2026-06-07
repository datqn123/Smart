"""Context compaction — message utils and context_compact node."""

from __future__ import annotations

import pytest
from langchain_core.messages import AIMessage, HumanMessage, RemoveMessage, SystemMessage

from app.config.graph_settings import GraphSettings
from app.graph.deps import GraphDeps
from app.graph.message_utils import (
    build_chat_context_text,
    count_human_turns,
    format_dialog_tail_for_sql,
    format_summary_prefix,
    messages_for_llm_context,
    messages_to_transcript,
    split_messages_for_compaction,
)
from app.graph.nodes.context_compact import make_context_compact_node
from app.graph.sql_executor import StubSqlExecutor
from app.graph.state import AgentState
from app.llm.registry import LlmRegistry
from tests.fake_llm import FakeLlmClient


def _pair(i: int) -> list:
    return [
        HumanMessage(content=f"user-{i}", id=f"h{i}"),
        AIMessage(content=f"ai-{i}", id=f"a{i}"),
    ]


def _many_messages(n_human: int) -> list:
    msgs: list = []
    for i in range(1, n_human + 1):
        msgs.extend(_pair(i))
    return msgs


def _summary_lines(n: int = 8) -> str:
    return "\n".join(f"Tóm tắt dòng {i}" for i in range(1, n + 1))


def test_count_human_turns() -> None:
    assert count_human_turns([]) == 0
    assert count_human_turns(_many_messages(3)) == 3


def test_split_messages_for_compaction_keeps_last_two_turns() -> None:
    msgs = _many_messages(5)
    old, keep = split_messages_for_compaction(msgs, keep_last_turns=2)
    assert len(old) == 6  # pairs 1-3
    assert len(keep) == 4  # pairs 4-5
    assert keep[0].content == "user-4"


def test_format_summary_prefix() -> None:
    assert format_summary_prefix(None) == ""
    assert "[Tóm tắt" in format_summary_prefix("abc")


def test_messages_for_llm_context_prepends_summary() -> None:
    msgs = [HumanMessage(content="hi")]
    out = messages_for_llm_context(msgs, "old facts", tail_cap=10)
    assert isinstance(out[0], SystemMessage)
    assert "old facts" in str(out[0].content)


def test_format_dialog_tail_includes_summary() -> None:
    tail = format_dialog_tail_for_sql(
        [HumanMessage(content="q"), AIMessage(content="a")],
        summary="tháng 3 doanh thu 1 tỷ",
        max_messages=12,
        max_chars=2000,
    )
    assert "[Tóm tắt" in tail
    assert "tháng 3" in tail
    assert "User: q" in tail


def test_build_chat_context_text() -> None:
    text = build_chat_context_text(
        [HumanMessage(content="câu mới")],
        "summary cũ",
        tail_messages=5,
        max_chars=4000,
    )
    assert "summary cũ" in text
    assert "câu mới" in text


def test_context_compact_skips_when_under_threshold() -> None:
    reg = LlmRegistry()
    fake = FakeLlmClient(reply=_summary_lines())
    reg.register("summarize", fake)
    settings = GraphSettings(context_compact_max_turns=10)
    node = make_context_compact_node(
        GraphDeps(llm_registry=reg, sql_executor=StubSqlExecutor(), settings=settings)
    )
    state: AgentState = {"messages": _many_messages(10)}
    out = node(state)
    assert out == {}
    assert fake.invoke_count == 0


def test_context_compact_disabled() -> None:
    reg = LlmRegistry()
    fake = FakeLlmClient(reply=_summary_lines())
    reg.register("summarize", fake)
    settings = GraphSettings(context_compact_enabled=False)
    node = make_context_compact_node(
        GraphDeps(llm_registry=reg, sql_executor=StubSqlExecutor(), settings=settings)
    )
    state: AgentState = {"messages": _many_messages(11)}
    assert node(state) == {}
    assert fake.invoke_count == 0


def test_context_compact_summarizes_and_prunes_at_turn_11() -> None:
    reg = LlmRegistry()
    summary = _summary_lines()
    fake = FakeLlmClient(reply=summary)
    reg.register("summarize", fake)
    settings = GraphSettings(
        context_compact_max_turns=10,
        context_compact_keep_last_turns=2,
    )
    node = make_context_compact_node(
        GraphDeps(llm_registry=reg, sql_executor=StubSqlExecutor(), settings=settings)
    )
    state: AgentState = {"messages": _many_messages(11), "context_compact_generation": 0}
    out = node(state)
    assert out.get("conversation_summary") == summary
    assert out.get("context_compact_generation") == 1
    removes = [m for m in out.get("messages", []) if isinstance(m, RemoveMessage)]
    assert len(removes) == 18  # 9 pairs × 2 messages
    assert fake.invoke_count == 1
    assert "user-1" in (fake.last_invoke_text or "")


def test_context_compact_includes_existing_summary_in_prompt() -> None:
    reg = LlmRegistry()
    fake = FakeLlmClient(reply=_summary_lines())
    reg.register("summarize", fake)
    settings = GraphSettings(context_compact_max_turns=10)
    node = make_context_compact_node(
        GraphDeps(llm_registry=reg, sql_executor=StubSqlExecutor(), settings=settings)
    )
    state: AgentState = {
        "messages": _many_messages(11),
        "conversation_summary": "Đã hỏi doanh thu tháng 3",
        "context_compact_generation": 1,
    }
    node(state)
    assert "Tóm tắt hiện có" in (fake.last_invoke_text or "")
    assert "tháng 3" in (fake.last_invoke_text or "")


def test_context_compact_llm_fail_does_not_prune() -> None:
    class FailingClient:
        def invoke_text(self, user: str, *, system: str | None = None) -> str:
            raise RuntimeError("boom")

    reg = LlmRegistry()
    reg.register("summarize", FailingClient())  # type: ignore[arg-type]
    settings = GraphSettings(context_compact_max_turns=10)
    node = make_context_compact_node(
        GraphDeps(llm_registry=reg, sql_executor=StubSqlExecutor(), settings=settings)
    )
    state: AgentState = {"messages": _many_messages(11)}
    out = node(state)
    assert "conversation_summary" not in out
    assert "messages" not in out


def test_messages_to_transcript() -> None:
    t = messages_to_transcript(
        [HumanMessage(content="h"), AIMessage(content="a")]
    )
    assert "User: h" in t
    assert "Assistant: a" in t


def test_compact_triggers_at_ratio() -> None:
    from app.harness.compact import CompactSubagent

    subagent = CompactSubagent(compact_context_ratio=0.70)

    assert subagent.should_compact(token_count=70, context_window=100)


@pytest.mark.asyncio
async def test_compact_preserves_constraints() -> None:
    from app.harness.compact import CompactSubagent

    block = await CompactSubagent(compact_context_ratio=0.70).compact(
        [
            HumanMessage(content="Xem doanh thu tháng 5"),
            AIMessage(content="Doanh thu là 10 triệu"),
            HumanMessage(content="Nhớ chỉ xem chi nhánh A"),
        ]
    )

    assert block.compact_block.startswith("[COMPACT]")
    assert "chi nhánh A" in block.compact_block
