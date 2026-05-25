"""Presentation helpers for assistant text shown in chat (no extra LLM by default)."""

from __future__ import annotations

import re


def format_display_for_chat_ui(text: str) -> str:
    """Normalise order-list formatting and insert line breaks for chat bubbles.

    Fixes common LLM output quirks:
    - ``ĐơnSO`` glued tokens  →  ``Đơn SO``
    - ``-Đơn`` missing space  →  ``- Đơn``
    - Inline items without newlines  →  each item on its own line
    """
    t = (text or "").strip()
    if not t:
        return t

    # --- Phase 1: normalise token gluing / spacing ---
    # "ĐơnSO" or "Đơn   SO" → "Đơn SO"
    t = re.sub(r"\bĐơn\s*SO\b", "Đơn SO", t)
    # "-Đơn" or "- Đơn" (inconsistent) → "- Đơn"
    t = re.sub(r"-\s*Đơn\b", "- Đơn", t)

    # --- Phase 2: insert line breaks before list items ---
    # "…đ- Đơn SO-…" or "…đ -Đơn SO-…" → newline before "- Đơn SO"
    t = re.sub(r"(?<!\n)\s*-\s*(?=Đơn SO\b)", "\n\n- ", t)
    # "… được bán: - Đơn hàng …" → break after colon/semicolon before first bullet
    t = re.sub(r"([:;])\s+-\s+", r"\1\n\n- ", t)
    # Subsequent "…4.000đ - Đơn hàng …" (no newline yet)
    t = re.sub(r"(?<!\n)\s+-\s+(?=Đơn hàng)", "\n\n- ", t)
    t = re.sub(r"(?<!\n)\s+-\s+(?=đơn hàng)", "\n\n- ", t)
    t = re.sub(r"(?<!\n)\s+-\s+(?=SO-\d)", "\n\n- ", t)
    return t.strip()

