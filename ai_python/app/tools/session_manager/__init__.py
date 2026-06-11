from __future__ import annotations
import json
import logging
from typing import Literal
from pydantic import BaseModel, ValidationError, field_validator
from app.config.llm_client import ToolCallError
from app.graph.state import SessionState
from app.harness.think_log import think
from app.registry.args import CommonArgs
from app.registry.registry import (get_args_model, is_dispatchable, load_skill,
                                   render_api_tools)

log = logging.getLogger(__name__)

Action = Literal["call_tool", "retry_tool", "request_clarification", "finish"]


class Decision(BaseModel):
    """Ngon ngu noi bo cua orchestrator — dung tu tool_call cua SM,
    KHONG con la format output LLM."""
    action: Action
    tool_name: str | None = None
    reasoning: str
    message: str | None = None
    resolved_require: str | None = None   # SM viet lai cau hoi noi tiep tu-du-nghia

    @field_validator("tool_name")
    @classmethod
    def _tool_dispatchable(cls, v, info):
        if info.data.get("action") in ("call_tool", "retry_tool"):
            if not v or not is_dispatchable(v):
                raise ValueError(f"tool_name khong hop le/khong dispatch duoc: {v!r}")
        return v


_PROMPT = ("{skill}\n\n{memory}raw_require: {raw_require}\n"
           "history: {history}\nlast_result: {last}\n\n"
           "Chon va goi DUNG 1 tool cho buoc tiep theo.")


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


def _derive_action(state: SessionState, tool_name: str) -> str:
    """Goi lai tool ma ket qua gan nhat cua chinh no KHONG dat = retry —
    model khong con phai tu khai 'retry_tool', orchestrator van dem retry cap.
    Quet nguoc bo qua entry khong mang ket qua (vd retry_capped) de cap
    khong bi reset."""
    for entry in reversed(state["history"]):
        if entry.get("tool") == tool_name and "valid" in entry:
            return "retry_tool" if entry["valid"] is False else "call_tool"
    return "call_tool"


def _to_decision(name: str, args: CommonArgs, state: SessionState) -> Decision:
    if name == "finish":
        return Decision(action="finish", reasoning=args.reasoning,
                        message=args.message, resolved_require=args.resolved_require)
    if name == "request_clarification":
        return Decision(action="request_clarification", reasoning=args.reasoning,
                        message=args.message, resolved_require=args.resolved_require)
    resolved = args.resolved_require or getattr(args, "require", None)
    return Decision(action=_derive_action(state, name), tool_name=name,
                    reasoning=args.reasoning, resolved_require=resolved)


def analyze(state: SessionState, *, llm, memory_context: dict | None = None) -> Decision:
    """SM doc LAI skill.md moi lan phan tich (fact-sm-reanalyze), chon hanh dong
    bang native tool-calling (tool_choice=required), role 'sm'."""
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
    user = _PROMPT.format(skill=skill, memory=_memory_blocks(memory_context),
                          raw_require=state["raw_require"],
                          history=json.dumps(state["history"], ensure_ascii=False)[:4000],
                          last=json.dumps(last, ensure_ascii=False))
    tools = render_api_tools()
    last_err = None
    for attempt in range(2):
        try:
            name, raw_args = llm.complete_tool_select(system=skill, user=user,
                                                      tools=tools, role="sm")
            args = get_args_model(name).model_validate_json(raw_args)
        except (ToolCallError, KeyError, ValidationError, ValueError) as exc:
            last_err = exc
            log.warning("SM tool-select failed attempt=%d err=%s", attempt + 1, exc)
            user += (f"\n\n[Loi attempt truoc: {exc}. Goi dung 1 tool trong "
                     "danh sach voi args dung schema.]")
            continue
        decision = _to_decision(name, args, state)
        log.info("SM decision action=%s tool=%s reasoning=%.120s",
                 decision.action, decision.tool_name, decision.reasoning)
        think("SM", "suy nghi: %s", decision.reasoning)
        if decision.resolved_require:
            think("SM", 'hieu lai yeu cau thanh: "%.150s"', decision.resolved_require)
        if decision.action in ("call_tool", "retry_tool"):
            think("SM", "-> quyet dinh: %s %s",
                  "goi tool" if decision.action == "call_tool" else "thu lai tool",
                  decision.tool_name)
        elif decision.action == "request_clarification":
            think("SM", '-> quyet dinh: can hoi lai user — "%.150s"', decision.message)
        else:
            think("SM", "-> quyet dinh: %s", decision.action)
        return decision
    log.error("SM falling back to finish after 2 attempts last_err=%s", last_err)
    think("SM", "-> bo cuoc: 2 lan khong doc duoc quyet dinh tu LLM, ket thuc an toan")
    return Decision(action="finish", reasoning=f"SM decision loi: {last_err}",
                    message="Xin loi, he thong chua xu ly duoc yeu cau luc nay.")
