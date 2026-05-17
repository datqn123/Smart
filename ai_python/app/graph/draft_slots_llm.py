"""LLM slot extraction for draft DB resolution (prompts in agents/*_draft_slots.md)."""

from __future__ import annotations

import logging

from langchain_core.messages import SystemMessage

from app.graph.deps import GraphDeps
from app.llm.schemas import CatalogDraftSlotsOutput, InventoryDraftSlotsOutput
from app.prompts.load import load_agent_json_contract, load_agent_prompt

logger = logging.getLogger(__name__)

_INVENTORY_SLOTS_SYSTEM = load_agent_prompt("inventory_draft_slots")
_INVENTORY_SLOTS_CONTRACT = load_agent_json_contract("inventory_draft_slots") or ""
_CATALOG_SLOTS_SYSTEM = load_agent_prompt("catalog_draft_slots")
_CATALOG_SLOTS_CONTRACT = load_agent_json_contract("catalog_draft_slots") or ""


def predict_inventory_draft_slots(
    deps: GraphDeps,
    question: str,
) -> InventoryDraftSlotsOutput:
    if not (question or "").strip():
        return InventoryDraftSlotsOutput()
    reg = deps.llm_registry
    if reg is None:
        logger.warning("inventory_draft_slots: no LLM registry")
        return InventoryDraftSlotsOutput()
    client = reg.get("intent")
    prompt = f"{_INVENTORY_SLOTS_SYSTEM}\n\nCâu người dùng:\n{question.strip()}"
    try:
        return client.structured_predict(
            [SystemMessage(content=prompt)],
            InventoryDraftSlotsOutput,
            json_output_contract=_INVENTORY_SLOTS_CONTRACT,
        )
    except Exception:
        logger.warning("inventory_draft_slots LLM failed", exc_info=True)
        return InventoryDraftSlotsOutput()


def predict_catalog_draft_slots(
    deps: GraphDeps,
    question: str,
) -> CatalogDraftSlotsOutput:
    if not (question or "").strip():
        return CatalogDraftSlotsOutput()
    reg = deps.llm_registry
    if reg is None:
        logger.warning("catalog_draft_slots: no LLM registry")
        return CatalogDraftSlotsOutput()
    try:
        client = reg.get("catalog_draft_slots")
    except KeyError:
        client = reg.get("intent")
    prompt = f"{_CATALOG_SLOTS_SYSTEM}\n\nCâu người dùng:\n{question.strip()}"
    try:
        return client.structured_predict(
            [SystemMessage(content=prompt)],
            CatalogDraftSlotsOutput,
            json_output_contract=_CATALOG_SLOTS_CONTRACT,
        )
    except Exception:
        logger.warning("catalog_draft_slots LLM failed", exc_info=True)
        return CatalogDraftSlotsOutput()
