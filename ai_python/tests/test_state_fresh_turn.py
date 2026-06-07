from __future__ import annotations

from langchain_core.messages import HumanMessage


def test_fresh_turn_overlay_covers_all_transient_keys() -> None:
    from app.graph.state import _TRANSIENT_KEYS, fresh_turn_overlay

    overlay = fresh_turn_overlay()

    assert set(overlay.keys()) == _TRANSIENT_KEYS
    assert all(value is None for value in overlay.values())


def test_fresh_turn_overlay_does_not_contain_persistent_keys() -> None:
    from app.graph.state import fresh_turn_overlay

    persistent = {
        "messages",
        "conversation_summary",
        "context_compact_generation",
        "business_scope",
        "last_business_scope",
        "last_data_answer",
    }

    assert not (persistent & set(fresh_turn_overlay()))


def test_fresh_turn_does_not_bleed_sql_chart_or_draft_state() -> None:
    from app.graph.state import fresh_turn_overlay

    state = {
        "generated_sql": "SELECT 1",
        "query_result": {"rows": [1]},
        "chart_spec_final": {"type": "bar"},
        "catalog_draft_sse": {"entity": "product"},
        "inventory_draft_sse": {"entity": "inventory"},
    }
    state.update(fresh_turn_overlay())

    assert state["generated_sql"] is None
    assert state["query_result"] is None
    assert state["chart_spec_final"] is None
    assert state["catalog_draft_sse"] is None
    assert state["inventory_draft_sse"] is None


def test_fresh_turn_preserves_messages() -> None:
    from app.graph.state import fresh_turn_overlay

    messages = [HumanMessage(content="hi")]
    state = {"messages": messages, "conversation_summary": "prev"}
    state.update(fresh_turn_overlay())

    assert state["messages"] == messages
    assert state["conversation_summary"] == "prev"
