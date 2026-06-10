"""Agent markdown playbooks load and cover all wired nodes."""

from __future__ import annotations

import pytest

from app.prompts.load import (
    catalog_draft_entity_prompt_id,
    list_agent_prompt_ids,
    load_agent_json_contract,
    load_agent_prompt,
    load_catalog_draft_system_prompt,
    load_inventory_draft_system_prompt,
)

_EXPECTED_IDS = frozenset(
    {
        "intent",
        "planner",
        "chat_normal",
        "summarize",
        "idea",
        "gen_sql",
        "chart_readiness",
        "chart",
        "chart_review",
        "catalog_entity_pick",
        "catalog_draft",
        "catalog_draft_product",
        "catalog_draft_category",
        "catalog_draft_supplier",
        "catalog_draft_customer",
        "inventory_entity_pick",
        "inventory_draft_slots",
        "catalog_draft_slots",
        "inventory_draft",
        "inventory_draft_stock_receipt",
        "context_compact",
        "domain_guard",
    }
)

# Entity playbooks: contract lives in catalog_draft.md only (merged at runtime).
_CATALOG_DRAFT_ENTITY_PLAYBOOKS = frozenset(
    {
        "catalog_draft_product",
        "catalog_draft_category",
        "catalog_draft_supplier",
        "catalog_draft_customer",
    }
)

_INVENTORY_DRAFT_PLAYBOOKS = frozenset({"inventory_draft_stock_receipt"})

_LEGACY_AGENT_IDS = frozenset({"inventory_entity_pick"})


def test_all_agent_prompt_files_exist() -> None:
    found = set(list_agent_prompt_ids())
    assert _EXPECTED_IDS <= found


@pytest.mark.parametrize("agent_id", sorted(_EXPECTED_IDS))
def test_load_agent_prompt_non_empty(agent_id: str) -> None:
    text = load_agent_prompt(agent_id)
    assert len(text) > 40


@pytest.mark.parametrize(
    "agent_id",
    sorted(
        _EXPECTED_IDS
        - {"chat_normal", "summarize", "gen_sql", "context_compact"}
        - _CATALOG_DRAFT_ENTITY_PLAYBOOKS
        - _INVENTORY_DRAFT_PLAYBOOKS
        - _LEGACY_AGENT_IDS
    ),
)
def test_load_agent_json_contract_non_empty(agent_id: str) -> None:
    contract = load_agent_json_contract(agent_id)
    assert contract
    assert "JSON" in contract or "json" in contract.lower()


def test_gen_sql_mentions_retry_mechanism() -> None:
    body = load_agent_prompt("gen_sql")
    assert "retry" in body.lower() or "WORK SESSION" in body


@pytest.mark.parametrize(
    "entity_type,needle",
    [
        ("product", "skuCode"),
        ("category", "categoryCode"),
        ("supplier", "supplierCode"),
        ("customer", "customerCode"),
    ],
)
def test_load_catalog_draft_system_prompt_includes_entity_playbook(
    entity_type: str, needle: str
) -> None:
    text = load_catalog_draft_system_prompt(entity_type)
    assert "Playbook bắt buộc" in text
    assert needle in text
    assert load_agent_prompt("catalog_draft") in text
    assert load_agent_prompt(catalog_draft_entity_prompt_id(entity_type)) in text


def test_catalog_draft_entity_prompt_id_rejects_unknown() -> None:
    with pytest.raises(ValueError, match="unknown catalog"):
        catalog_draft_entity_prompt_id("warehouse")


def test_load_inventory_draft_system_prompt_includes_stock_receipt() -> None:
    text = load_inventory_draft_system_prompt("stock_receipt")
    assert "Playbook bắt buộc" in text
    assert "skuCode" in text
    assert "supplierName" in text
