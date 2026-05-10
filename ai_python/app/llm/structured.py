"""Structured output: try LangChain native; fallback JSON + parse + retry."""

from __future__ import annotations

import json
import re
from typing import TypeVar

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)

_JSON_FENCE = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```", re.IGNORECASE)


def _extract_json_text(raw: str) -> str:
    raw = raw.strip()
    m = _JSON_FENCE.search(raw)
    if m:
        return m.group(1).strip()
    return raw


def _coerce_schema(raw: object, schema: type[T]) -> T:
    if isinstance(raw, schema):
        return raw
    if isinstance(raw, dict):
        return schema.model_validate(raw)
    if isinstance(raw, BaseModel):
        return schema.model_validate(raw.model_dump())
    raise TypeError(f"Unexpected structured output type: {type(raw)!r}")


def structured_invoke(
    chat: BaseChatModel,
    messages: list[BaseMessage],
    schema: type[T],
    *,
    max_retries: int = 3,
) -> T:
    """Try ``with_structured_output``; on failure use JSON-only prompt path."""
    last_err: Exception | None = None
    try:
        structured = chat.with_structured_output(schema)
        raw = structured.invoke(messages)
        return _coerce_schema(raw, schema)
    except Exception as e:  # noqa: BLE001 — gateway / provider varies
        last_err = e

    hint = (
        "Respond with ONLY a single JSON object matching this schema keys; "
        "no markdown, no prose."
    )
    tail = list(messages)
    tail.append(HumanMessage(content=hint + f" Schema: {schema.model_json_schema()}"))
    for _ in range(max_retries):
        try:
            msg: AIMessage = chat.invoke(tail)  # type: ignore[assignment]
            text = _extract_json_text(str(msg.content))
            data = json.loads(text)
            return schema.model_validate(data)
        except (json.JSONDecodeError, ValidationError, TypeError) as e:
            last_err = e
            tail = list(messages) + [
                SystemMessage(
                    content="Your previous reply was not valid JSON for the schema. "
                    "Output ONLY valid JSON."
                ),
                HumanMessage(content=f"Parse error: {e}. {hint}"),
            ]
    raise ValueError(f"structured_invoke failed after {max_retries} retries") from last_err
