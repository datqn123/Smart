from __future__ import annotations
from typing import Protocol
from app.config.settings import Settings


class LLMClient(Protocol):
    model: str
    temperature: float
    def complete(self, *, system: str, user: str, role: str = "default",
                 temperature: float | None = None) -> str: ...


class OpenAILLMClient:
    """Thin wrapper quanh openai SDK tro FPT Cloud (OpenAI-compatible)."""

    def __init__(self, *, sdk, model: str, temperature: float):
        self._sdk = sdk
        self.model = model
        self.temperature = temperature

    def complete(self, *, system: str, user: str, role: str = "default",
                 temperature: float | None = None) -> str:
        resp = self._sdk.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
            temperature=self.temperature if temperature is None else temperature,
        )
        return resp.choices[0].message.content or ""


def _build_sdk(settings: Settings):
    from openai import OpenAI
    return OpenAI(base_url=settings.llm_base_url, api_key=settings.llm_api_key,
                  timeout=settings.llm_http_request_timeout)


def make_llm(settings: Settings, role: str = "default") -> OpenAILLMClient:
    """Tra LLM client. Moi tool chung 1 model (Qwen); role='sm' chi doi
    temperature (deterministic) — KHONG doi model (R5)."""
    temperature = settings.llm_sm_temperature if role == "sm" else settings.llm_temperature
    return OpenAILLMClient(sdk=_build_sdk(settings), model=settings.llm_model,
                           temperature=temperature)
