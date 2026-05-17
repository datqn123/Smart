"""Prior-turn context for chart/SQL (checkpoint messages), without hardcoded metrics."""

from __future__ import annotations

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from app.graph.message_utils import format_summary_prefix


def format_prior_turns_for_chart(
    messages: list[BaseMessage] | None,
    *,
    max_turns: int = 2,
    max_chars: int = 2500,
    summary: str | None = None,
) -> str:
    """
    Extract recent User/Assistant pairs *before* the latest human message.
    Helps chart SQL stay consistent with a prior numeric answer in the thread.
    """
    if max_turns <= 0 or max_chars <= 0:
        return ""
    raw = list(messages or [])
    if len(raw) < 2:
        return ""

    # Find index of last human
    last_h_idx = -1
    for i in range(len(raw) - 1, -1, -1):
        if isinstance(raw[i], HumanMessage):
            c = str(getattr(raw[i], "content", "") or "").strip()
            if c:
                last_h_idx = i
                break
    if last_h_idx <= 0:
        return ""
    prior = raw[:last_h_idx]
    pairs: list[str] = []
    i = len(prior) - 1
    turns = 0
    while i >= 0 and turns < max_turns:
        if isinstance(prior[i], AIMessage):
            a_text = str(getattr(prior[i], "content", "") or "").strip()
            j = i - 1
            u_text = ""
            while j >= 0:
                if isinstance(prior[j], HumanMessage):
                    u_text = str(getattr(prior[j], "content", "") or "").strip()
                    break
                j -= 1
            if u_text or a_text:
                block = f"User: {u_text}\nAssistant: {a_text}".strip()
                pairs.insert(0, block)
                turns += 1
            i = j
        i -= 1
    block = "\n\n---\n\n".join(pairs).strip()
    prefix = format_summary_prefix(summary)
    if prefix and block:
        combined = f"{prefix}\n\n---\n\n{block}"
    elif prefix:
        combined = prefix
    else:
        combined = block
    if not combined:
        return ""
    if len(combined) <= max_chars:
        return combined
    return combined[-max_chars:].lstrip()
