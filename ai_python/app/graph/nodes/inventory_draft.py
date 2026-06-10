"""Inventory document draft: pick doc → generate → persist Spring."""

from __future__ import annotations

import logging

from langchain_core.messages import AIMessage, SystemMessage

from app.graph.agent_trace import emit_agent_trace
from app.graph.answer_quality import finalize_answer
from app.graph.deps import GraphDeps
from app.graph.inventory_draft_schema import (
    default_line_columns,
    default_receipt_header,
    enrich_receipt_header,
    enrich_receipt_lines,
    normalize_lines,
    validate_receipt_draft,
)
from app.graph.message_utils import latest_human_question
from app.graph.draft_reference_messages import (
    format_draft_schema_issues,
    format_reference_validation_failure,
)
from app.graph.draft_slots_llm import predict_inventory_draft_slots
from app.graph.pg_schema_context import build_schema_artifact_for_table_names
from app.graph.progress import emit_progress
from app.graph.spring_inventory_draft_client import (
    post_inventory_draft,
    validate_inventory_draft_references,
)
from app.graph.sql_prompts import format_schema_block
from app.graph.state import AgentState
from app.harness import ToolCallContext
from app.llm.schemas import InventoryDraftGenerateOutput
from app.prompts.load import (
    load_inventory_draft_json_contract,
    load_inventory_draft_system_prompt,
)

logger = logging.getLogger(__name__)

_DRAFT_CONTRACT = load_inventory_draft_json_contract() or ""

# Tables relevant to inventory draft — introspected from Postgres at runtime.
_INVENTORY_SCHEMA_TABLES = [
    "products",
    "suppliers",
    "inventory",
    "stockreceipts",
    "stockreceiptdetails",
    "productunits",
    "categories",
]


def make_classify_inventory_doc_node(deps: GraphDeps):
    def classify_inventory_doc(state: AgentState) -> dict:
        logger.info("node=classify_inventory_doc action=start")
        question = latest_human_question(state.get("messages"))
        slots = predict_inventory_draft_slots(deps, question)
        doc_type = slots.doc_type
        line_hint = max(1, min(20, slots.line_count_hint))
        emit_agent_trace(
            logger,
            deps.settings,
            agent="inventory_draft_slots",
            phase="Tách slot phiếu kho (LLM)",
            detail=f"doc_type={doc_type} qty={slots.quantity} product={slots.product_query!r}",
        )
        return {
            **emit_progress(state, "classify_inventory_doc"),
            "inventory_doc_type": doc_type,
            "inventory_line_count_hint": line_hint,
            "inventory_draft_slots": slots.model_dump(),
        }

    return classify_inventory_doc


def _build_schema_context_for_draft(deps: GraphDeps) -> str:
    """Introspect Postgres schema for inventory-related tables and format for LLM."""
    try:
        artifact, err = deps.harness.run_tool(
            tool_name="schema.build_artifact_for_table_names",
            tool=lambda: build_schema_artifact_for_table_names(
                deps.settings, _INVENTORY_SCHEMA_TABLES
            ),
            context=ToolCallContext(tool_name="schema.build_artifact_for_table_names"),
        )
        if artifact is not None:
            return format_schema_block(artifact, selected_tables=None, enriched=True)
    except Exception as exc:
        logger.warning("inventory draft schema introspect failed: %s", exc)
    return ""


