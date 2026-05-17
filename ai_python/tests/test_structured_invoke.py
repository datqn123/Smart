"""Structured invoke — JSON path with a mocked chat model."""

from __future__ import annotations

from unittest.mock import MagicMock

from langchain_core.messages import AIMessage, HumanMessage

from app.llm.schemas import IntentOutput, SqlReviewOutput
from app.llm.structured import structured_invoke


def test_structured_invoke_json_fallback_intent() -> None:
    chat = MagicMock()
    chat.invoke.return_value = AIMessage(content='{"intent": "system_data_query"}')

    out = structured_invoke(chat, [HumanMessage(content="classify")], IntentOutput, max_retries=2)
    assert out.intent == "system_data_query"


def test_structured_invoke_with_json_output_contract() -> None:
    """Compact contract avoids embedding full Pydantic JSON Schema in the prompt."""
    chat = MagicMock()
    chat.invoke.return_value = AIMessage(content='{"intent": "general_chat"}')
    contract = 'Single key "intent" only.'

    out = structured_invoke(
        chat,
        [HumanMessage(content="xin chào")],
        IntentOutput,
        max_retries=2,
        json_output_contract=contract,
    )
    assert out.intent == "general_chat"
    last_msg = chat.invoke.call_args[0][0][-1]
    sent = str(last_msg.content)
    assert contract in sent
    assert "$defs" not in sent
    chat = MagicMock()
    chat.invoke.return_value = AIMessage(
        content='```json\n{"ok": false, "issues": ["bad"]}\n```',
    )

    out = structured_invoke(chat, [HumanMessage(content="review")], SqlReviewOutput)
    assert out.ok is False
    assert out.issues == ["bad"]
