"""OpenAI-compatible chat client — LangChain ChatOpenAI behind LlmClient port."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator, Iterator, Sequence
from dataclasses import dataclass
from typing import Any, TypeVar

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from app.config.settings import LlmSettings
from app.llm.structured import astructured_invoke, structured_invoke

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


def extract_usage(message: Any) -> "InvokeUsage":
    """Extract token usage from a LangChain AIMessage response.

    Supports three provider metadata shapes:
    - ``usage_metadata = {"input_tokens": N, "output_tokens": N}``
    - ``response_metadata = {"token_usage": {"prompt_tokens": N, "completion_tokens": N}}``
    - ``response_metadata = {"usage": {"prompt_tokens": N, "completion_tokens": N}}``
    """
    if message is None:
        logger.debug("usage_unavailable: message is None")
        return InvokeUsage()
    um = getattr(message, "usage_metadata", None)
    if isinstance(um, dict) and (um.get("input_tokens") or um.get("output_tokens")):
        return InvokeUsage(
            prompt_tokens=int(um.get("input_tokens", 0) or 0),
            completion_tokens=int(um.get("output_tokens", 0) or 0),
        )
    rm = getattr(message, "response_metadata", None) or {}
    if isinstance(rm, dict):
        for key in ("token_usage", "usage"):
            tu = rm.get(key)
            if isinstance(tu, dict) and (tu.get("prompt_tokens") or tu.get("completion_tokens")):
                return InvokeUsage(
                    prompt_tokens=int(tu.get("prompt_tokens", 0) or 0),
                    completion_tokens=int(tu.get("completion_tokens", 0) or 0),
                )
    logger.debug("usage_unavailable: no token metadata on LLM response")
    return InvokeUsage()


@dataclass(frozen=True)
class InvokeUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0

    @property
    def total_tokens(self) -> int:
        return int(self.prompt_tokens or 0) + int(self.completion_tokens or 0)


class OpenAICompatibleChatClient:
    """Wraps ``ChatOpenAI``; sole place that instantiates the LangChain model."""

    def __init__(self, chat: ChatOpenAI) -> None:
        self._chat = chat
        self.last_usage = InvokeUsage()

    def invoke_text(self, user: str, *, system: str | None = None) -> str:
        messages: list[BaseMessage] = []
        if system:
            messages.append(SystemMessage(content=system))
        messages.append(HumanMessage(content=user))
        out: AIMessage = self._chat.invoke(messages)  # type: ignore[assignment]
        self.last_usage = extract_usage(out)
        return str(out.content)

    def stream_text(self, user: str, *, system: str | None = None) -> Iterator[str]:
        messages: list[BaseMessage] = []
        if system:
            messages.append(SystemMessage(content=system))
        messages.append(HumanMessage(content=user))
        for chunk in self._chat.stream(messages):
            # Prefer LangChain's normalized text accessor to preserve streaming text shape.
            # `content` may be structured blocks in newer providers/APIs.
            text = getattr(chunk, "text", None)
            if isinstance(text, str) and text:
                yield text
                continue
            raw = getattr(chunk, "content", None)
            if isinstance(raw, str) and raw:
                yield raw

    async def ainvoke_text(self, user: str, *, system: str | None = None) -> str:
        messages: list[BaseMessage] = []
        if system:
            messages.append(SystemMessage(content=system))
        messages.append(HumanMessage(content=user))
        out: AIMessage = await self._chat.ainvoke(messages)  # type: ignore[assignment]
        self.last_usage = extract_usage(out)
        return str(out.content)

    async def astream_text(self, user: str, *, system: str | None = None) -> AsyncIterator[str]:
        messages: list[BaseMessage] = []
        if system:
            messages.append(SystemMessage(content=system))
        messages.append(HumanMessage(content=user))
        async for chunk in self._chat.astream(messages):
            text = getattr(chunk, "text", None)
            if isinstance(text, str) and text:
                yield text
                continue
            raw = getattr(chunk, "content", None)
            if isinstance(raw, str) and raw:
                yield raw

    def structured_predict(
        self,
        messages: Sequence[BaseMessage],
        schema: type[T],
        *,
        max_retries: int = 3,
        json_output_contract: str | None = None,
    ) -> T:
        _sink: list[Any] = []
        result = structured_invoke(
            self._chat,
            list(messages),
            schema,
            max_retries=max_retries,
            json_output_contract=json_output_contract,
            _last_msg_out=_sink,
        )
        if _sink:
            self.last_usage = extract_usage(_sink[0])
        return result

    async def astructured_predict(
        self,
        messages: Sequence[BaseMessage],
        schema: type[T],
        *,
        max_retries: int = 3,
        json_output_contract: str | None = None,
    ) -> T:
        _sink: list[Any] = []
        result = await astructured_invoke(
            self._chat,
            list(messages),
            schema,
            max_retries=max_retries,
            json_output_contract=json_output_contract,
            _last_msg_out=_sink,
        )
        if _sink:
            self.last_usage = extract_usage(_sink[0])
        return result


def build_chat_openai(*, settings: LlmSettings) -> ChatOpenAI:
    """Build ``ChatOpenAI`` from :class:`app.config.settings.LlmSettings`."""
    if not isinstance(settings, LlmSettings):
        raise TypeError("settings must be LlmSettings")
    s = settings
    key = s.api_key.get_secret_value() if s.api_key else None
    kwargs: dict = {
        "base_url": s.base_url or None,
        "api_key": key,
        "model": s.model or None,
        "temperature": s.temperature,
    }
    if s.max_tokens is not None:
        kwargs["max_tokens"] = s.max_tokens
    if s.top_p is not None:
        kwargs["top_p"] = s.top_p
    if s.send_top_k and s.top_k is not None:
        kwargs["model_kwargs"] = {"top_k": s.top_k}
    kwargs["timeout"] = float(s.http_request_timeout)
    chat = ChatOpenAI(**kwargs)
    logger.debug("ChatOpenAI built for model=%s", s.model)
    return chat
