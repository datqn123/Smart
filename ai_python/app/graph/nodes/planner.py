"""Pre-intent planner: pick strategy/route with markdown-grounded context."""

from __future__ import annotations

import logging

from langchain_core.messages import HumanMessage, SystemMessage

from app.graph.agent_trace import emit_agent_trace
from app.graph.deps import GraphDeps
from app.graph.interaction_mode import normalize_interaction_mode
from app.graph.message_utils import effective_user_question, format_dialog_tail_for_sql
from app.graph.planner_md_context import build_planner_md_context
from app.graph.progress import emit_progress
from app.graph.registry import normalize_intent
from app.graph.state import AgentState
from app.llm.schemas import AgentPlannerOutput
from app.prompts.load import load_agent_json_contract, load_agent_prompt

logger = logging.getLogger(__name__)

_PLANNER_SYSTEM = load_agent_prompt("planner")
_PLANNER_CONTRACT = load_agent_json_contract("planner") or ""

_STRATEGY_TO_INTENT: dict[str, str] = {
    "answer_direct": "general_chat",
    "ask_clarification": "general_chat",
    "guide_answer": "general_chat",
    "data_query": "system_data_query",
    "data_table": "system_data_query",
    "data_chart": "system_data_chart",
    "data_then_chart": "system_data_chart",
    "catalog_draft": "catalog_data_entry",
    "inventory_draft": "inventory_data_entry",
}

_TABLE_REQUEST_HINTS = (
    "liệt kê",
    "liet ke",
    "chi tiết",
    "chi tiet",
    "danh sách",
    "danh sach",
    "xem bảng",
    "xem bang",
    "bảng",
    "bang",
    "từng dòng",
    "tung dong",
)

_SCALAR_REQUEST_HINTS = (
    "bao nhiêu",
    "bao nhieu",
    "bao nhiêu?",
    "tổng",
    "tong",
    "số lượng",
    "so luong",
    "đếm",
    "dem",
    "count",
)


def _planner_prompt(state: AgentState, *, md_context: str) -> str:
    user_q = effective_user_question(
        state.get("messages"), state.get("normalized_user_question")
    )
    dialog_tail = format_dialog_tail_for_sql(
        state.get("messages"),
        max_messages=8,
        max_chars=1600,
        summary=state.get("conversation_summary"),
    )
    mode = normalize_interaction_mode(state.get("interaction_mode"))
    parts = [
        f"User question:\n{user_q or '(empty)'}",
        f"interaction_mode={mode}",
    ]
    if dialog_tail:
        parts.append(f"Recent dialog:\n{dialog_tail}")
    if md_context:
        parts.append(f"Runtime markdown references:\n{md_context}")
    return "\n\n".join(parts)


def _intent_from_planner(out: AgentPlannerOutput) -> str | None:
    if out.intent:
        return normalize_intent(out.intent)
    mapped = _STRATEGY_TO_INTENT.get(out.strategy)
    if mapped:
        return normalize_intent(mapped)
    return None


def _wants_table_view(user_q: str | None) -> bool:
    q = (user_q or "").strip().lower()
    if not q:
        return False
    has_table = any(h in q for h in _TABLE_REQUEST_HINTS)
    has_scalar = any(h in q for h in _SCALAR_REQUEST_HINTS)
    if has_table:
        return True
    if has_scalar:
        return False
    return False


def make_agent_planner_node(deps: GraphDeps):
    def planner(state: AgentState) -> dict:
        logger.info("node=agent_planner action=start")
        mode = str(state.get("planning_mode") or "auto").strip().lower()
        if mode == "classic" or not deps.settings.planner_enabled:
            return {}
        reg = deps.llm_registry
        if reg is None:
            return {}

        user_q = effective_user_question(
            state.get("messages"), state.get("normalized_user_question")
        )
        md_ctx, refs = build_planner_md_context(
            user_q,
            max_chars=int(deps.settings.planner_max_md_chars),
            enabled=bool(deps.settings.planner_md_context_enabled),
        )
        prompt = _planner_prompt(state, md_context=md_ctx)
        try:
            out = reg.get("planner").structured_predict(
                [SystemMessage(content=_PLANNER_SYSTEM), HumanMessage(content=prompt)],
                AgentPlannerOutput,
                json_output_contract=_PLANNER_CONTRACT,
            )
        except Exception:
            logger.warning(
                "agent_planner structured_predict failed; fallback to classify_intent",
                exc_info=True,
            )
            return {}

        intent = _intent_from_planner(out)
        conf = float(out.confidence or 0.0)
        min_conf = float(deps.settings.planner_confidence_threshold)
        patch: dict[str, object] = {
            **emit_progress(state, "agent_planner"),
            "planner_strategy": out.strategy,
            "planner_reason": (out.reason or "").strip() or None,
            "planner_confidence": conf,
            "planner_doc_refs": refs or None,
        }
        if intent and (mode == "planner" or conf >= min_conf):
            patch["intent"] = intent
            patch["route_source"] = "planner"
            if out.strategy == "data_table":
                selected_mode = normalize_interaction_mode(state.get("interaction_mode"))
                if selected_mode == "data_table" or _wants_table_view(user_q):
                    patch["show_query_table"] = True
            emit_agent_trace(
                logger,
                deps.settings,
                agent="agent_planner",
                phase="Planner override",
                detail=(
                    f"strategy={out.strategy} intent={intent} confidence={conf:.2f} "
                    f"mode={mode} refs={refs}"
                ),
            )
            return patch

        emit_agent_trace(
            logger,
            deps.settings,
            agent="agent_planner",
            phase="Planner observe (defer)",
            detail=(
                f"strategy={out.strategy} confidence={conf:.2f} min_conf={min_conf:.2f} "
                f"mode={mode} refs={refs}"
            ),
        )
        return patch

    return planner
