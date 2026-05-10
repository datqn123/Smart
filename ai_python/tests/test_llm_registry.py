"""Tests for LLM settings and registry (no network)."""

from __future__ import annotations

import pytest

from app.config.settings import load_llm_settings, validate_llm_required
from app.llm.registry import LlmRegistry, build_llm_registry
from app.llm.streaming import join_stream
from tests.fake_llm import FakeLlmClient


def test_validate_llm_required_missing_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.setenv("LLM_REQUIRED", "1")
    monkeypatch.setenv("LLM_BASE_URL", "https://example.com")
    monkeypatch.setenv("LLM_MODEL", "m")
    s = load_llm_settings()
    with pytest.raises(ValueError, match="LLM_API_KEY"):
        validate_llm_required(s)


def test_build_llm_registry_requires_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_REQUIRED", "0")
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    s = load_llm_settings()
    with pytest.raises(ValueError, match="LLM_API_KEY"):
        build_llm_registry(s)


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