def make_generate_inventory_draft_node(deps: GraphDeps):
    def generate_inventory_draft(state: AgentState) -> dict:
        logger.info("node=generate_inventory_draft action=start")
        doc_type = state.get("inventory_doc_type") or "stock_receipt"
        line_hint = int(state.get("inventory_line_count_hint") or 1)
        question = latest_human_question(state.get("messages"))
        header = default_receipt_header()
        line_columns = default_line_columns(doc_type)
        lines: list[dict] = []
        reg = deps.llm_registry
        if reg is not None:
            try:
                client = reg.get("inventory_draft")
            except KeyError:
                try:
                    client = reg.get("intent")
                except KeyError:
                    client = reg.get("default")
            draft_system = load_inventory_draft_system_prompt(doc_type)
            # Inject real DB schema context so LLM sees actual table/column names
            schema_ctx = _build_schema_context_for_draft(deps)
            if schema_ctx:
                draft_system += (
                    "\n\n## Database Schema Reference (read-only — dùng để đối chiếu tên cột/bảng thực tế)\n\n"
                    + schema_ctx
                )
            slots_blob = state.get("inventory_draft_slots")
            user_block = (
                f"doc_type={doc_type}\nline_count_hint={line_hint}\n"
                f"resolved_slots={slots_blob}\n\n"
                f"Câu người dùng:\n{question}"
            )
            try:
                out = client.structured_predict(
                    [SystemMessage(content=draft_system), SystemMessage(content=user_block)],
                    InventoryDraftGenerateOutput,
                    json_output_contract=_DRAFT_CONTRACT,
                )
                if out.header:
                    header = {**header, **out.header}
                if out.lineColumns:
                    line_columns = [c.model_dump() for c in out.lineColumns]
                raw = [ln.model_dump() for ln in out.lines]
                lines = enrich_receipt_lines(
                    normalize_lines(raw),
                    user_prompt=question,
                    header=header,
                )
            except Exception:
                logger.warning("inventory draft LLM failed; using stub", exc_info=True)
        doc_label = (
            "phiếu xuất kho"
            if doc_type == "stock_dispatch"
            else "phiếu nhập kho"
        )
        if not lines:
            msg = (
                f"Không tạo được nháp **{doc_label}** từ câu hỏi.\n\n"
                "Vui lòng nêu **tên hoặc mã SKU** sản phẩm"
                + (
                    " và **số lượng** xuất."
                    if doc_type == "stock_dispatch"
                    else " và **nhà cung cấp (mã hoặc tên)** đã có trong hệ thống."
                )
            )
            return {
                **emit_progress(state, "generate_inventory_draft"),
                "final_answer": msg,
                "messages": [AIMessage(content=msg)],
                "error_payload": {"code": "INVENTORY_DRAFT_EMPTY", "message": msg},
            }
        header = enrich_receipt_header(header, user_prompt=question)
        lines = enrich_receipt_lines(lines, user_prompt=question, header=header)
        slots_raw = state.get("inventory_draft_slots")
        if doc_type == "stock_receipt" and isinstance(slots_raw, dict):
            slot_qty = slots_raw.get("quantity")
            if slot_qty is not None:
                try:
                    qn = int(slot_qty)
                    if qn > 0:
                        for row in lines:
                            vals = row.get("values")
                            if not isinstance(vals, dict):
                                continue
                            cur = vals.get("quantity")
                            if cur is None or cur == "" or int(cur) <= 0:
                                vals["quantity"] = qn
                except (TypeError, ValueError):
                    pass
        payload = {
            "entityType": doc_type,
            "header": header,
            "lineColumns": line_columns,
            "lines": lines,
            "meta": {"sourcePrompt": question[:500]},
        }
        emit_agent_trace(
            logger,
            deps.settings,
            agent="inventory_draft",
            phase="Sinh nháp phiếu kho",
            detail=f"doc={doc_type} line_count={len(lines)}",
        )
        return {**emit_progress(state, "generate_inventory_draft"), "inventory_draft_payload": payload}

    return generate_inventory_draft


