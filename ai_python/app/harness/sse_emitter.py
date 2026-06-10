from __future__ import annotations
import json


class SSEEvent(str):
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    CLARIFY = "clarify"      # HITL: frontend confirm UI tieu thu event nay
    ANSWER = "answer"        # token/doan cau tra loi cuoi
    DONE = "done"
    ERROR = "error"


def sse_format(event_type: str, data: dict) -> str:
    """SSE line. Boc duoi 1 key goc co dinh 'harness' de route trung gian
    khong flatten lam mat key payload (R6)."""
    body = json.dumps({"harness": {"type": event_type, "data": data}},
                      ensure_ascii=False)
    return f"data: {body}\n\n"
