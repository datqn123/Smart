from __future__ import annotations

import pytest


def test_required_data_item_schema() -> None:
    from app.harness.intent import RequiredDataItem

    item = RequiredDataItem(field="revenue", source="orders", required=True, resolved=False)

    assert item.field == "revenue"
    assert item.source == "orders"
    assert item.required is True
    assert item.resolved is False


def _settings(**overrides):  # noqa: ANN003
    from types import SimpleNamespace

    values = {
        "intent_confidence_run": 0.9,
        "intent_confidence_hitl": 0.75,
        "entity_score_hitl": 0.6,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_intent_high_confidence_runs() -> None:
    from app.harness.intent import IntentObject, IntentSubagent

    intent = IntentObject(
        goal="Xem doanh thu",
        intent_type="data_query",
        required_data=["revenue"],
        confidence=0.95,
        resolved_entities=[],
    )

    decision = IntentSubagent(settings=_settings()).decide(intent)

    assert decision.mode == "run"


def test_intent_missing_required_clarifies() -> None:
    from app.harness.intent import IntentObject, IntentSubagent

    intent = IntentObject(
        goal="Xem báo cáo",
        intent_type="data_query",
        required_data=["revenue"],
        confidence=0.95,
        missing_required=["time_period"],
    )

    decision = IntentSubagent(settings=_settings()).decide(intent)

    assert decision.mode == "clarify"
    assert decision.clarify_questions
    assert "thời gian" in decision.clarify_questions[0].lower()


def test_intent_mid_confidence_auto_assume() -> None:
    from app.harness.intent import IntentObject, IntentSubagent

    intent = IntentObject(
        goal="Xem tồn kho",
        intent_type="data_query",
        required_data=["inventory"],
        confidence=0.8,
    )

    decision = IntentSubagent(settings=_settings()).decide(intent)

    assert decision.mode == "auto_assume"
    assert decision.assumptions


def test_entity_resolver_fuzzy_fallback() -> None:
    from app.harness.intent import EntityResolver

    resolver = EntityResolver(
        synonym_map={"doanh thu": ["sales_revenue"]},
        catalog=[
            {"entity_type": "product", "display": "Coca-Cola lon 330ml"},
            {"entity_type": "product", "display": "Pepsi lon 330ml"},
        ],
    )

    resolved = resolver.score_sync("coca", "product")

    assert resolved.matched == "Coca-Cola lon 330ml"
    assert resolved.score > 0


@pytest.mark.asyncio
async def test_intent_subagent_llm_output() -> None:
    from app.harness.intent import IntentObjectOutput, IntentSubagent
    from tests.fake_llm import FakeLlmClient

    class Registry:
        def get(self, role: str):  # noqa: ANN001
            return FakeLlmClient(intent="data_query", intent_confidence=0.95)

    out = await IntentSubagent(llm_registry=Registry(), settings=_settings()).analyze(
        "doanh thu tháng này",
        memory_text="",
        dictionary_text="",
    )

    assert isinstance(out, IntentObjectOutput)
    assert out.intent_type == "data_query"
    assert out.confidence == 0.95


def test_intent_context_builder_assembles_blocks() -> None:
    from app.harness.intent import IntentContextBuilder

    builder = IntentContextBuilder()
    ctx = builder.build(
        schema_text="Table: orders(id, total, created_at)",
        history_text="Q: doanh thu tháng 3 → SELECT SUM(total) FROM orders WHERE month=3",
        memory_text="User asked about revenue",
    )

    assert "orders" in ctx.schema_text
    assert "SELECT" in ctx.history_text
    assert "revenue" in ctx.memory_text
    assert ctx.to_prompt_blocks()  # returns non-empty string
