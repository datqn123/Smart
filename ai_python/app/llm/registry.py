"""Role → LlmClient registry (Option B)."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from app.config.settings import LlmSettings, validate_llm_required
from app.llm.openai_compatible import OpenAICompatibleChatClient, build_chat_openai
from app.llm.protocol import LlmClient

logger = logging.getLogger(__name__)

_TEXT_ROLES = ("chat", "summarize")
_STRUCTURED_ROLES = (
    "intent",
    "sql_review",
    "sql_table_pick",
    "schema_plan",
    "idea",
    "chart",
    "chart_critic",
    "review",
)


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
    """Build registry: primary for chat/summarize; optional second client for sql_gen + structured JSON."""
    validate_llm_required(settings)
    if not settings.api_key or not settings.api_key.get_secret_value().strip():
        raise ValueError("LLM_API_KEY is required to build the LLM registry.")
    if not settings.base_url or not settings.model:
        raise ValueError("LLM_BASE_URL and LLM_MODEL are required to build the LLM registry.")

    primary_chat = build_chat_openai(settings=settings)
    primary: LlmClient = OpenAICompatibleChatClient(primary_chat)

    fork = settings.fork_for_structured_chat()
    if fork is None:
        structured: LlmClient = primary
        logger.info(
            "LLM registry: single model %r for all roles.",
            settings.model,
        )
    else:
        structured_chat = build_chat_openai(settings=fork)
        structured = OpenAICompatibleChatClient(structured_chat)
        logger.info(
            "LLM registry: primary model=%r (chat, summarize); "
            "structured model=%r (sql_gen, intent, sql_review, sql_table_pick, schema_plan, idea, chart, chart_critic, review).",
            settings.model,
            fork.model,
        )

    reg = LlmRegistry()
    reg.register("default", primary)
    for role in _TEXT_ROLES:
        reg.register(role, primary)
    sql_gen_client = structured if fork is not None else primary
    reg.register("sql_gen", sql_gen_client)
    for role in _STRUCTURED_ROLES:
        reg.register(role, structured)
    return reg
