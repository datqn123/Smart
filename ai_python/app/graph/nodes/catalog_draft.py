"""Catalog draft pipeline: pick entity → generate rows → validate → persist Spring."""

from __future__ import annotations

import logging

import re

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.graph.agent_trace import emit_agent_trace
from app.graph.answer_quality import finalize_answer
from app.graph.catalog_draft_schema import (
    default_columns,
    enrich_catalog_draft_rows,
    normalize_rows,
    validate_draft_rows,
)
from app.graph.deps import GraphDeps
from app.graph.message_utils import latest_human_question
from app.graph.draft_reference_messages import (
    format_draft_schema_issues,
    format_reference_validation_failure,
)
from app.graph.draft_slots_llm import predict_catalog_draft_slots
from app.graph.progress import emit_progress
from app.graph.spring_catalog_draft_client import (
    post_catalog_draft,
    validate_catalog_draft_references,
)
from app.graph.state import AgentState
from app.harness import ToolCallContext
from app.llm.schemas import CatalogDraftGenerateOutput
from app.prompts.load import (
    load_catalog_draft_json_contract,
    load_catalog_draft_system_prompt,
)

logger = logging.getLogger(__name__)

_DRAFT_CONTRACT = load_catalog_draft_json_contract() or ""


def make_classify_catalog_entity_node(deps: GraphDeps):
    def classify_catalog_entity(state: AgentState) -> dict:
        logger.info("node=classify_catalog_entity action=start")
        question = latest_human_question(state.get("messages"))
        slots = predict_catalog_draft_slots(deps, question)
        entity_type = slots.entity_type
        row_hint = max(1, min(50, slots.row_count_hint))
        emit_agent_trace(
            logger,
            deps.settings,
            agent="catalog_draft_slots",
            phase="Tách slot catalog (LLM)",
            detail=f"entity={entity_type} product={slots.product_query!r}",
        )
        return {
            **emit_progress(state, "classify_catalog_entity"),
            "catalog_entity_type": entity_type,
            "catalog_row_count_hint": row_hint,
            "catalog_draft_slots": slots.model_dump(),
        }

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
        slots_raw = state.get("catalog_draft_slots")
        slots_dict = slots_raw if isinstance(slots_raw, dict) else None
        if reg is not None:
            try:
                client = reg.get("catalog_draft")
            except KeyError:
                try:
                    client = reg.get("intent")
                except KeyError:
                    client = reg.get("default")
            draft_system = load_catalog_draft_system_prompt(entity_type)
            user_block = (
                f"entity_type={entity_type}\nrow_count_hint={row_hint}\n"
                f"resolved_slots={slots_dict}\n\n"
                f"Câu người dùng:\n{question}"
            )
            existing_data = state.get("catalog_draft_existing_data")
            if existing_data and isinstance(existing_data, list):
                if entity_type == "product":
                    headers = ["skuCode", "name", "categoryName", "categoryCode", "baseUnitName", "costPrice", "salePrice", "barcode", "status"]
                    id_col = "skuCode"
                    label_vi = "sản phẩm"
                elif entity_type == "supplier":
                    headers = ["supplierCode", "name", "contactPerson", "phone", "email", "address", "taxCode", "status"]
                    id_col = "supplierCode"
                    label_vi = "nhà cung cấp"
                elif entity_type == "customer":
                    headers = ["customerCode", "name", "phone", "email", "address", "status"]
                    id_col = "customerCode"
                    label_vi = "khách hàng"
                elif entity_type == "category":
                    headers = ["categoryCode", "name", "description", "parentName", "parentCode", "status"]
                    id_col = "categoryCode"
                    label_vi = "danh mục"
                else:
                    headers = list(existing_data[0].keys()) if existing_data else []
                    id_col = headers[0] if headers else ""
                    label_vi = entity_type
                
                rows_md = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
                for row in existing_data:
                    vals = [str(row.get(h) if row.get(h) is not None else "") for h in headers]
                    rows_md.append("| " + " | ".join(vals) + " |")
                md_table = "\n".join(rows_md)
                user_block += (
                    f"\n\n## DỮ LIỆU HIỆN CÓ SẴN TRONG HỆ THỐNG:\n{md_table}\n\n"
                    f"CHỈ THỊ QUAN TRỌNG:\n"
                    f"1. Người dùng đang muốn nạp dữ liệu hiện có này vào bảng để chỉnh sửa/cập nhật. Hãy đọc kỹ bảng trên.\n"
                    f"2. Hãy xuất toàn bộ các {label_vi} trong danh sách này vào kết quả JSON dưới dạng danh sách `rows` (giữ nguyên đúng {id_col} của từng dòng để thực hiện cập nhật).\n"
                    f"3. ĐỒNG THỜI, hãy áp dụng chính xác các yêu cầu chỉnh sửa/cập nhật bằng ngôn ngữ tự nhiên từ câu người dùng (ví dụ: thay đổi thông tin, trạng thái, địa chỉ, tăng giá...) lên dữ liệu gốc trên trước khi ghi nhận vào JSON.\n"
                    f"4. Không tự ý bịa thêm dữ liệu rác ngoài bảng trên trừ khi người dùng yêu cầu rõ ràng việc tạo mới."
                )
            try:
                out = client.structured_predict(
                    [SystemMessage(content=draft_system), HumanMessage(content=user_block)],
                    CatalogDraftGenerateOutput,
                    json_output_contract=_DRAFT_CONTRACT,
                )
                if out.columns:
                    columns = [c.model_dump() for c in out.columns]
                raw = [r.model_dump() for r in out.rows]
                rows = enrich_catalog_draft_rows(
                    entity_type,
                    normalize_rows(raw),
                    user_prompt=question,
                )
            except Exception:
                logger.warning("catalog draft LLM failed; using fallback rows", exc_info=True)
                rows = _fallback_catalog_rows(
                    entity_type,
                    count=row_hint,
                    question=question,
                    slots=slots_dict,
                )
                rows = enrich_catalog_draft_rows(entity_type, rows, user_prompt=question)
        if not rows:
            msg = (
                "Không tạo được bảng nháp từ câu hỏi. "
                "Vui lòng nêu rõ mã/tên theo loại dữ liệu (SKU, mã NCC, …) cần nhập."
            )
            return {
                **emit_progress(state, "generate_catalog_draft"),
                "final_answer": msg,
                "messages": [AIMessage(content=msg)],
                "error_payload": {"code": "CATALOG_DRAFT_EMPTY", "message": msg},
            }
        rows = enrich_catalog_draft_rows(entity_type, rows, user_prompt=question)
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
        return {**emit_progress(state, "generate_catalog_draft"), "catalog_draft_payload": payload}

    return generate_catalog_draft


