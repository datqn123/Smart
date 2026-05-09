from __future__ import annotations

from app.smart_erp_mcp.chat_reply import format_turn_as_chat_text


def test_format_turn_includes_intent() -> None:
    turn = {
        "mode": "inline",
        "steps": [
            {
                "tool": "intent_analyze",
                "result": {
                    "ok": True,
                    "primary_intent": "rag_qa",
                    "entities": {},
                    "risk_flags": [],
                    "hitl_required": False,
                    "suggested_tools": ["rag_retrieve"],
                },
            },
            {
                "tool": "rag_retrieve",
                "result": {
                    "ok": True,
                    "chunks": [{"id": "1", "text": "Chunk about ERP.", "source": {}, "score": 0.9}],
                    "rag_stale_warning": "stub",
                },
            },
        ],
    }
    text = format_turn_as_chat_text(turn)
    assert "rag_qa" not in text  # intent is hidden by default (debug only)
    assert "Chunk" in text or "ERP" in text


def test_format_refusal() -> None:
    turn = {
        "steps": [
            {
                "tool": "intent_analyze",
                "result": {
                    "ok": True,
                    "primary_intent": "refusal",
                    "entities": {},
                    "risk_flags": [],
                    "hitl_required": False,
                    "suggested_tools": [],
                },
            }
        ]
    }
    assert "không thể" in format_turn_as_chat_text(turn).lower()
