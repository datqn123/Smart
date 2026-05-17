"""ERP domain guard — scope, terminology, clarify before execute (Task112)."""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.graph.agent_trace import emit_agent_trace
from app.graph.deps import GraphDeps
from app.graph.erp_guide.load_index import format_index_for_prompt, load_domain_index
from app.graph.erp_guide.retrieve import detect_heuristic_misnomers, retrieve_guide_snippets
from app.graph.erp_guide.rewrite import resolve_suggested_rewrite
from app.graph.erp_guide.slot_resolution import (
    default_normalized_for_proceed,
    filter_resolved_missing_slots,
    has_blocking_issues,
    strip_noop_issues,
)
from app.graph.message_utils import latest_human_question
from app.graph.state import AgentState
from app.llm.schemas import DomainGuardOutput, DomainIssue
from app.prompts.load import load_agent_json_contract, load_agent_prompt

logger = logging.getLogger(__name__)

_DOMAIN_GUARD_SYSTEM = load_agent_prompt("domain_guard")
_DOMAIN_GUARD_CONTRACT = load_agent_json_contract("domain_guard") or ""

_CLARIFY_BUBBLE_INTRO = (
    "Cần làm rõ thêm — xem chi tiết và câu đề xuất trong khung bên dưới."
)


def _issues_from_heuristic(hits: list[dict[str, Any]]) -> list[DomainIssue]:
    return [
        DomainIssue(
            type=h.get("type", "term_mismatch"),  # type: ignore[arg-type]
            user_text=str(h.get("user_text", "")),
            canonical_vi=h.get("canonical_vi"),
            canonical_en=h.get("canonical_en"),
            guide_ref=str(h.get("guide_ref")) if h.get("guide_ref") else None,
            severity=h.get("severity", "block"),  # type: ignore[arg-type]
        )
        for h in hits
    ]


def _short_clarify_intro(issues: list[DomainIssue]) -> str:
    parts: list[str] = []
    for i in issues:
        if i.type == "term_mismatch" and i.canonical_vi and (i.user_text or "").strip().lower() != (
            i.canonical_vi or ""
        ).strip().lower():
            parts.append(
                f"Trong Mini ERP, «{i.user_text}» nên dùng «{i.canonical_vi}»."
            )
    if parts:
        return " ".join(parts[:2]) + " " + _CLARIFY_BUBBLE_INTRO
    return _CLARIFY_BUBBLE_INTRO


def _apply_hard_rules(
    out: DomainGuardOutput,
    heuristic_blocks: list[DomainIssue],
    *,
    user_question: str,
) -> DomainGuardOutput:
    issues = strip_noop_issues(list(out.issues) + [i for i in heuristic_blocks if i.user_text])
    seen = set()
    deduped: list[DomainIssue] = []
    for i in issues:
        key = (i.type, i.user_text, i.canonical_vi or "")
        if key in seen:
            continue
        seen.add(key)
        deduped.append(i)

    missing = filter_resolved_missing_slots(user_question, list(out.missing_slots or []))
    blocking = has_blocking_issues(deduped)

    action = out.action
    if not out.in_scope and any(i.type == "out_of_scope" for i in deduped):
        action = "reject"
    elif blocking:
        action = "clarify"
    elif missing:
        # Only optional slots left (e.g. order status) — proceed; SQL can count all retail orders
        action = "proceed"
    elif deduped and action == "proceed" and blocking:
        action = "clarify"

    questions = list(out.clarification_questions)[:3]
    if action == "clarify":
        assistant = _short_clarify_intro(deduped)
    elif action == "reject":
        assistant = out.assistant_message or (
            "Yêu cầu này nằm ngoài phạm vi Mini ERP hiện tại. "
            "Tôi chỉ hỗ trợ các nghiệp vụ trong hệ thống (kho, sản phẩm, đơn hàng, tài chính, AI nội bộ)."
        )
    else:
        assistant = out.assistant_message or ""

    normalized = (out.normalized_question or "").strip()
    if action == "proceed":
        if not normalized or normalized.lower() == user_question.strip().lower():
            normalized = default_normalized_for_proceed(user_question)
        else:
            normalized = default_normalized_for_proceed(normalized)

    return DomainGuardOutput(
        action=action,
        in_scope=out.in_scope,
        matched_modules=out.matched_modules,
        coverage=out.coverage if action != "proceed" or not missing else "full",
        issues=deduped,
        missing_slots=missing,
        normalized_question=normalized,
        clarification_questions=questions if action == "clarify" else [],
        assistant_message=assistant,
    )


