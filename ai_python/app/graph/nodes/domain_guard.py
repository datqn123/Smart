"""ERP domain guard — scope, terminology, clarify before execute (Task112)."""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.graph.agent_trace import emit_agent_trace
from app.graph.answer_quality import finalize_answer
from app.graph.deps import GraphDeps
from app.graph.erp_guide.load_index import format_index_for_prompt, load_domain_index
from app.graph.erp_guide.retrieve import detect_heuristic_misnomers, retrieve_guide_snippets
from app.graph.erp_guide.rewrite import resolve_suggested_rewrite
from app.graph.erp_guide.slot_resolution import (
    default_normalized_for_proceed,
    expand_elliptical_follow_up,
    filter_resolved_missing_slots,
    has_blocking_issues,
    should_proceed_after_repeated_clarify,
    strip_catalog_draft_misnomers,
    strip_noop_issues,
)
from app.graph.message_utils import (
    count_identical_human_messages,
    format_dialog_tail_for_sql,
    latest_human_question,
)
from app.graph.progress import emit_progress
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


def _dialog_context_for_guard(state: AgentState, settings) -> str:
    return format_dialog_tail_for_sql(
        state.get("messages"),
        max_messages=min(8, int(settings.sql_dialog_tail_max_messages)),
        max_chars=min(1800, int(settings.sql_dialog_tail_max_chars)),
        summary=state.get("conversation_summary"),
    )


def _apply_hard_rules(
    out: DomainGuardOutput,
    heuristic_blocks: list[DomainIssue],
    *,
    user_question: str,
    dialog_tail: str = "",
    messages: list | None = None,
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

    deduped = strip_catalog_draft_misnomers(deduped, user_question)

    missing = filter_resolved_missing_slots(
        user_question, list(out.missing_slots or []), dialog_tail=dialog_tail
    )
    blocking = has_blocking_issues(deduped)
    expanded_q = expand_elliptical_follow_up(user_question, dialog_tail)
    repeat_turns = count_identical_human_messages(messages, user_question)

    action = out.action
    if not out.in_scope and any(i.type == "out_of_scope" for i in deduped):
        action = "reject"
    elif blocking:
        action = "clarify"
    elif missing:
        # Only optional slots left (e.g. order status) — proceed; SQL can count all retail orders
        action = "proceed"
    elif action == "clarify" and not blocking and not missing:
        # Terminology-only clarify with no remaining blockers (e.g. stripped catalog names)
        action = "proceed"
    elif deduped and action == "proceed" and blocking:
        action = "clarify"
    elif (
        action == "clarify"
        and not blocking
        and expanded_q.strip() != user_question.strip()
    ):
        # Follow-up inherits channel/time from prior turn — do not re-ask «loại đơn nào»
        action = "proceed"

    if (
        action == "clarify"
        and out.in_scope
        and should_proceed_after_repeated_clarify(
            question=user_question,
            matched_modules=out.matched_modules,
            identical_human_turns=repeat_turns,
        )
        and not any(
            i.severity == "block" and i.type not in ("term_mismatch",) for i in deduped
        )
    ):
        action = "proceed"
        blocking = False

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
        base_q = expanded_q if expanded_q.strip() != user_question.strip() else user_question
        if not normalized or normalized.lower() == user_question.strip().lower():
            normalized = default_normalized_for_proceed(base_q)
        else:
            normalized = default_normalized_for_proceed(normalized)
        if expanded_q.strip() != user_question.strip() and expanded_q.lower() not in normalized.lower():
            normalized = default_normalized_for_proceed(expanded_q)

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
                **emit_progress(state, "domain_guard"),
                "domain_guard_action": "proceed",
                "normalized_user_question": q,
            }

        question = latest_human_question(state.get("messages"))
        dialog_tail = _dialog_context_for_guard(state, deps.settings)
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
            hi = strip_catalog_draft_misnomers(heuristic_issues, question)
            if hi and has_blocking_issues(hi):
                return _pack_clarify(
                    state,
                    question,
                    hi,
                    snippets,
                    index=index,
                )
            return {
                **emit_progress(state, "domain_guard"),
                "domain_guard_action": "proceed",
                "normalized_user_question": default_normalized_for_proceed(question),
                "domain_context": {"guide_snippets": snippets},
            }

        dialog_block = (
            f"## Recent conversation (resolve đơn đó / từng đơn / tháng đó from here)\n{dialog_tail}\n\n"
            if dialog_tail
            else ""
        )
        prompt = (
            f"## Domain index\n{index_text}\n\n"
            f"## Guide snippets\n{snippet_block or '(none)'}\n\n"
            f"{dialog_block}"
            f"## User message (current turn)\n{question}\n"
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
            hi = strip_catalog_draft_misnomers(heuristic_issues, question)
            if hi and has_blocking_issues(hi):
                return _pack_clarify(
                    state,
                    question,
                    hi,
                    snippets,
                    index=index,
                )
            return {
                **emit_progress(state, "domain_guard"),
                "domain_guard_action": "proceed",
                "normalized_user_question": default_normalized_for_proceed(question),
                "domain_context": {"guide_snippets": snippets},
            }

        final = _apply_hard_rules(
            out,
            heuristic_issues,
            user_question=question,
            dialog_tail=dialog_tail,
            messages=state.get("messages"),
        )
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
            return _pack_reject(state, final, deps)
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
            **emit_progress(state, "domain_guard"),
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


def _pack_reject(state: AgentState, final: DomainGuardOutput, deps: GraphDeps) -> dict:
    msg = final.assistant_message or "Yêu cầu ngoài phạm vi Mini ERP."
    msg = finalize_answer(
        msg,
        deps=deps,
        node_name="domain_guard",
        scenario="domain_reject",
        fallback_template_id="domain_reject_stub_vi",
    )
    return {
        **emit_progress(state, "domain_guard"),
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
        **emit_progress(state, "domain_guard"),
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