def make_persist_inventory_draft_node(deps: GraphDeps):
    def persist_inventory_draft(state: AgentState) -> dict:
        logger.info("node=persist_inventory_draft action=start")
        payload = state.get("inventory_draft_payload") or {}
        doc_type = payload.get("entityType") or state.get("inventory_doc_type") or "stock_receipt"
        header = payload.get("header") if isinstance(payload.get("header"), dict) else {}
        lines = payload.get("lines") or []
        if isinstance(lines, list):
            issues = validate_receipt_draft(header, lines)
        else:
            issues = ["lines không hợp lệ"]
        doc_label = (
            "phiếu xuất kho"
            if doc_type == "stock_dispatch"
            else "phiếu nhập kho"
        )
        if issues:
            msg = format_draft_schema_issues(
                doc_kind=doc_label,
                issues=issues,
                extra_hints=(
                    [
                        "Phiếu nhập: bổ sung **số lượng nhập** (> 0). Không cần tồn kho trước khi nhập.",
                        "Ví dụ: «Tạo phiếu nhập SKU … từ NCC …, số lượng 50».",
                    ]
                    if doc_type == "stock_receipt"
                    else None
                ),
            )
            return {
                **emit_progress(state, "persist_inventory_draft"),
                "final_answer": msg,
                "messages": [AIMessage(content=msg)],
                "error_payload": {"code": "INVENTORY_DRAFT_INVALID", "message": msg},
            }
        line_columns = payload.get("lineColumns") or default_line_columns(doc_type)
        bearer = state.get("spring_bearer_token")
        # NOTE: Bỏ qua validate_inventory_draft_references (cuộc gọi HTTP /validate)
        # vì node resolve_inventory_draft đã trực tiếp truy vấn SQL để xác thực
        # SKU và Nhà cung cấp trước khi vào đây. Tiết kiệm ~2-4s trễ mạng.
        conversation_id = state.get("thread_id")
        try:
            saved = deps.harness.run_tool(
                tool_name="inventory_draft.post",
                tool=lambda: post_inventory_draft(
                    deps.settings,
                    bearer_token=bearer,
                    entity_type=doc_type,
                    header=header,
                    line_columns=line_columns if isinstance(line_columns, list) else default_line_columns(doc_type),
                    lines=lines,
                    conversation_id=conversation_id,
                    meta=payload.get("meta") if isinstance(payload.get("meta"), dict) else None,
                ),
                context=ToolCallContext(
                    tool_name="inventory_draft.post",
                    correlation_id=str(state.get("correlation_id") or "") or None,
                    tenant_id=str(state.get("tenant_id") or "") or None,
                    thread_id=str(state.get("thread_id") or "") or None,
                ),
            )
        except Exception as exc:
            logger.warning("persist inventory draft failed", exc_info=True)
            msg = f"Không lưu được nháp trên server: {exc}"
            return {
                **emit_progress(state, "persist_inventory_draft"),
                "final_answer": msg,
                "messages": [AIMessage(content=msg)],
                "error_payload": {"code": "INVENTORY_DRAFT_PERSIST", "message": msg},
            }
        draft_id = str(saved.get("id") or "")
        sse_payload = {
            "draftId": draft_id,
            "entityType": doc_type,
            "header": saved.get("header") or header,
            "lineColumns": saved.get("lineColumns") or line_columns,
            "lines": saved.get("lines") or lines,
            "status": saved.get("status"),
            "previewMessage": _preview_message(doc_type, lines, header),
        }
        preview = _preview_message(doc_type, lines, header)
        answer = (
            f"Đã tạo nháp phiếu nhập kho ({preview}).\n\n"
            "Bước tiếp theo:\n"
            "- Kiểm tra header và từng dòng hàng trong bảng bên dưới.\n"
            "- Bấm **Lưu nháp** → **Xác nhận tạo phiếu** (Draft/Pending).\n"
            "- Duyệt và chọn vị trí nhập tại màn **Nhập kho**.\n"
            "- Bạn có thể hỏi để thêm dòng hoặc chỉnh số lượng / NCC."
        )
        answer = finalize_answer(
            answer,
            deps=deps,
            node_name="inventory_draft",
            scenario="draft_confirm",
        )
        emit_agent_trace(
            logger,
            deps.settings,
            agent="inventory_draft",
            phase="Lưu nháp Spring",
            detail=f"draftId={draft_id}",
        )
        return {
            **emit_progress(state, "persist_inventory_draft"),
            "inventory_draft_id": draft_id,
            "inventory_draft_sse": sse_payload,
            "final_answer": answer,
            "messages": [AIMessage(content=answer)],
        }

    return persist_inventory_draft


def _preview_message(doc_type: str, lines: list, header: dict) -> str:
    if doc_type == "stock_receipt":
        total_qty = 0
        for ln in lines:
            v = ln.get("values") if isinstance(ln.get("values"), dict) else ln
            try:
                total_qty += int(v.get("quantity") or 0)
            except (TypeError, ValueError):
                pass
        ncc = header.get("supplierName") or header.get("supplierCode") or "NCC"
        return f"Phiếu nhập — {len(lines)} dòng, ~{total_qty} SP ({ncc})"
    return f"{doc_type} — {len(lines)} dòng"

