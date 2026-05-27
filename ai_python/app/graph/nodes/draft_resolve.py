"""Pre-draft DB resolution nodes (inventory + catalog)."""

from __future__ import annotations

import logging

from langchain_core.messages import AIMessage

from app.graph.agent_trace import emit_agent_trace
from app.graph.deps import GraphDeps
from app.graph.draft_entity_resolution import (
    resolve_catalog_before_generate,
    resolve_inventory_before_generate,
)
from app.graph.draft_slots_llm import predict_catalog_draft_slots, predict_inventory_draft_slots
from app.graph.progress import emit_progress
from app.llm.schemas import CatalogDraftSlotsOutput, InventoryDraftSlotsOutput
from app.graph.message_utils import latest_human_question
from app.graph.state import AgentState

logger = logging.getLogger(__name__)


def route_after_draft_resolve(state: AgentState) -> str:
    if state.get("final_answer"):
        return "stop"
    return "continue"


def route_after_catalog_generate(state: AgentState) -> str:
    """Skip persist when generate failed or produced no rows."""
    if state.get("final_answer") and not state.get("catalog_draft_payload"):
        return "stop"
    payload = state.get("catalog_draft_payload")
    if not isinstance(payload, dict):
        return "stop"
    rows = payload.get("rows")
    if not isinstance(rows, list) or len(rows) == 0:
        return "stop"
    return "continue"


def make_resolve_inventory_draft_node(deps: GraphDeps):
    def resolve_inventory_draft(state: AgentState) -> dict:
        logger.info("node=resolve_inventory_draft action=start")
        question = latest_human_question(state.get("messages"))
        raw_slots = state.get("inventory_draft_slots")
        if isinstance(raw_slots, dict):
            slots = InventoryDraftSlotsOutput.model_validate(raw_slots)
        else:
            slots = predict_inventory_draft_slots(deps, question)
        patch = resolve_inventory_before_generate(
            question=question,
            slots=slots,
            executor=deps.sql_executor,
            tenant_id=state.get("tenant_id"),
        )
        if patch:
            msg = str(patch.get("final_answer") or "")
            patch["messages"] = [AIMessage(content=msg)]
            emit_agent_trace(
                logger,
                deps.settings,
                agent="inventory_resolve",
                phase="Tra cứu DB trước nháp",
                detail="clarify",
            )
            return patch
        emit_agent_trace(
            logger,
            deps.settings,
            agent="inventory_resolve",
            phase="Tra cứu DB trước nháp",
            detail=f"proceed doc={slots.doc_type}",
        )
        return {
            **emit_progress(state, "draft_resolve"),
            "inventory_doc_type": slots.doc_type,
            "inventory_draft_slots": slots.model_dump(),
        }

    return resolve_inventory_draft


def make_resolve_catalog_draft_node(deps: GraphDeps):
    def resolve_catalog_draft(state: AgentState) -> dict:
        logger.info("node=resolve_catalog_draft action=start")
        question = latest_human_question(state.get("messages"))
        raw_slots = state.get("catalog_draft_slots")
        if isinstance(raw_slots, dict):
            slots = CatalogDraftSlotsOutput.model_validate(raw_slots)
        else:
            slots = predict_catalog_draft_slots(deps, question)
        patch = resolve_catalog_before_generate(
            question=question,
            slots=slots,
            executor=deps.sql_executor,
            tenant_id=state.get("tenant_id"),
            llm_registry=deps.llm_registry,
            settings=deps.settings,
        )
        if patch:
            if "final_answer" in patch:
                msg = str(patch.get("final_answer") or "")
                patch["messages"] = [AIMessage(content=msg)]
                emit_agent_trace(
                    logger,
                    deps.settings,
                    agent="catalog_resolve",
                    phase="Tra cứu DB trước nháp",
                    detail="clarify",
                )
                return patch
            else:
                emit_agent_trace(
                    logger,
                    deps.settings,
                    agent="catalog_resolve",
                    phase="Tra cứu DB trước nháp (Tải dữ liệu có sẵn)",
                    detail=f"loaded existing rows: {len(patch.get('catalog_draft_existing_data') or [])}",
                )
                return {
                    **emit_progress(state, "draft_resolve"),
                    "catalog_entity_type": slots.entity_type,
                    "catalog_row_count_hint": slots.row_count_hint,
                    "catalog_draft_slots": slots.model_dump(),
                    **patch
                }
        emit_agent_trace(
            logger,
            deps.settings,
            agent="catalog_resolve",
            phase="Tra cứu DB trước nháp",
            detail=f"proceed entity={slots.entity_type}",
        )
        return {
            **emit_progress(state, "draft_resolve"),
            "catalog_entity_type": slots.entity_type,
            "catalog_row_count_hint": slots.row_count_hint,
            "catalog_draft_slots": slots.model_dump(),
        }

    return resolve_catalog_draft
