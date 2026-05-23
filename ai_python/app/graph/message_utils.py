"""Helpers for picking the *current* user question from LangGraph message lists."""

from __future__ import annotations

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

_SUMMARY_PREFIX = "[Tóm tắt các lượt trước]"


def strip_embedded_chat_transcript(text: str) -> str:
    """
    If the client put a mini transcript inside one HumanMessage (User / Assistant turns),
    keep only the latest user segment so SQL + summarize do not repeat prior answers.
    Conservative: only mutates when assistant-role markers are present.
    """
    t = (text or "").strip()
    if not t:
        return t
    low = t.lower()
    if "\nassistant:" not in low and "trợ lý:" not in t and "\nai:" not in low:
        return t
    user_markers = ("\nuser:", "\nngười dùng:", "\nhuman:", "\n[user]")
    last_at = -1
    last_needle = ""
    for needle in user_markers:
        i = low.rfind(needle)
        if i > last_at:
            last_at = i
            last_needle = needle
    if last_at == -1:
        lines = [x.strip() for x in t.splitlines() if x.strip()]
        return lines[-1] if lines else t
    rest = t[last_at + len(last_needle) :].strip()
    return rest if rest else t


def effective_user_question(
    messages: list[BaseMessage] | None,
    normalized: str | None = None,
) -> str:
    """Prefer domain-guard normalized question when present."""
    if normalized and str(normalized).strip():
        return str(normalized).strip()
    return latest_human_question(messages)


def latest_human_question(messages: list[BaseMessage] | None) -> str:
    """Last non-empty HumanMessage content, with optional transcript stripping."""
    for m in reversed(messages or []):
        if isinstance(m, HumanMessage):
            c = getattr(m, "content", "")
            if c is None:
                continue
            s = str(c).strip()
            if s:
                return strip_embedded_chat_transcript(s)
    for m in reversed(messages or []):
        c = getattr(m, "content", "")
        if c:
            return strip_embedded_chat_transcript(str(c).strip())
    return ""


def count_human_turns(messages: list[BaseMessage] | None) -> int:
    """Count non-empty HumanMessage entries (one per user turn)."""
    n = 0
    for m in messages or []:
        if isinstance(m, HumanMessage):
            c = getattr(m, "content", "")
            if c is not None and str(c).strip():
                n += 1
    return n


def count_identical_human_messages(
    messages: list[BaseMessage] | None,
    question: str,
) -> int:
    """How many user turns match the current question text (case-insensitive)."""
    target = strip_embedded_chat_transcript(question).strip().lower()
    if not target:
        return 0
    n = 0
    for m in messages or []:
        if isinstance(m, HumanMessage):
            c = getattr(m, "content", "")
            if c is None:
                continue
            s = strip_embedded_chat_transcript(str(c)).strip().lower()
            if s == target:
                n += 1
    return n


def _human_turn_start_indices(messages: list[BaseMessage]) -> list[int]:
    """Indices of each non-empty HumanMessage in order."""
    out: list[int] = []
    for i, m in enumerate(messages):
        if isinstance(m, HumanMessage):
            c = getattr(m, "content", "")
            if c is not None and str(c).strip():
                out.append(i)
    return out


def split_messages_for_compaction(
    messages: list[BaseMessage] | None,
    *,
    keep_last_turns: int,
) -> tuple[list[BaseMessage], list[BaseMessage]]:
    """
    Split messages into (to_summarize, to_keep) by user-turn boundary.
    Keeps the last ``keep_last_turns`` human turns and all messages after the
    first kept human index.
    """
    raw = list(messages or [])
    if not raw or keep_last_turns <= 0:
        return [], raw
    human_starts = _human_turn_start_indices(raw)
    if len(human_starts) <= keep_last_turns:
        return [], raw
    keep_from = human_starts[-keep_last_turns]
    return raw[:keep_from], raw[keep_from:]


def format_summary_prefix(summary: str | None) -> str:
    s = (summary or "").strip()
    if not s:
        return ""
    return f"{_SUMMARY_PREFIX}\n{s}"


def messages_to_transcript(messages: list[BaseMessage]) -> str:
    """Labeled User/Assistant text for compaction input."""
    parts: list[str] = []
    for m in messages:
        c = getattr(m, "content", None)
        if c is None:
            continue
        text = str(c).strip().replace("\r\n", "\n")
        if not text:
            continue
        if isinstance(m, HumanMessage):
            parts.append(f"User: {text}")
        elif isinstance(m, AIMessage):
            parts.append(f"Assistant: {text}")
    return "\n\n".join(parts).strip()


def messages_for_llm_context(
    messages: list[BaseMessage] | None,
    summary: str | None,
    *,
    tail_cap: int = 24,
) -> list[BaseMessage]:
    """Recent message tail with optional summary as leading SystemMessage."""
    raw = list(messages or [])
    tail = raw[-tail_cap:] if len(raw) > tail_cap else list(raw)
    prefix = format_summary_prefix(summary)
    if prefix:
        return [SystemMessage(content=prefix), *tail]
    return tail


def build_chat_context_text(
    messages: list[BaseMessage] | None,
    summary: str | None,
    *,
    tail_messages: int = 20,
    max_chars: int = 4000,
) -> str:
    """Plain text block for chat_normal (summary + recent turns)."""
    parts: list[str] = []
    prefix = format_summary_prefix(summary)
    if prefix:
        parts.append(prefix)
    for m in (messages or [])[-tail_messages:]:
        c = getattr(m, "content", "")
        if c:
            parts.append(str(c))
    text = "\n".join(parts)
    if len(text) > max_chars:
        return text[-max_chars:]
    return text


def format_dialog_tail_for_sql(
    messages: list[BaseMessage] | None,
    *,
    max_messages: int = 12,
    max_chars: int = 2000,
    summary: str | None = None,
) -> str:
    """
    Last N Human/AI turns as labeled text for gen_sql / summarize (pronoun resolution).
    max_messages or max_chars 0 disables (returns empty).
    """
    if max_messages <= 0 or max_chars <= 0:
        return ""
    raw = list(messages or [])
    if not raw:
        return ""
    tail = raw[-max_messages:]
    parts: list[str] = []
    for m in tail:
        c = getattr(m, "content", None)
        if c is None:
            continue
        text = str(c).strip().replace("\r\n", "\n")
        if not text:
            continue
        if isinstance(m, HumanMessage):
            parts.append(f"User: {text}")
        elif isinstance(m, AIMessage):
            parts.append(f"Assistant: {text}")
    block = "\n\n".join(parts).strip()
    if not block and not summary:
        return ""
    prefix = format_summary_prefix(summary)
    if prefix and block:
        combined = f"{prefix}\n\n{block}"
    elif prefix:
        combined = prefix
    else:
        combined = block
    if len(combined) <= max_chars:
        return combined
    return combined[-max_chars:].lstrip()