def make_domain_guard_node(deps: GraphDeps):
    def domain_guard(state: AgentState) -> dict:
        logger.info("node=domain_guard action=start")
        if not deps.settings.erp_domain_guard_enabled:
            q = latest_human_question(state.get("messages"))
            return {
                "domain_guard_action": "proceed",
                "normalized_user_question": q,
            }

        question = latest_human_question(state.get("messages"))
        data_dir = deps.settings.erp_guide_data_dir
        index = load_domain_index(data_dir)
        index_text = format_index_for_prompt(index)
        snippets = retrieve_guide_snippets(
            question,
            data_dir=data_dir,
            max_chunks=deps.settings.erp_guide_retrieve_max_chunks,
        )
        snippet_block = ""
        if snippets:
            parts = [f"### Guide {s['guide_ref']} ({s['module_id']})\n{s['text'][:2800]}" for s in snippets]
            snippet_block = "\n\n".join(parts)

        heuristic_hits = detect_heuristic_misnomers(question, index)
        heuristic_issues = _issues_from_heuristic(heuristic_hits)

        reg = deps.llm_registry
        if reg is None:
            if heuristic_issues:
                return _pack_clarify(
                    state,
                    question,
                    heuristic_issues,
                    snippets,
                    index=index,
                )
            return {
                "domain_guard_action": "proceed",
                "normalized_user_question": default_normalized_for_proceed(question),
                "domain_context": {"guide_snippets": snippets},
            }

        prompt = (
            f"## Domain index\n{index_text}\n\n"
            f"## Guide snippets\n{snippet_block or '(none)'}\n\n"
            f"## User message\n{question}\n"
        )
        client = reg.get("domain_guard")
        try:
            out = client.structured_predict(
                [SystemMessage(content=_DOMAIN_GUARD_SYSTEM), HumanMessage(content=prompt)],
                DomainGuardOutput,
                json_output_contract=_DOMAIN_GUARD_CONTRACT,
            )
        except Exception:
            logger.warning("domain_guard structured_predict failed", exc_info=True)
            if heuristic_issues:
                return _pack_clarify(
                    state,
                    question,
                    heuristic_issues,
                    snippets,
                    index=index,
                )
            return {
                "domain_guard_action": "proceed",
                "normalized_user_question": default_normalized_for_proceed(question),
                "domain_context": {"guide_snippets": snippets},
            }

        final = _apply_hard_rules(out, heuristic_issues, user_question=question)
        emit_agent_trace(
            logger,
            deps.settings,
            agent="domain_guard",
            phase=f"Kết luận action={final.action}",
            detail=(
                f"in_scope={final.in_scope} modules={final.matched_modules} "
                f"issues={len(final.issues)} missing_slots={final.missing_slots}"
            ),
        )

        if final.action == "reject":
            return _pack_reject(final)
        if final.action == "clarify":
            return _pack_clarify(
                state,
                question,
                final.issues,
                snippets,
                questions=final.clarification_questions,
                matched_modules=final.matched_modules,
                llm_normalized=final.normalized_question,
                missing_slots=final.missing_slots,
                index=index,
            )

        normalized = final.normalized_question.strip() or default_normalized_for_proceed(question)
        return {
            "domain_guard_action": "proceed",
            "normalized_user_question": normalized,
            "domain_context": {
                "matched_modules": final.matched_modules,
                "coverage": final.coverage,
                "issues": [i.model_dump() for i in final.issues],
                "guide_snippets": snippets,
            },
        }

    return domain_guard


def _pack_reject(final: DomainGuardOutput) -> dict:
    msg = final.assistant_message or "Yêu cầu ngoài phạm vi Mini ERP."
    return {
        "domain_guard_action": "reject",
        "final_answer": msg,
        "messages": [AIMessage(content=msg)],
    }


def _pack_clarify(
    state: AgentState,
    question: str,
    issues: list[DomainIssue],
    snippets: list[dict[str, str]],
    *,
    questions: list[str] | None = None,
    matched_modules: list[str] | None = None,
    llm_normalized: str | None = None,
    missing_slots: list[str] | None = None,
    index: dict[str, Any] | None = None,
) -> dict:
    slots = list(missing_slots or [])
    suggested = resolve_suggested_rewrite(
        question,
        llm_normalized=llm_normalized,
        issues=issues,
        index=index,
        missing_slots=slots,
    )
    clarify_sse = {
        "questions": questions or [],
        "issues": [i.model_dump() for i in issues],
        "guideRefs": [s.get("guide_ref", "") for s in snippets],
        "originalQuestion": question,
        "suggestedRewrite": suggested,
        "suggestedNormalized": suggested,
        "matchedModules": matched_modules or [],
    }
    msg = _short_clarify_intro(issues)
    return {
        "domain_guard_action": "clarify",
        "domain_clarify_sse": clarify_sse,
        "final_answer": msg,
        "messages": [AIMessage(content=msg)],
    }


def route_after_domain_guard(state: AgentState) -> str:
    action = state.get("domain_guard_action") or "proceed"
    if action == "proceed":
        return "continue"
    return "stop"
