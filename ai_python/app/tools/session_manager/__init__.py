from __future__ import annotations
import json
from typing import Any, Literal
from pydantic import BaseModel, field_validator
from app.graph.state import SessionState
from app.registry.registry import load_skill, render_tool_catalog, is_registered

Action = Literal["call_tool", "retry_tool", "replan", "request_clarification", "finish"]


class Decision(BaseModel):
    action: Action
    tool_name: str | None = None
    forward_data: dict[str, Any] = {}
    reasoning: str
    message: str | None = None

    @field_validator("tool_name")
    @classmethod
    def _tool_registered(cls, v, info):
        action = info.data.get("action")
        if action in ("call_tool", "retry_tool"):
            if not v or not is_registered(v):
                raise ValueError(f"tool_name khong hop le/khong dang ky: {v!r}")
        return v


_PROMPT = ("{skill}\n\n{catalog}\n\nraw_require: {raw_require}\n"
           "history: {history}\nlast_result: {last}\n\n"
           "Tra ve DUY NHAT JSON theo Output schema.")


def _coerce_json(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.strip("`"); raw = raw[raw.find("{"):]
    return json.loads(raw)


def analyze(state: SessionState, *, llm) -> Decision:
    """SM doc LAI skill.md moi lan phan tich (fact-sm-reanalyze) va dung
    role 'sm' (Qwen, temperature thap — R5). Reparse co bound 2 lan."""
    skill = load_skill("session_manager")
    last = state["history"][-1] if state["history"] else None
    user = _PROMPT.format(skill=skill, catalog=render_tool_catalog(),
                          raw_require=state["raw_require"],
                          history=json.dumps(state["history"], ensure_ascii=False)[:4000],
                          last=json.dumps(last, ensure_ascii=False))
    last_err = None
    for _ in range(2):
        raw = llm.complete(system=skill, user=user, role="sm")
        try:
            return Decision.model_validate(_coerce_json(raw))
        except Exception as exc:
            last_err = exc
            user += f"\n\n[Loi parse JSON truoc: {exc}. Tra lai dung JSON schema.]"
    return Decision(action="finish", reasoning=f"SM decision loi parse: {last_err}",
                    message="Xin loi, he thong chua xu ly duoc yeu cau luc nay.")
