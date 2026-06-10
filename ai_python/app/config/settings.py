"""Pydantic settings for LLM (OpenAI-compatible / Gemma)."""

from __future__ import annotations

from dataclasses import dataclass

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
    structured_model: str = Field(
        default="",
        description=(
            "Optional second model for sql_gen plus structured JSON roles "
            "(intent, idea, chart, review). "
            "Empty = use LLM_MODEL for all roles."
        ),
    )
    structured_base_url: str = Field(
        default="",
        description="OpenAI-compatible base URL for structured model; empty inherits LLM_BASE_URL.",
    )
    structured_api_key: SecretStr | None = Field(
        default=None,
        description="API key for structured model; unset inherits LLM_API_KEY.",
    )
    structured_temperature: float | None = Field(
        default=None,
        description="Temperature for structured model; unset inherits LLM_TEMPERATURE.",
    )
    # --- Tiered model routing (P7). Each tier optionally maps to its own model id on
    #     the same gateway. Empty = alias to the existing structured client (no-op),
    #     so enabling AGENTIC_MODEL_ROUTING with no tier set keeps current behaviour. ---
    tier_haiku_model: str = Field(
        default="",
        description="LLM_TIER_HAIKU_MODEL — cheap/fast model for intent & compact.",
    )
    tier_sonnet_model: str = Field(
        default="",
        description="LLM_TIER_SONNET_MODEL — balanced model for planner/sql/compose.",
    )
    tier_opus_model: str = Field(
        default="",
        description="LLM_TIER_OPUS_MODEL — strong model used on replan escalation.",
    )

    @field_validator(
        "base_url",
        "model",
        "structured_base_url",
        "structured_model",
        "tier_haiku_model",
        "tier_sonnet_model",
        "tier_opus_model",
        mode="before",
    )
    @classmethod
    def strip_str(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator("structured_temperature", mode="after")
    @classmethod
    def clamp_structured_temperature(cls, v: float | None) -> float | None:
        if v is None:
            return None
        return max(0.0, min(2.0, v))

    def fork_for_model(self, name: str) -> LlmSettings | None:
        """Return settings for a tier model on the same gateway, or ``None`` if unset.

        Inherits primary base_url / api_key / temperature; only the model id changes.
        """
        clean = (name or "").strip()
        if not clean:
            return None
        return self.model_copy(update={"model": clean})

    def fork_for_structured_chat(self) -> LlmSettings | None:
        """Return settings for the structured-output LLM, or ``None`` to use primary only."""
        name = self.structured_model.strip()
        if not name:
            return None
        sk = self.structured_api_key
        use_key = sk if (sk and sk.get_secret_value().strip()) else self.api_key
        url = self.structured_base_url.strip() or self.base_url
        temp = self.temperature if self.structured_temperature is None else self.structured_temperature
        return self.model_copy(
            update={
                "model": name,
                "base_url": url,
                "api_key": use_key,
                "temperature": temp,
            }
        )


def load_llm_settings() -> LlmSettings:
    return LlmSettings()


class SttSettings(BaseSettings):
    """Speech-to-text (FPT Whisper) — env prefix ``STT_``.

    Gateway credentials always come from ``LLM_BASE_URL`` and ``LLM_API_KEY`` (same as Gemma/chat).
    """

    model_config = SettingsConfigDict(
        env_prefix="STT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    enabled: bool = Field(
        default=True,
        description="Set STT_ENABLED=0 to disable voice STT.",
    )
    model: str = Field(default="FPT.AI-whisper-medium")
    language: str = Field(default="vi")
    response_format: str = Field(default="json")
    max_audio_seconds: int = Field(default=60, ge=1, le=600)
    max_upload_bytes: int = Field(default=10_485_760, ge=1)
    http_timeout_seconds: float = Field(default=45.0, ge=5.0, le=300.0)

    @field_validator("model", "language", "response_format", mode="before")
    @classmethod
    def strip_stt_str(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip()
        return v


@dataclass(frozen=True)
class ResolvedSttCredentials:
    base_url: str
    api_key: str
    model: str
    language: str
    response_format: str
    http_timeout_seconds: float
    max_upload_bytes: int
    max_audio_seconds: int


def load_stt_settings() -> SttSettings:
    return SttSettings()


class TtsSettings(BaseSettings):
    """Text-to-speech (FPT VITs) — env prefix ``TTS_``.

    Gateway credentials use ``LLM_BASE_URL`` and ``LLM_API_KEY`` (same as chat/STT).
    """

    model_config = SettingsConfigDict(
        env_prefix="TTS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    enabled: bool = Field(
        default=True,
        description="Set TTS_ENABLED=0 to disable speech synthesis.",
    )
    model: str = Field(default="FPT.AI-VITs")
    voice: str = Field(default="std_kimngan")
    response_format: str = Field(default="wav")
    max_input_chars: int = Field(default=5000, ge=1, le=50_000)
    http_timeout_seconds: float = Field(default=60.0, ge=5.0, le=300.0)

    @field_validator("model", "voice", "response_format", mode="before")
    @classmethod
    def strip_tts_str(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip()
        return v


@dataclass(frozen=True)
class ResolvedTtsCredentials:
    base_url: str
    api_key: str
    model: str
    voice: str
    response_format: str
    http_timeout_seconds: float
    max_input_chars: int


def load_tts_settings() -> TtsSettings:
    return TtsSettings()


def resolve_tts_credentials(
    llm: LlmSettings,
    tts: TtsSettings,
) -> ResolvedTtsCredentials | None:
    if not tts.enabled:
        return None
    base_url = llm.base_url.strip()
    api_key = llm.api_key.get_secret_value().strip() if llm.api_key else ""
    if not base_url or not api_key:
        return None
    model = tts.model.strip() or "FPT.AI-VITs"
    voice = tts.voice.strip() or "std_kimngan"
    return ResolvedTtsCredentials(
        base_url=base_url.rstrip("/"),
        api_key=api_key,
        model=model,
        voice=voice,
        response_format=tts.response_format.strip() or "wav",
        http_timeout_seconds=tts.http_timeout_seconds,
        max_input_chars=tts.max_input_chars,
    )


def resolve_stt_credentials(
    llm: LlmSettings,
    stt: SttSettings,
) -> ResolvedSttCredentials | None:
    """Return resolved credentials when STT is enabled; gateway uses ``LLM_*`` like chat models."""
    if not stt.enabled:
        return None
    base_url = llm.base_url.strip()
    api_key = llm.api_key.get_secret_value().strip() if llm.api_key else ""
    if not base_url or not api_key:
        return None
    model = stt.model.strip() or "FPT.AI-whisper-medium"
    return ResolvedSttCredentials(
        base_url=base_url.rstrip("/"),
        api_key=api_key,
        model=model,
        language=stt.language.strip() or "vi",
        response_format=stt.response_format.strip() or "json",
        http_timeout_seconds=stt.http_timeout_seconds,
        max_upload_bytes=stt.max_upload_bytes,
        max_audio_seconds=stt.max_audio_seconds,
    )


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