def make_persist_catalog_draft_node(deps: GraphDeps):
    def persist_catalog_draft(state: AgentState) -> dict:
        logger.info("node=persist_catalog_draft action=start")
        payload = state.get("catalog_draft_payload") or {}
        entity_type = payload.get("entityType") or state.get("catalog_entity_type") or "product"
        rows = payload.get("rows") or []
        if not isinstance(rows, list) or len(rows) == 0:
            msg = "Bảng nháp trống — không có dòng để lưu. Vui lòng thử lại và nêu rõ tên hoặc mã cần nhập."
            return {
                **emit_progress(state, "persist_catalog_draft"),
                "final_answer": msg,
                "messages": [AIMessage(content=msg)],
                "error_payload": {"code": "CATALOG_DRAFT_EMPTY", "message": msg},
            }
        if isinstance(rows, list):
            issues = validate_draft_rows(entity_type, rows)
        else:
            issues = ["rows không hợp lệ"]
        kind = {
            "product": "sản phẩm",
            "supplier": "nhà cung cấp",
            "category": "danh mục",
            "customer": "khách hàng",
        }.get(entity_type, entity_type)
        if issues:
            msg = format_draft_schema_issues(doc_kind=kind, issues=issues)
            return {
                **emit_progress(state, "persist_catalog_draft"),
                "final_answer": msg,
                "messages": [AIMessage(content=msg)],
                "error_payload": {"code": "CATALOG_DRAFT_INVALID", "message": msg},
            }
        columns = payload.get("columns") or default_columns(entity_type)
        bearer = state.get("spring_bearer_token")
        try:
            db_issues = deps.harness.run_tool(
                tool_name="catalog_draft.validate_references",
                tool=lambda: validate_catalog_draft_references(
                    deps.settings,
                    bearer_token=bearer,
                    entity_type=entity_type,
                    columns=columns if isinstance(columns, list) else default_columns(entity_type),
                    rows=rows,
                ),
                context=ToolCallContext(
                    tool_name="catalog_draft.validate_references",
                    correlation_id=str(state.get("correlation_id") or "") or None,
                    tenant_id=str(state.get("tenant_id") or "") or None,
                    thread_id=str(state.get("thread_id") or "") or None,
                ),
            )
        except Exception as exc:
            logger.warning("catalog draft DB validate failed", exc_info=True)
            msg = f"Không kiểm tra được dữ liệu tham chiếu: {exc}"
            return {
                **emit_progress(state, "persist_catalog_draft"),
                "final_answer": msg,
                "messages": [AIMessage(content=msg)],
                "error_payload": {"code": "CATALOG_DRAFT_VALIDATE", "message": msg},
            }
        if db_issues:
            kind = {
                "product": "sản phẩm",
                "supplier": "nhà cung cấp",
                "category": "danh mục",
                "customer": "khách hàng",
            }.get(entity_type, entity_type)
            msg = format_reference_validation_failure(draft_kind=kind, issues=db_issues)
            return {
                **emit_progress(state, "persist_catalog_draft"),
                "final_answer": msg,
                "messages": [AIMessage(content=msg)],
                "error_payload": {"code": "CATALOG_DRAFT_REFERENCE", "message": msg},
            }
        conversation_id = state.get("thread_id")
        try:
            saved = deps.harness.run_tool(
                tool_name="catalog_draft.post",
                tool=lambda: post_catalog_draft(
                    deps.settings,
                    bearer_token=bearer,
                    entity_type=entity_type,
                    columns=columns if isinstance(columns, list) else default_columns(entity_type),
                    rows=rows,
                    conversation_id=conversation_id,
                    meta=payload.get("meta") if isinstance(payload.get("meta"), dict) else None,
                ),
                context=ToolCallContext(
                    tool_name="catalog_draft.post",
                    correlation_id=str(state.get("correlation_id") or "") or None,
                    tenant_id=str(state.get("tenant_id") or "") or None,
                    thread_id=str(state.get("thread_id") or "") or None,
                ),
            )
        except Exception as exc:
            logger.warning("persist catalog draft failed", exc_info=True)
            msg = f"Không lưu được nháp trên server: {exc}"
            return {
                **emit_progress(state, "persist_catalog_draft"),
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
        preview = _preview_message(entity_type, len(rows))
        answer = (
            f"Đã tạo bảng nháp **{entity_type}** ({len(rows)} dòng): {preview}.\n\n"
            "Bước tiếp theo:\n"
            "- Chỉnh sửa từng dòng trong bảng bên dưới nếu cần.\n"
            "- Bấm **Lưu nháp** rồi **Xác nhận ghi DB** khi đã đúng.\n"
            "- Bạn có thể hỏi thêm để bổ sung dòng hoặc tạo nháp loại danh mục khác."
        )
        if len(rows) < 2:
            answer += (
                "\n\nGợi ý: nếu cần nhập nhiều bản ghi, mô tả rõ số lượng và thuộc tính "
                "(ví dụ: thêm 5 sản phẩm cùng danh mục)."
            )
        answer = finalize_answer(
            answer,
            deps=deps,
            node_name="catalog_draft",
            scenario="draft_confirm",
        )
        emit_agent_trace(
            logger,
            deps.settings,
            agent="catalog_draft",
            phase="Lưu nháp Spring",
            detail=f"draftId={draft_id}",
        )
        return {
            **emit_progress(state, "persist_catalog_draft"),
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


_NAME_FROM_PROMPT = re.compile(
    r"(?:có\s+)?tên\s+(?:là\s+)?['\"]?([^'\".,;\n]{1,80})",
    re.IGNORECASE,
)


def _display_name_from_slots_and_prompt(
    entity_type: str,
    question: str,
    slots: dict | None,
) -> str | None:
    if slots:
        for key in (
            "supplier_query",
            "customer_query",
            "category_query",
            "product_query",
        ):
            raw = slots.get(key)
            if raw and str(raw).strip():
                return str(raw).strip()
    m = _NAME_FROM_PROMPT.search(question or "")
    if m:
        name = m.group(1).strip()
        if name:
            return name
    return None


def _fallback_catalog_rows(
    entity_type: str,
    *,
    count: int,
    question: str,
    slots: dict | None,
) -> list[dict]:
    """Deterministic rows when structured LLM output fails."""
    rows = _stub_rows(entity_type, count)
    display = _display_name_from_slots_and_prompt(entity_type, question, slots)
    if display and rows:
        rows[0]["values"]["name"] = display
        if entity_type == "supplier" and slots and slots.get("supplier_code"):
            rows[0]["values"]["supplierCode"] = str(slots["supplier_code"]).strip()
        elif entity_type == "category" and slots and slots.get("category_code"):
            rows[0]["values"]["categoryCode"] = str(slots["category_code"]).strip()
        elif entity_type == "customer" and slots and slots.get("customer_query"):
            rows[0]["values"]["name"] = str(slots["customer_query"]).strip()
    return rows


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
