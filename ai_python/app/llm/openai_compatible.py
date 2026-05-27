"""OpenAI-compatible chat client — LangChain ChatOpenAI behind LlmClient port."""

from __future__ import annotations

import logging
from collections.abc import Iterator, Sequence
from typing import TypeVar

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from app.config.settings import LlmSettings
from app.llm.structured import structured_invoke

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class OpenAICompatibleChatClient:
    """Wraps ``ChatOpenAI``; sole place that instantiates the LangChain model."""

    def __init__(self, chat: ChatOpenAI) -> None:
        self._chat = chat

    def invoke_text(self, user: str, *, system: str | None = None) -> str:
        messages: list[BaseMessage] = []
        if system:
            messages.append(SystemMessage(content=system))
        messages.append(HumanMessage(content=user))
        out: AIMessage = self._chat.invoke(messages)  # type: ignore[assignment]
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

    def structured_predict(
        self,
        messages: Sequence[BaseMessage],
        schema: type[T],
        *,
        max_retries: int = 3,
        json_output_contract: str | None = None,
    ) -> T:
        return structured_invoke(
            self._chat,
            list(messages),
            schema,
            max_retries=max_retries,
            json_output_contract=json_output_contract,
        )


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
