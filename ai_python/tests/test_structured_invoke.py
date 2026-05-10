"""Structured invoke — JSON path with a mocked chat model."""

from __future__ import annotations

from unittest.mock import MagicMock

from langchain_core.messages import AIMessage, HumanMessage

from app.llm.schemas import IntentOutput, SqlReviewOutput
from app.llm.structured import structured_invoke


def test_structured_invoke_json_fallback_intent() -> None:
    chat = MagicMock()
    chat.with_structured_output.side_effect = RuntimeError("no native")
    chat.invoke.return_value = AIMessage(content='{"intent": "system_data_query"}')

    out = structured_invoke(chat, [HumanMessage(content="classify")], IntentOutput, max_retries=2)
    assert out.intent == "system_data_query"


def test_structured_invoke_fence_sql_review() -> None:
    chat = MagicMock()
    chat.with_structured_output.side_effect = RuntimeError("no native")
    chat.invoke.return_value = AIMessage(
        content='```json\n{"ok": false, "issues": ["bad"]}\n```',
    )

    out = structured_invoke(chat, [HumanMessage(content="review")], SqlReviewOutput)
    assert out.ok is False
    assert out.issues == ["bad"]
