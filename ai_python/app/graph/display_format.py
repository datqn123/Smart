"""Presentation helpers for assistant text shown in chat (no extra LLM by default)."""

from __future__ import annotations

import re


def format_display_for_chat_ui(text: str) -> str:
    """Insert line breaks before common inline list patterns (e.g. multiple orders on one line).

    HTML chat bubbles collapse newlines unless CSS ``pre-line`` is used; this still helps when
    the model emits ``'...: - Item'`` or ``'...đ - Đơn hàng'`` on a single line.
    """
    t = (text or "").strip()
    if not t:
        return t
    # "… được bán: - Đơn hàng …" → break after colon/semicolon before first bullet
    t = re.sub(r"([:;])\s+-\s+", r"\1\n\n- ", t)
    # Subsequent "…4.000đ - Đơn hàng …" (no newline yet)
    t = re.sub(r"(?<!\n)\s+-\s+(?=Đơn hàng)", "\n\n- ", t)
    t = re.sub(r"(?<!\n)\s+-\s+(?=đơn hàng)", "\n\n- ", t)
    t = re.sub(r"(?<!\n)\s+-\s+(?=SO-\d)", "\n\n- ", t)
    return t.strip()
