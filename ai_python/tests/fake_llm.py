"""Fake LlmClient for offline tests."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from typing import TypeVar

from langchain_core.messages import BaseMessage
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class FakeLlmClient:
    """Deterministic stub implementing :class:`app.llm.protocol.LlmClient`."""

    def __init__(
        self,
        *,
        reply: str = "ok",
        stream_parts: list[str] | None = None,
        intent: str | None = None,
        sql_review_failures: int = 0,
    ) -> None:
        self._reply = reply
        self._stream_parts = stream_parts or ["hel", "lo"]
        self._intent = intent
        self._sql_review_fail_left = sql_review_failures
        self.invoke_count = 0

    def invoke_text(self, user: str, *, system: str | None = None) -> str:
        self.invoke_count += 1
        return self._reply

    def stream_text(self, user: str, *, system: str | None = None) -> Iterator[str]:
        yield from self._stream_parts

    def structured_predict(
        self,
        messages: Sequence[BaseMessage],
        schema: type[T],
        *,
        max_retries: int = 3,
    ) -> T:
        if schema.__name__ == "IntentOutput":
            intent_val = self._intent if self._intent is not None else "general_chat"
            return schema.model_validate({"intent": intent_val})  # type: ignore[return-value]
        if schema.__name__ == "SqlReviewOutput":
            if self._sql_review_fail_left > 0:
                self._sql_review_fail_left -= 1
                return schema.model_validate({"ok": False, "issues": ["forced fail"]})  # type: ignore[return-value]
            return schema.model_validate({"ok": True, "issues": []})  # type: ignore[return-value]
        raise NotImplementedError(schema)
