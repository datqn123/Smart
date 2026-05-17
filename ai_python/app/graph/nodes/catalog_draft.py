"""Catalog draft pipeline: pick entity → generate rows → validate → persist Spring."""

from __future__ import annotations

import logging

from langchain_core.messages import AIMessage, SystemMessage

from app.graph.agent_trace import emit_agent_trace
from app.graph.catalog_draft_schema import (
    default_columns,
    normalize_rows,
    validate_draft_rows,
)
from app.graph.deps import GraphDeps
from app.graph.message_utils import latest_human_question
from app.graph.spring_catalog_draft_client import post_catalog_draft
from app.graph.state import AgentState
from app.llm.schemas import CatalogDraftGenerateOutput, CatalogEntityPickOutput
from app.prompts.load import load_agent_json_contract, load_agent_prompt

logger = logging.getLogger(__name__)

_ENTITY_PICK_SYSTEM = load_agent_prompt("catalog_entity_pick")
_ENTITY_PICK_CONTRACT = load_agent_json_contract("catalog_entity_pick") or ""
_DRAFT_SYSTEM = load_agent_prompt("catalog_draft")
_DRAFT_CONTRACT = load_agent_json_contract("catalog_draft") or ""


def make_classify_catalog_entity_node(deps: GraphDeps):
    def classify_catalog_entity(state: AgentState) -> dict:
        logger.info("node=classify_catalog_entity action=start")
        question = latest_human_question(state.get("messages"))
        reg = deps.llm_registry
        entity_type = "product"
        row_hint = 3
        if reg is not None:
            client = reg.get("intent")
            prompt = f"{_ENTITY_PICK_SYSTEM}\n\nCâu người dùng:\n{question}"
            try:
                out = client.structured_predict(
                    [SystemMessage(content=prompt)],
                    CatalogEntityPickOutput,
                    json_output_contract=_ENTITY_PICK_CONTRACT,
                )
                entity_type = out.entity_type
                row_hint = max(1, min(50, out.row_count_hint))
            except Exception:
                logger.warning("catalog entity pick failed; default product", exc_info=True)
        emit_agent_trace(
            logger,
            deps.settings,
            agent="catalog_entity",
            phase="Chọn loại catalog",
            detail=f"entity_type={entity_type} rows≈{row_hint}",
        )
        return {"catalog_entity_type": entity_type, "catalog_row_count_hint": row_hint}

    return classify_catalog_entity


def make_generate_catalog_draft_node(deps: GraphDeps):
    def generate_catalog_draft(state: AgentState) -> dict:
        logger.info("node=generate_catalog_draft action=start")
        entity_type = state.get("catalog_entity_type") or "product"
        row_hint = int(state.get("catalog_row_count_hint") or 3)
        question = latest_human_question(state.get("messages"))
        columns = default_columns(entity_type)
        rows: list[dict] = []
        reg = deps.llm_registry
        if reg is not None:
            client = reg.get("gen_sql")
            user_block = (
                f"entity_type={entity_type}\nrow_count_hint={row_hint}\n\n"
                f"Câu người dùng:\n{question}"
            )
            try:
                out = client.structured_predict(
                    [SystemMessage(content=_DRAFT_SYSTEM), SystemMessage(content=user_block)],
                    CatalogDraftGenerateOutput,
                    json_output_contract=_DRAFT_CONTRACT,
                )
                if out.columns:
                    columns = [c.model_dump() for c in out.columns]
                rows = normalize_rows([r.model_dump() for r in out.rows])
            except Exception:
                logger.warning("catalog draft LLM failed; using stub rows", exc_info=True)
        if not rows:
            rows = _stub_rows(entity_type, row_hint)
        payload = {
            "entityType": entity_type,
            "columns": columns,
            "rows": rows,
            "meta": {"sourcePrompt": question[:500]},
        }
        emit_agent_trace(
            logger,
            deps.settings,
            agent="catalog_draft",
            phase="Sinh bảng nháp",
            detail=f"entity={entity_type} row_count={len(rows)}",
        )
        return {"catalog_draft_payload": payload}

    return generate_catalog_draft


