"""Helpers for picking the *current* user question from LangGraph message lists."""

from __future__ import annotations

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage


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


def format_dialog_tail_for_sql(
    messages: list[BaseMessage] | None,
    *,
    max_messages: int = 12,
    max_chars: int = 2000,
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
    if not block:
        return ""
    if len(block) <= max_chars:
        return block
    return block[-max_chars:].lstrip()
