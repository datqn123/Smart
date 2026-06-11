from __future__ import annotations
import json
import logging
from typing import Any, Literal
from pydantic import BaseModel, field_validator
from app.graph.state import SessionState
from app.harness.think_log import think
from app.registry.registry import load_skill, is_dispatchable

log = logging.getLogger(__name__)

Action = Literal["call_tool", "retry_tool", "replan", "request_clarification", "finish"]


class Decision(BaseModel):
    action: Action
    tool_name: str | None = None
    forward_data: dict[str, Any] = {}
    reasoning: str
    message: str | None = None
    resolved_require: str | None = None   # SM viet lai cau hoi noi tiep tu-du-nghia

    @field_validator("tool_name")
    @classmethod
    def _tool_registered(cls, v, info):
        action = info.data.get("action")
        if action in ("call_tool", "retry_tool"):
            if not v or not is_dispatchable(v):
                raise ValueError(f"tool_name khong hop le/khong dang ky: {v!r}")
        return v


_PROMPT = ("{skill}\n\n{memory}raw_require: {raw_require}\n"
           "history: {history}\nlast_result: {last}\n\n"
           "Tra ve DUY NHAT JSON theo Output schema.")


def _memory_blocks(memory_context) -> str:
    """SM la noi duy nhat thay du cac luot verbatim (spec) — tool chi nhan summary."""
    if not memory_context:
        return ""
    parts = []
    if memory_context.get("summary"):
        parts.append(f"[Tom tat hoi thoai cu]: {memory_context['summary']}")
    if memory_context.get("turns"):
        parts.append("[Cac luot gan nhat]: "
                     + json.dumps(memory_context["turns"], ensure_ascii=False)[:6000])
    return "\n".join(parts) + "\n" if parts else ""


def _coerce_json(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.strip("`"); raw = raw[raw.find("{"):]
    return json.loads(raw)


def analyze(state: SessionState, *, llm, memory_context: dict | None = None) -> Decision:
    """SM doc LAI skill.md moi lan phan tich (fact-sm-reanalyze) va dung
    role 'sm' (Qwen, temperature thap — R5). Reparse co bound 2 lan."""
    skill = load_skill("session_manager")
    last = state["history"][-1] if state["history"] else None
    log.debug("SM analyze step=%d history_len=%d raw_require=%.100s",
              state["step_count"], len(state["history"]), state["raw_require"])
    if last:
        think("SM", 'doc lai tinh hinh: yeu cau "%.100s", da qua %d buoc, '
              "buoc gan nhat: %s%s",
              state["raw_require"], len(state["history"]),
              last.get("tool") or last.get("action"),
              "" if last.get("valid", True) else " (KHONG dat)")
    else:
        think("SM", 'nhan yeu cau moi: "%.100s" — chua co buoc nao, '
              "bat dau phan tich xem can tool gi", state["raw_require"])
    user = _PROMPT.format(skill=skill,
                          memory=_memory_blocks(memory_context),
                          raw_require=state["raw_require"],
                          history=json.dumps(state["history"], ensure_ascii=False)[:4000],
                          last=json.dumps(last, ensure_ascii=False))
    last_err = None
    for attempt in range(2):
        raw = llm.complete(system=skill, user=user, role="sm")
        try:
            decision = Decision.model_validate(_coerce_json(raw))
            log.info("SM decision action=%s tool=%s reasoning=%.120s",
                     decision.action, decision.tool_name, decision.reasoning)
            think("SM", "suy nghi: %s", decision.reasoning)
            if decision.resolved_require:
                think("SM", 'hieu lai cau hoi noi tiep thanh: "%.150s"',
                      decision.resolved_require)
            if decision.action in ("call_tool", "retry_tool"):
                think("SM", "-> quyet dinh: %s %s",
                      "goi tool" if decision.action == "call_tool" else "thu lai tool",
                      decision.tool_name)
            elif decision.action == "request_clarification":
                think("SM", '-> quyet dinh: can hoi lai user — "%.150s"', decision.message)
            else:
                think("SM", "-> quyet dinh: %s", decision.action)
            return decision
        except Exception as exc:
            last_err = exc
            log.warning("SM JSON parse failed attempt=%d err=%s raw_preview=%.200s",
                        attempt + 1, exc, raw[:200])
            user += f"\n\n[Loi parse JSON truoc: {exc}. Tra lai dung JSON schema.]"
    log.error("SM falling back to finish after 2 parse attempts last_err=%s", last_err)
    think("SM", "-> bo cuoc: 2 lan khong doc duoc quyet dinh tu LLM, ket thuc an toan")
    return Decision(action="finish", reasoning=f"SM decision loi parse: {last_err}",
                    message="Xin loi, he thong chua xu ly duoc yeu cau luc nay.")
