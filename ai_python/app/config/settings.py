"""Pydantic settings for LLM (OpenAI-compatible / Gemma)."""

from __future__ import annotations

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LlmSettings(BaseSettings):
    """Load from env with prefix ``LLM_`` (see ``.env.example``)."""

    model_config = SettingsConfigDict(
        env_prefix="LLM_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    base_url: str = Field(
        default="",
        description="OpenAI-compatible base URL (no trailing / required).",
    )
    api_key: SecretStr | None = Field(default=None)
    model: str = Field(default="", description="Model id, e.g. gemma-4-31B-it.")
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, ge=1)
    top_p: float | None = Field(default=None, gt=0.0, le=1.0)
    top_k: int | None = Field(default=None, ge=1)
    streaming_default: bool = Field(default=False)
    send_top_k: bool = Field(
        default=False,
        description="If true, pass top_k to provider when set (gateway may 400 if unsupported).",
    )
    required: bool = Field(
        default=False,
        description="If true, missing api_key/base_url/model fails at registry build.",
    )
    http_request_timeout: float = Field(
        default=120.0,
        ge=5.0,
        le=600.0,
        description="HTTP timeout (s) for each LLM request (ChatOpenAI / OpenAI-compatible).",
    )

    @field_validator("base_url", "model", mode="before")
    @classmethod
    def strip_str(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip()
        return v


def load_llm_settings() -> LlmSettings:
    return LlmSettings()


def validate_llm_required(settings: LlmSettings) -> None:
    """Fail fast when LLM_REQUIRED and credentials missing."""
    if not settings.required:
        return
    if not settings.api_key or not settings.api_key.get_secret_value().strip():
        raise ValueError("LLM_REQUIRED is enabled but LLM_API_KEY is missing or empty.")
    if not settings.base_url:
        raise ValueError("LLM_REQUIRED is enabled but LLM_BASE_URL is missing or empty.")
    if not settings.model:
        raise ValueError("LLM_REQUIRED is enabled but LLM_MODEL is missing or empty.")
