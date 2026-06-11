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


def sse_frontend(event_name: str, data: str) -> str:
    """SSE frame cho Spring relay / browser: event: + data: line(s).
    data phai la string (plain text hoac JSON-encoded string).

    Data nhieu dong PHAI tach thanh nhieu 'data:' line theo spec SSE —
    EventSource phia client tu noi lai bang '\\n'. Truoc day nhet nguyen
    chuoi sau 1 'data:' lam moi dong sau dong dau bi parser SSE bo qua
    (answer danh sach bi cat cut o dong dau tien)."""
    lines = data.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    body = "\n".join(f"data: {ln}" for ln in lines)
    return f"event: {event_name}\n{body}\n\n"
