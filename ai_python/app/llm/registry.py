"""Role → LlmClient registry (Option B)."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from app.config.settings import LlmSettings, validate_llm_required
from app.llm.openai_compatible import OpenAICompatibleChatClient, build_chat_openai
from app.llm.protocol import LlmClient

logger = logging.getLogger(__name__)


@dataclass
class LlmRegistry:
    """Maps logical roles (chat, sql_review, …) to an ``LlmClient``."""

    _clients: dict[str, LlmClient] = field(default_factory=dict)

    def register(self, role: str, client: LlmClient) -> None:
        self._clients[role] = client

    def get(self, role: str) -> LlmClient:
        if role in self._clients:
            return self._clients[role]
        if "default" in self._clients:
            logger.debug("Unknown LLM role %r — using 'default'.", role)
            return self._clients["default"]
        raise KeyError(f"No LlmClient for role {role!r} and no 'default'.")


def build_llm_registry(settings: LlmSettings) -> LlmRegistry:
    """Build registry with at least ``default`` when credentials are present."""
    validate_llm_required(settings)
    if not settings.api_key or not settings.api_key.get_secret_value().strip():
        raise ValueError("LLM_API_KEY is required to build the LLM registry.")
    if not settings.base_url or not settings.model:
        raise ValueError("LLM_BASE_URL and LLM_MODEL are required to build the LLM registry.")

    chat = build_chat_openai(settings=settings)
    client: LlmClient = OpenAICompatibleChatClient(chat)
    reg = LlmRegistry()
    reg.register("default", client)
    return reg
