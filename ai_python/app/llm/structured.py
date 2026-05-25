"""Structured output via JSON-only prompts (OpenAI-compatible gateways).

We intentionally avoid ``ChatOpenAI.with_structured_output`` here: it attaches a
``parsed=…`` payload on ``AIMessage`` that LangGraph's JsonPlus checkpoint serde
cannot round-trip, which breaks streaming / checkpointing with Pydantic warnings
and runtime failures.
"""

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


def structured_invoke(
    chat: BaseChatModel,
    messages: list[BaseMessage],
    schema: type[T],
    *,
    max_retries: int = 3,
    json_output_contract: str | None = None,
) -> T:
    """Ask the model for **only** JSON matching ``schema``; parse + validate with retries.

    If ``json_output_contract`` is a non-empty string, it replaces the embedded
    ``model_json_schema()`` text in the final instruction (useful for small models).
    """
    hint = (
        "Respond with ONLY a single JSON object matching this schema keys; "
        "no markdown, no prose."
    )
    contract = (json_output_contract or "").strip()
    schema_instruction = contract if contract else f"Schema: {schema.model_json_schema()}"
    instruction = f"{hint} {schema_instruction}"

    # --- FIX: Merge instruction into last HumanMessage to avoid consecutive Human messages ---
    tail: list[BaseMessage] = list(messages)
    if tail and isinstance(tail[-1], HumanMessage):
        last_msg = tail[-1]
        new_content = f"{last_msg.content}\n\n{instruction}"
        tail[-1] = HumanMessage(
            content=new_content,
            additional_kwargs=last_msg.additional_kwargs,
            response_metadata=last_msg.response_metadata,
            id=last_msg.id,
        )
    else:
        tail.append(HumanMessage(content=instruction))
    # --- END FIX ---

    last_err: Exception | None = None
    for _ in range(max_retries):
        try:
            msg: AIMessage = chat.invoke(tail)  # type: ignore[assignment]
            text = _extract_json_text(str(msg.content))
            data = json.loads(text)
            return schema.model_validate(data)
        except (json.JSONDecodeError, ValidationError, TypeError) as e:
            last_err = e
            # Retry: SystemMessage for error hint, then re-merge instruction into last Human
            retry_tail: list[BaseMessage] = list(messages)
            err_prefix = f"Parse error: {e}. "
            if retry_tail and isinstance(retry_tail[-1], HumanMessage):
                last_msg = retry_tail[-1]
                retry_content = f"{last_msg.content}\n\n{err_prefix}{instruction}"
                retry_tail[-1] = HumanMessage(
                    content=retry_content,
                    additional_kwargs=last_msg.additional_kwargs,
                    response_metadata=last_msg.response_metadata,
                    id=last_msg.id,
                )
                retry_tail.insert(-1, SystemMessage(
                    content="Your previous reply was not valid JSON for the schema. "
                    "Output ONLY valid JSON."
                ))
            else:
                retry_tail.extend([
                    SystemMessage(
                        content="Your previous reply was not valid JSON for the schema. "
                        "Output ONLY valid JSON."
                    ),
                    HumanMessage(content=f"{err_prefix}{instruction}"),
                ])
            tail = retry_tail
    raise ValueError(f"structured_invoke failed after {max_retries} retries") from last_err
