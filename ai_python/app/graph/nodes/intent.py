"""Intent routing node."""

from __future__ import annotations

import logging

from langchain_core.messages import BaseMessage, SystemMessage

from app.graph.agent_trace import emit_agent_trace
from app.graph.deps import GraphDeps
from app.graph.message_utils import (
    effective_user_question,
    latest_human_question,
    messages_for_llm_context,
)
from app.graph.interaction_mode import resolve_mode_override
from app.graph.progress import emit_progress
from app.graph.registry import normalize_intent
from app.graph.state import AgentState
from app.llm.schemas import IntentOutput
from app.prompts.load import load_agent_json_contract, load_agent_prompt

logger = logging.getLogger(__name__)

_INTENT_CLASSIFY_SYSTEM = load_agent_prompt("intent")
_INTENT_JSON_CONTRACT = load_agent_json_contract("intent") or ""

_INTENT_MESSAGE_TAIL = 24


def _messages_for_intent(state: AgentState) -> list[BaseMessage]:
    """System + recent turns; avoids dumping huge Pydantic schema on the model."""
    tail = messages_for_llm_context(
        state.get("messages"),
        state.get("conversation_summary"),
        tail_cap=_INTENT_MESSAGE_TAIL,
    )
    return [SystemMessage(content=_INTENT_CLASSIFY_SYSTEM), *tail]


def _user_question_snippet(state: AgentState, max_chars: int = 220) -> str:
    t = effective_user_question(
        state.get("messages"), state.get("normalized_user_question")
    ).replace("\n", " ").strip()
    if not t:
        return "(no user text)"
    if len(t) > max_chars:
        return t[:max_chars] + "…"
    return t


def make_intent_node(deps: GraphDeps):
    def intent(state: AgentState) -> dict:
        logger.info("node=intent action=start")
        clarification_ctx = state.get("clarification_applied_context")
        if isinstance(clarification_ctx, dict):
            clarify_kind = str(clarification_ctx.get("clarify_kind") or "")
            if clarify_kind == "data_followup_detail":
                emit_agent_trace(
                    logger,
                    deps.settings,
                    agent="intent",
                    phase="Override theo clarification continuation",
                    detail=(
                        f"clarify_kind={clarify_kind}\n"
                        f"intent=system_data_query\n"
                        f"câu_hỏi={_user_question_snippet(state)}"
                    ),
                )
                return {
                    **emit_progress(state, "classify_intent"),
                    "intent": "system_data_query",
                    "route_source": "clarification",
                }
        mode_patch = resolve_mode_override(state.get("interaction_mode"))
        if mode_patch is not None:
            normalized = str(mode_patch["intent"])
            emit_agent_trace(
                logger,
                deps.settings,
                agent="intent",
                phase="Override theo interaction_mode",
                detail=(
                    f"interaction_mode={state.get('interaction_mode')}\n"
                    f"intent={normalized}\n"
                    f"show_query_table={mode_patch.get('show_query_table')}\n"
                    f"câu_hỏi={_user_question_snippet(state)}"
                ),
            )
            return {
                **emit_progress(state, "classify_intent"),
                **mode_patch,
                "route_source": "interaction_mode",
            }
        planned_intent = state.get("intent")
        if (
            str(state.get("route_source") or "") == "planner"
            and isinstance(planned_intent, str)
            and planned_intent
        ):
            emit_agent_trace(
                logger,
                deps.settings,
                agent="intent",
                phase="Nhận route từ planner",
                detail=(
                    f"intent={planned_intent}\n"
                    f"strategy={state.get('planner_strategy')}\n"
                    f"câu_hỏi={_user_question_snippet(state)}"
                ),
            )
            return {
                **emit_progress(state, "classify_intent"),
                "intent": normalize_intent(planned_intent),
                "route_source": "planner",
            }
        reg = deps.llm_registry
        if reg is None:
            emit_agent_trace(
                logger,
                deps.settings,
                agent="intent",
                phase="Kết luận (stub, không gọi LLM)",
                detail="intent=general_chat",
            )
            return {
                **emit_progress(state, "classify_intent"),
                "intent": "general_chat",
                "route_source": "intent_auto",
            }
        messages = _messages_for_intent(state)
        client = reg.get("intent")
        try:
            out = client.structured_predict(
                messages,
                IntentOutput,
                json_output_contract=_INTENT_JSON_CONTRACT,
            )
            raw = out.intent
        except Exception:
            logger.warning("intent structured_predict failed; routing to general_chat", exc_info=True)
            emit_agent_trace(
                logger,
                deps.settings,
                agent="intent",
                phase="Lỗi LLM — fallback",
                detail="intent=general_chat",
            )
            return {
                **emit_progress(state, "classify_intent"),
                "intent": "general_chat",
                "route_source": "intent_auto",
            }
        normalized = normalize_intent(raw)
        emit_agent_trace(
            logger,
            deps.settings,
            agent="intent",
            phase="Suy luận định tuyến (JSON từ LLM)",
            detail=(
                f"intent={normalized}\n"
                f"raw_model_intent={raw}\n"
                f"câu_hỏi={_user_question_snippet(state)}"
            ),
        )
        return {
            **emit_progress(state, "classify_intent"),
            "intent": normalized,
            "route_source": "intent_auto",
        }

    return intent


def route_after_intent(state: AgentState) -> str:
    intent = state.get("intent") or "general_chat"
    if intent == "catalog_data_entry":
        return "catalog_draft_branch"
    if intent == "inventory_data_entry":
        return "inventory_draft_branch"
    if intent == "system_data_chart":
        return "agent_idea"
    if intent == "system_data_query":
        return "sql_branch"
    return "chat_normal"
