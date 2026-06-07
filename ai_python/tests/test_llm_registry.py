"""Tests for LLM settings and registry (no network)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.config.settings import load_llm_settings, validate_llm_required
from app.llm.registry import LlmRegistry, build_llm_registry
from app.llm.streaming import join_stream
from tests.fake_llm import FakeLlmClient


def test_validate_llm_required_missing_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_API_KEY", "")
    monkeypatch.setenv("LLM_REQUIRED", "1")
    monkeypatch.setenv("LLM_BASE_URL", "https://example.com")
    monkeypatch.setenv("LLM_MODEL", "m")
    s = load_llm_settings()
    with pytest.raises(ValueError, match="LLM_API_KEY"):
        validate_llm_required(s)


def test_build_llm_registry_requires_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_REQUIRED", "0")
    monkeypatch.setenv("LLM_API_KEY", "")
    s = load_llm_settings()
    with pytest.raises(ValueError, match="LLM_API_KEY"):
        build_llm_registry(s)


@patch("app.llm.registry.build_chat_openai")
def test_build_llm_registry_dual_model_invokes_factory_twice(
    mock_build: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LLM_REQUIRED", "0")
    monkeypatch.setenv("LLM_API_KEY", "secret")
    monkeypatch.setenv("LLM_BASE_URL", "https://example.com")
    monkeypatch.setenv("LLM_MODEL", "primary-m")
    monkeypatch.setenv("LLM_STRUCTURED_MODEL", "structured-m")
    mock_build.return_value = MagicMock()
    s = load_llm_settings()
    reg = build_llm_registry(s)
    assert mock_build.call_count == 2
    models = [call.kwargs["settings"].model for call in mock_build.call_args_list]
    assert models == ["primary-m", "structured-m"]
    assert reg.get("chat") is not reg.get("intent")
    assert reg.get("sql_gen") is reg.get("intent")


@patch("app.llm.registry.build_chat_openai")
def test_build_llm_registry_single_model_one_factory_call(
    mock_build: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LLM_REQUIRED", "0")
    monkeypatch.setenv("LLM_API_KEY", "secret")
    monkeypatch.setenv("LLM_BASE_URL", "https://example.com")
    monkeypatch.setenv("LLM_MODEL", "only-m")
    monkeypatch.setenv("LLM_STRUCTURED_MODEL", "")
    mock_build.return_value = MagicMock()
    s = load_llm_settings()
    reg = build_llm_registry(s)
    assert mock_build.call_count == 1
    assert reg.get("chat") is reg.get("intent")
    assert reg.get("sql_gen") is reg.get("chat")


@patch("app.llm.registry.build_chat_openai")
def test_tiers_alias_structured_when_unset(
    mock_build: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No tier model configured → haiku/sonnet/opus alias the structured client."""
    monkeypatch.setenv("LLM_REQUIRED", "0")
    monkeypatch.setenv("LLM_API_KEY", "secret")
    monkeypatch.setenv("LLM_BASE_URL", "https://example.com")
    monkeypatch.setenv("LLM_MODEL", "primary-m")
    monkeypatch.setenv("LLM_STRUCTURED_MODEL", "structured-m")
    for tier in ("HAIKU", "SONNET", "OPUS"):
        monkeypatch.delenv(f"LLM_TIER_{tier}_MODEL", raising=False)
    mock_build.return_value = MagicMock()
    reg = build_llm_registry(load_llm_settings())
    # Only primary + structured were built; tiers reuse the structured client object.
    assert mock_build.call_count == 2
    assert reg.get("sonnet") is reg.get("intent")
    assert reg.get("haiku") is reg.get("intent")
    assert reg.get("opus") is reg.get("intent")


@patch("app.llm.registry.build_chat_openai")
def test_tier_opus_uses_its_own_model(
    mock_build: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A configured tier model builds a dedicated client distinct from structured."""
    monkeypatch.setenv("LLM_REQUIRED", "0")
    monkeypatch.setenv("LLM_API_KEY", "secret")
    monkeypatch.setenv("LLM_BASE_URL", "https://example.com")
    monkeypatch.setenv("LLM_MODEL", "primary-m")
    monkeypatch.setenv("LLM_STRUCTURED_MODEL", "structured-m")
    monkeypatch.setenv("LLM_TIER_OPUS_MODEL", "opus-m")
    mock_build.side_effect = lambda **kwargs: MagicMock(name=kwargs["settings"].model)
    reg = build_llm_registry(load_llm_settings())
    models = [call.kwargs["settings"].model for call in mock_build.call_args_list]
    assert "opus-m" in models  # dedicated opus client built
    assert reg.get("opus") is not reg.get("sonnet")  # opus distinct from aliased structured


def test_registry_unknown_role_falls_back_to_default() -> None:
    reg = LlmRegistry()
    fake = FakeLlmClient(reply="x", stream_parts=["a", "b"])
    reg.register("default", fake)
    assert reg.get("unknown-role").invoke_text("u") == "x"


def test_join_stream_fake() -> None:
    client = FakeLlmClient(stream_parts=["a", "", "b"])
    assert join_stream(client, "hi") == "ab"


def test_structured_fake_intent() -> None:
    from app.llm.schemas import IntentOutput

    client = FakeLlmClient()
    from langchain_core.messages import HumanMessage

    out = client.structured_predict([HumanMessage(content="x")], IntentOutput)
    assert out.intent == "general_chat"
