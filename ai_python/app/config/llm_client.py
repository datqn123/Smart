from __future__ import annotations
import logging
import time
from typing import Protocol
from app.config.settings import Settings

log = logging.getLogger(__name__)


class LLMClient(Protocol):
    model: str
    temperature: float
    def complete(self, *, system: str, user: str, role: str = "default",
                 temperature: float | None = None) -> str: ...


class OpenAILLMClient:
    """Thin wrapper quanh openai SDK tro FPT Cloud (OpenAI-compatible)."""

    def __init__(self, *, sdk, model: str, temperature: float,
                 max_tokens: int | None = None, disable_thinking: bool = False):
        self._sdk = sdk
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.disable_thinking = disable_thinking

    def complete(self, *, system: str, user: str, role: str = "default",
                 temperature: float | None = None) -> str:
        temp = self.temperature if temperature is None else temperature
        log.debug("LLM call role=%s model=%s temperature=%s prompt_chars=%d",
                  role, self.model, temp, len(system) + len(user))
        extra: dict = {}
        if self.max_tokens:
            extra["max_tokens"] = self.max_tokens
        if self.disable_thinking:
            # Qwen3: thinking mode mac dinh ON, sinh <think> dai -> rat cham.
            extra["extra_body"] = {"chat_template_kwargs": {"enable_thinking": False}}
        t0 = time.perf_counter()
        resp = self._sdk.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
            temperature=temp,
            **extra,
        )
        elapsed = time.perf_counter() - t0
        content = resp.choices[0].message.content or ""
        if "</think>" in content:                       # phong ho server van bat thinking
            content = content.split("</think>", 1)[1].strip()
        log.info("LLM done role=%s elapsed=%.2fs response_chars=%d",
                 role, elapsed, len(content))
        log.debug("LLM response preview: %s", content[:300])
        return content


def _build_sdk(settings: Settings):
    from openai import OpenAI
    return OpenAI(base_url=settings.llm_base_url, api_key=settings.llm_api_key,
                  timeout=settings.llm_http_request_timeout)


def make_llm(settings: Settings, role: str = "default") -> OpenAILLMClient:
    """Tra LLM client. Moi tool chung 1 model (Qwen); role='sm' chi doi
    temperature (deterministic) — KHONG doi model (R5)."""
    temperature = settings.llm_sm_temperature if role == "sm" else settings.llm_temperature
    return OpenAILLMClient(sdk=_build_sdk(settings), model=settings.llm_model,
                           temperature=temperature,
                           max_tokens=settings.llm_max_tokens,
                           disable_thinking=settings.llm_disable_thinking)
