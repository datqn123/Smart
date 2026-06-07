from __future__ import annotations

import pytest
from langchain_core.messages import AIMessage
from pydantic import BaseModel


def test_harness_max_steps_override(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.config.graph_settings import load_graph_settings

    monkeypatch.setenv("HARNESS_MAX_STEPS", "2")

    assert load_graph_settings().harness_max_steps == 2


def test_harness_loop_intents_accept_json_env(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.config.graph_settings import load_graph_settings

    monkeypatch.setenv("HARNESS_LOOP_INTENTS", '["data_query", "catalog_draft"]')

    assert load_graph_settings().harness_loop_intents == ["data_query", "catalog_draft"]


@pytest.mark.asyncio
async def test_build_async_checkpointer_returns_saver_instance() -> None:
    from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

    from app.config.graph_settings import GraphSettings
    from app.graph.checkpointing import build_async_checkpointer

    saver = await build_async_checkpointer(GraphSettings(checkpoint_sqlite_path=":memory:"))

    assert isinstance(saver, AsyncSqliteSaver)


@pytest.mark.asyncio
async def test_astructured_predict_parses_decision_schema() -> None:
    from app.harness.tool_registry import DecisionSchema
    from app.llm.openai_compatible import OpenAICompatibleChatClient

    class Chat:
        async def ainvoke(self, messages):  # noqa: ANN001
            return AIMessage(content='{"action": "final_answer", "final_answer": "xong"}')

    client = OpenAICompatibleChatClient(Chat())  # type: ignore[arg-type]

    result = await client.astructured_predict([], DecisionSchema)

    assert result.action == "final_answer"
    assert result.final_answer == "xong"


def test_protocol_exposes_async_methods() -> None:
    from app.llm.protocol import LlmClient

    assert "astructured_predict" in LlmClient.__dict__
