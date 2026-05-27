"""Task111 — interaction mode → intent override."""

from __future__ import annotations

from langchain_core.messages import HumanMessage

from app.config.graph_settings import GraphSettings
from app.graph.deps import GraphDeps
from app.graph.interaction_mode import (
    normalize_interaction_mode,
    resolve_mode_override,
    should_route_query_table,
)
from app.graph.nodes.intent import make_intent_node
from app.graph.sql_executor import StubSqlExecutor
from app.llm.registry import LlmRegistry
from tests.fake_llm import FakeLlmClient


def test_normalize_interaction_mode_defaults_to_auto() -> None:
    assert normalize_interaction_mode(None) == "auto"
    assert normalize_interaction_mode("invalid") == "auto"
    assert normalize_interaction_mode("data_table") == "data_table"


def test_resolve_mode_override_auto_returns_none() -> None:
    assert resolve_mode_override("auto") is None
    assert resolve_mode_override(None) is None


def test_resolve_mode_override_maps_intents() -> None:
    assert resolve_mode_override("data_query") == {
        "intent": "system_data_query",
        "show_query_table": False,
    }
    assert resolve_mode_override("data_table") == {
        "intent": "system_data_query",
        "show_query_table": True,
    }
    assert resolve_mode_override("chart") == {
        "intent": "system_data_chart",
        "show_query_table": False,
    }
    assert resolve_mode_override("catalog_draft") == {
        "intent": "catalog_data_entry",
        "show_query_table": False,
    }
    assert resolve_mode_override("inventory_draft") == {
        "intent": "inventory_data_entry",
        "show_query_table": False,
    }


def test_should_route_query_table() -> None:
    assert should_route_query_table({"interaction_mode": "data_table"}) is True
    assert should_route_query_table({"show_query_table": True}) is True
    assert should_route_query_table({"interaction_mode": "data_query"}) is False


class _IntentProbe(FakeLlmClient):
    def __init__(self) -> None:
        super().__init__(intent="general_chat")
        self.structured_calls = 0

    def structured_predict(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        self.structured_calls += 1
        return super().structured_predict(*args, **kwargs)


def _deps_with_intent_probe(probe: _IntentProbe) -> GraphDeps:
    reg = LlmRegistry()
    reg.register("default", probe)
    reg.register("intent", probe)
    return GraphDeps(
        llm_registry=reg,
        sql_executor=StubSqlExecutor(),
        settings=GraphSettings(),
    )


def test_mode_override_hard_bypass_skips_intent_llm() -> None:
    probe = _IntentProbe()
    node = make_intent_node(_deps_with_intent_probe(probe))
    out = node(
        {
            "messages": [HumanMessage(content="vẽ biểu đồ doanh thu")],
            "interaction_mode": "chart",
        }
    )
    assert out["intent"] == "system_data_chart"
    assert out["route_source"] == "interaction_mode"
    assert probe.structured_calls == 0


def test_auto_mode_uses_intent_llm_json_contract() -> None:
    probe = _IntentProbe()
    node = make_intent_node(_deps_with_intent_probe(probe))
    out = node(
        {
            "messages": [HumanMessage(content="xin chào")],
            "interaction_mode": "auto",
        }
    )
    assert out["intent"] == "general_chat"
    assert out["route_source"] == "intent_auto"
    assert probe.structured_calls == 1
