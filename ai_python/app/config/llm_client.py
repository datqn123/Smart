from __future__ import annotations
import logging
import time
from typing import Protocol
from pydantic import BaseModel, ValidationError
from app.config.settings import Settings

log = logging.getLogger(__name__)


class ToolCallError(Exception):
    """Model khong tra tool_calls trong response."""


class StructuredOutputError(Exception):
    """Sau 2 attempt van khong co args hop le theo output_model."""


class LLMClient(Protocol):
    model: str
    temperature: float
    def complete(self, *, system: str, user: str, role: str = "default",
                 temperature: float | None = None) -> str: ...
    def complete_tool_select(self, *, system: str, user: str, tools: list[dict],
                             role: str = "default",
                             temperature: float | None = None) -> tuple[str, str]: ...
    def complete_structured(self, *, system: str, user: str,
                            output_model: type[BaseModel], role: str = "default",
                            temperature: float | None = None) -> BaseModel: ...


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

    def _tool_request(self, *, system: str, user: str, tools: list[dict],
                      tool_choice, role: str, temperature: float | None):
        temp = self.temperature if temperature is None else temperature
        log.debug("LLM tool-call role=%s model=%s tools=%d", role, self.model, len(tools))
        extra: dict = {}
        if self.max_tokens:
            extra["max_tokens"] = self.max_tokens
        if self.disable_thinking:
            extra["extra_body"] = {"chat_template_kwargs": {"enable_thinking": False}}
        t0 = time.perf_counter()
        resp = self._sdk.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
            tools=tools, tool_choice=tool_choice, temperature=temp, **extra)
        msg = resp.choices[0].message
        log.info("LLM tool-call done role=%s elapsed=%.2fs has_tool_calls=%s",
                 role, time.perf_counter() - t0, bool(msg.tool_calls))
        return msg

    def complete_tool_select(self, *, system: str, user: str, tools: list[dict],
                             role: str = "default",
                             temperature: float | None = None) -> tuple[str, str]:
        """1 call voi tool_choice='required'. Tra (tool_name, args_json_str).
        Khong co tool_calls -> ToolCallError (caller tu retry vi can args_model
        theo ten tool de validate)."""
        msg = self._tool_request(system=system, user=user, tools=tools,
                                 tool_choice="required", role=role,
                                 temperature=temperature)
        if not msg.tool_calls:
            raise ToolCallError("model khong goi tool nao (tool_calls rong)")
        fn = msg.tool_calls[0].function
        log.debug("LLM tool-select -> %s args=%.300s", fn.name, fn.arguments)
        return fn.name, fn.arguments

    def complete_structured(self, *, system: str, user: str,
                            output_model: type[BaseModel], role: str = "default",
                            temperature: float | None = None) -> BaseModel:
        """Forced-function extraction: ep model dien dung schema output_model.
        Retry 1 lan; het -> StructuredOutputError."""
        tools = [{"type": "function", "function": {
            "name": "respond",
            "description": (output_model.__doc__ or "").strip(),
            "parameters": output_model.model_json_schema()}}]
        choice = {"type": "function", "function": {"name": "respond"}}
        u = user
        last_err: Exception | None = None
        for attempt in range(2):
            try:
                msg = self._tool_request(system=system, user=u, tools=tools,
                                         tool_choice=choice, role=role,
                                         temperature=temperature)
                if not msg.tool_calls:
                    raise ToolCallError("khong co tool_calls")
                return output_model.model_validate_json(
                    msg.tool_calls[0].function.arguments)
            except (ToolCallError, ValidationError, ValueError) as exc:
                last_err = exc
                log.warning("structured attempt=%d model=%s err=%s",
                            attempt + 1, output_model.__name__, exc)
                u = user + f"\n\n[Loi attempt truoc: {exc}. Dien dung schema.]"
        raise StructuredOutputError(str(last_err))


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
