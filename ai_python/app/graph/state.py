from __future__ import annotations
from typing import Any, TypedDict


class ToolState(TypedDict):
    tool_name: str
    raw_require: str
    upstream_data: dict[str, Any]
    memory_summary: str | None       # summary hoi thoai cu (None = khong co)
    skill: str                       # noi dung skill.md da nap o node load_skill
    output: dict[str, Any] | None    # ket qua execute
    valid: bool                      # verdict cua self_validate
    validation_error: str | None
    attempt: int                     # so lan da chay (tang moi lan build/retry)


class SessionState(TypedDict):
    raw_require: str
    thread_id: str
    history: list[dict[str, Any]]            # nhat ky decision + tool result
    tool_results: dict[str, dict[str, Any]]  # tool_name -> output gan nhat
    retry_counts: dict[str, int]             # tool_name -> so lan retry da dung
    step_count: int
    status: str                              # running|finished|paused|aborted
    final_answer: str | None
    pending_clarification: dict[str, Any] | None
    last_decision: dict[str, Any] | None


def new_tool_state(*, tool_name: str, raw_require: str,
                   upstream_data: dict | None = None,
                   memory_summary: str | None = None) -> ToolState:
    return ToolState(tool_name=tool_name, raw_require=raw_require,
                     upstream_data=upstream_data or {},
                     memory_summary=memory_summary, skill="", output=None,
                     valid=False, validation_error=None, attempt=0)


def new_session_state(*, raw_require: str, thread_id: str) -> SessionState:
    return SessionState(raw_require=raw_require, thread_id=thread_id, history=[],
                        tool_results={}, retry_counts={}, step_count=0,
                        status="running", final_answer=None,
                        pending_clarification=None, last_decision=None)