def make_persist_catalog_draft_node(deps: GraphDeps):
    def persist_catalog_draft(state: AgentState) -> dict:
        logger.info("node=persist_catalog_draft action=start")
        payload = state.get("catalog_draft_payload") or {}
        entity_type = payload.get("entityType") or state.get("catalog_entity_type") or "product"
        rows = payload.get("rows") or []
        if isinstance(rows, list):
            issues = validate_draft_rows(entity_type, rows)
        else:
            issues = ["rows không hợp lệ"]
        if issues:
            msg = "Không thể tạo nháp: " + "; ".join(issues[:5])
            return {
                "final_answer": msg,
                "messages": [AIMessage(content=msg)],
                "error_payload": {"code": "CATALOG_DRAFT_INVALID", "message": msg},
            }
        columns = payload.get("columns") or default_columns(entity_type)
        bearer = state.get("spring_bearer_token")
        conversation_id = state.get("thread_id")
        try:
            saved = post_catalog_draft(
                deps.settings,
                bearer_token=bearer,
                entity_type=entity_type,
                columns=columns if isinstance(columns, list) else default_columns(entity_type),
                rows=rows,
                conversation_id=conversation_id,
                meta=payload.get("meta") if isinstance(payload.get("meta"), dict) else None,
            )
        except Exception as exc:
            logger.warning("persist catalog draft failed", exc_info=True)
            msg = f"Không lưu được nháp trên server: {exc}"
            return {
                "final_answer": msg,
                "messages": [AIMessage(content=msg)],
                "error_payload": {"code": "CATALOG_DRAFT_PERSIST", "message": msg},
            }
        draft_id = str(saved.get("id") or "")
        sse_payload = {
            "draftId": draft_id,
            "entityType": entity_type,
            "columns": columns,
            "rows": saved.get("rows") or rows,
            "status": saved.get("status"),
            "previewMessage": _preview_message(entity_type, len(rows)),
        }
        answer = (
            f"Đã tạo bảng nháp ({entity_type}, {len(rows)} dòng). "
            "Bạn có thể chỉnh sửa bên dưới rồi bấm **Lưu nháp** và **Xác nhận ghi DB**."
        )
        emit_agent_trace(
            logger,
            deps.settings,
            agent="catalog_draft",
            phase="Lưu nháp Spring",
            detail=f"draftId={draft_id}",
        )
        return {
            "catalog_draft_id": draft_id,
            "catalog_draft_sse": sse_payload,
            "final_answer": answer,
            "messages": [AIMessage(content=answer)],
        }

    return persist_catalog_draft


def _preview_message(entity_type: str, count: int) -> str:
    labels = {
        "product": "sản phẩm",
        "category": "danh mục",
        "supplier": "nhà cung cấp",
        "customer": "khách hàng",
    }
    return f"{count} dòng {labels.get(entity_type, entity_type)}"


def _stub_rows(entity_type: str, count: int) -> list[dict]:
    n = max(1, min(count, 3))
    rows: list[dict] = []
    for i in range(n):
        idx = i + 1
        if entity_type == "category":
            values = {
                "categoryCode": f"CAT-AI-{idx:03d}",
                "name": f"Danh mục AI {idx}",
                "status": "Active",
            }
        elif entity_type == "supplier":
            values = {
                "supplierCode": f"NCC-AI-{idx:03d}",
                "name": f"NCC AI {idx}",
                "contactPerson": "Liên hệ",
                "phone": f"0900000{idx:03d}",
                "status": "Active",
            }
        elif entity_type == "customer":
            values = {
                "customerCode": f"KH-AI-{idx:03d}",
                "name": f"Khách AI {idx}",
                "phone": f"0910000{idx:03d}",
                "status": "Active",
            }
        else:
            values = {
                "skuCode": f"AI-{idx:03d}",
                "name": f"Sản phẩm AI {idx}",
                "baseUnitName": "Cái",
                "costPrice": 10000,
                "salePrice": 15000,
                "status": "Active",
            }
        rows.append({"rowId": f"r{idx}", "values": values})
    return rows
