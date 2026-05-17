"""Agent markdown playbooks load and cover all wired nodes."""

from __future__ import annotations

import pytest

from app.prompts.load import list_agent_prompt_ids, load_agent_json_contract, load_agent_prompt

_EXPECTED_IDS = frozenset(
    {
        "intent",
        "chat_normal",
        "summarize",
        "idea",
        "gen_sql",
        "sql_review",
        "schema_explore",
        "sql_table_pick",
        "chart_readiness",
        "chart",
        "chart_review",
        "catalog_entity_pick",
        "catalog_draft",
    }
)


def test_all_agent_prompt_files_exist() -> None:
    found = set(list_agent_prompt_ids())
    assert _EXPECTED_IDS <= found


@pytest.mark.parametrize("agent_id", sorted(_EXPECTED_IDS))
def test_load_agent_prompt_non_empty(agent_id: str) -> None:
    text = load_agent_prompt(agent_id)
    assert len(text) > 40


@pytest.mark.parametrize("agent_id", sorted(_EXPECTED_IDS - {"chat_normal", "summarize", "gen_sql"}))
def test_load_agent_json_contract_non_empty(agent_id: str) -> None:
    contract = load_agent_json_contract(agent_id)
    assert contract
    assert "JSON" in contract or "json" in contract.lower()


def test_gen_sql_mentions_with_cte() -> None:
    body = load_agent_prompt("gen_sql")
    assert "WITH" in body or "generate_series" in body
