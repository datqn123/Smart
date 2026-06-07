"""Tests for LLM usage extraction — Slice B (FR-2)."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage

from app.llm.openai_compatible import InvokeUsage, OpenAICompatibleChatClient, extract_usage


# ---------------------------------------------------------------------------
# extract_usage() unit tests
# ---------------------------------------------------------------------------

def _make_msg(*, usage_metadata=None, response_metadata=None) -> AIMessage:
    msg = AIMessage(content="hi")
    if usage_metadata is not None:
        object.__setattr__(msg, "usage_metadata", usage_metadata)
    if response_metadata is not None:
        object.__setattr__(msg, "response_metadata", response_metadata)
    return msg


def test_extract_usage_none_returns_zero():
    u = extract_usage(None)
    assert u.prompt_tokens == 0
    assert u.completion_tokens == 0


def test_extract_usage_usage_metadata_shape():
    msg = _make_msg(usage_metadata={"input_tokens": 10, "output_tokens": 20})
    u = extract_usage(msg)
    assert u.prompt_tokens == 10
    assert u.completion_tokens == 20
    assert u.total_tokens == 30


def test_extract_usage_token_usage_shape():
    msg = _make_msg(
        response_metadata={"token_usage": {"prompt_tokens": 5, "completion_tokens": 15}}
    )
    u = extract_usage(msg)
    assert u.prompt_tokens == 5
    assert u.completion_tokens == 15


def test_extract_usage_usage_key_shape():
    msg = _make_msg(
        response_metadata={"usage": {"prompt_tokens": 7, "completion_tokens": 3}}
    )
    u = extract_usage(msg)
    assert u.prompt_tokens == 7
    assert u.completion_tokens == 3


def test_extract_usage_no_metadata_returns_zero():
    msg = AIMessage(content="hi")
    u = extract_usage(msg)
    assert u.prompt_tokens == 0
    assert u.completion_tokens == 0


def test_extract_usage_zero_tokens_ignored_falls_through():
    # usage_metadata with all zeros should fall through to response_metadata
    msg = _make_msg(
        usage_metadata={"input_tokens": 0, "output_tokens": 0},
        response_metadata={"token_usage": {"prompt_tokens": 3, "completion_tokens": 4}},
    )
    u = extract_usage(msg)
    assert u.prompt_tokens == 3
    assert u.completion_tokens == 4


# ---------------------------------------------------------------------------
# last_usage set after invoke_text / ainvoke_text
# ---------------------------------------------------------------------------

def test_invoke_text_updates_last_usage():
    chat_mock = MagicMock()
    out = AIMessage(content="answer")
    object.__setattr__(out, "usage_metadata", {"input_tokens": 11, "output_tokens": 22})
    chat_mock.invoke.return_value = out

    client = OpenAICompatibleChatClient(chat_mock)
    client.invoke_text("hi")

    assert client.last_usage.prompt_tokens == 11
    assert client.last_usage.completion_tokens == 22


@pytest.mark.asyncio
async def test_ainvoke_text_updates_last_usage():
    chat_mock = MagicMock()
    out = AIMessage(content="answer")
    object.__setattr__(out, "usage_metadata", {"input_tokens": 3, "output_tokens": 7})
    chat_mock.ainvoke = AsyncMock(return_value=out)

    client = OpenAICompatibleChatClient(chat_mock)
    await client.ainvoke_text("hi")

    assert client.last_usage.prompt_tokens == 3
    assert client.last_usage.completion_tokens == 7


# ---------------------------------------------------------------------------
# last_usage set after structured_predict / astructured_predict
# ---------------------------------------------------------------------------

from pydantic import BaseModel


class _Schema(BaseModel):
    answer: str


def test_structured_predict_updates_last_usage():
    from langchain_core.messages import HumanMessage, SystemMessage

    chat_mock = MagicMock()
    out = AIMessage(content='{"answer": "yes"}')
    object.__setattr__(out, "usage_metadata", {"input_tokens": 2, "output_tokens": 4})
    chat_mock.invoke.return_value = out

    client = OpenAICompatibleChatClient(chat_mock)
    result = client.structured_predict(
        [HumanMessage(content="q")], _Schema, json_output_contract='{"answer": "string"}'
    )

    assert result.answer == "yes"
    assert client.last_usage.prompt_tokens == 2
    assert client.last_usage.completion_tokens == 4


@pytest.mark.asyncio
async def test_astructured_predict_updates_last_usage():
    from langchain_core.messages import HumanMessage

    chat_mock = MagicMock()
    out = AIMessage(content='{"answer": "no"}')
    object.__setattr__(out, "usage_metadata", {"input_tokens": 6, "output_tokens": 8})
    chat_mock.ainvoke = AsyncMock(return_value=out)

    client = OpenAICompatibleChatClient(chat_mock)
    result = await client.astructured_predict(
        [HumanMessage(content="q")], _Schema, json_output_contract='{"answer": "string"}'
    )

    assert result.answer == "no"
    assert client.last_usage.prompt_tokens == 6
    assert client.last_usage.completion_tokens == 8
