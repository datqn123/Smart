"""Compact long conversation threads: summarize old turns and prune checkpoint messages."""

from __future__ import annotations

import logging

from langchain_core.messages import RemoveMessage

from app.graph.agent_trace import emit_agent_trace
from app.graph.deps import GraphDeps
from app.graph.message_utils import (
    count_human_turns,
    messages_to_transcript,
    split_messages_for_compaction,
)
from app.graph.state import AgentState
from app.prompts.load import load_agent_prompt

logger = logging.getLogger(__name__)

_CONTEXT_COMPACT_SYSTEM = load_agent_prompt("context_compact")


def _build_compact_prompt(
    *,
    to_summarize: list,
    existing_summary: str | None,
    summary_lines: int,
) -> str:
    parts: list[str] = []
    if existing_summary and existing_summary.strip():
        parts.append(f"Tóm tắt hiện có:\n{existing_summary.strip()}")
    transcript = messages_to_transcript(to_summarize)
    if transcript:
        parts.append(f"Hội thoại cần gộp thêm:\n{transcript}")
    parts.append(f"Viết đúng {summary_lines} dòng tiếng Việt (mỗi dòng một ý).")
    return "\n\n".join(parts)


def _system_with_line_count(summary_lines: int) -> str:
    return _CONTEXT_COMPACT_SYSTEM.replace("{summary_lines}", str(summary_lines))


def make_context_compact_node(deps: GraphDeps):
    def context_compact(state: AgentState) -> dict:
        settings = deps.settings
        if not settings.context_compact_enabled:
            return {}

        messages = list(state.get("messages") or [])
        max_turns = int(settings.context_compact_max_turns)
        keep_last = int(settings.context_compact_keep_last_turns)
        summary_lines = int(settings.context_compact_summary_lines)
        human_turns = count_human_turns(messages)

        if human_turns <= max_turns:
            return {}

        to_summarize, to_keep = split_messages_for_compaction(
            messages, keep_last_turns=keep_last
        )
        if not to_summarize:
            return {}

        existing = (state.get("conversation_summary") or "").strip() or None
        gen = int(state.get("context_compact_generation") or 0)
        reg = deps.llm_registry

        if reg is None:
            logger.warning(
                "context_compact: no LLM registry — skipping prune (human_turns=%s)",
                human_turns,
            )
            return {}

        user_prompt = _build_compact_prompt(
            to_summarize=to_summarize,
            existing_summary=existing,
            summary_lines=summary_lines,
        )
        system = _system_with_line_count(summary_lines)

        try:
            new_summary = reg.get("summarize").invoke_text(
                user_prompt, system=system
            )
            new_summary = (new_summary or "").strip()
            if not new_summary:
                logger.warning("context_compact: empty LLM summary — skipping prune")
                return {}
        except Exception:
            logger.exception("context_compact: LLM failed — skipping prune")
            return {}

        remove_ids: list[str] = []
        for m in to_summarize:
            mid = getattr(m, "id", None)
            if mid:
                remove_ids.append(str(mid))

        if not remove_ids:
            logger.warning(
                "context_compact: no message ids to remove — summary stored only"
            )
            emit_agent_trace(
                logger,
                settings,
                agent="context_compact",
                phase="Tóm tắt (không prune — thiếu id)",
                detail=f"human_turns={human_turns} gen={gen + 1}",
            )
            return {
                "conversation_summary": new_summary,
                "context_compact_generation": gen + 1,
            }

        preview = new_summary if len(new_summary) <= 600 else new_summary[:600] + "…"
        emit_agent_trace(
            logger,
            settings,
            agent="context_compact",
            phase="Tóm tắt + prune checkpoint",
            detail=(
                f"human_turns={human_turns} removed={len(remove_ids)} "
                f"kept_turns={keep_last} gen={gen + 1}\n{preview}"
            ),
        )
        return {
            "conversation_summary": new_summary,
            "context_compact_generation": gen + 1,
            "messages": [RemoveMessage(id=mid) for mid in remove_ids],
        }

    return context_compact
