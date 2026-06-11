from __future__ import annotations
import logging
from typing import Any, AsyncGenerator
from app.harness.turn_context import TurnContext
from app.tools.session_manager import analyze
from app.graph.dispatcher import dispatch, DispatchError
from app.graph.state import new_session_state

log = logging.getLogger(__name__)


def _event(type_: str, data: dict) -> dict:
    return {"type": type_, "data": data}


def _build_upstream(state, forward_data: dict) -> dict:
    """SM chi ra lay data tu tool nao ('from'); orchestrator dung payload.

    Luon merge TAT CA tool_results lam nen, roi overlay source SM chi dinh
    len tren (key cua source thang khi trung). Truoc day 'from' thay the
    toan bo upstream → SM forward tu data_validator lam answer_composer
    mat rows cua sql_execute va tra loi 'khong co du lieu'."""
    merged: dict[str, Any] = {}
    for out in state["tool_results"].values():
        if isinstance(out, dict):
            merged.update(out)
    src = forward_data.get("from")
    if src and src in state["tool_results"]:
        merged.update(state["tool_results"][src])
    return merged


async def run_session(ctx: TurnContext, *, llm_sm, llm_tool, deps: dict,
                      max_steps: int = 6, retry_cap: int = 2,
                      resume_snapshot: dict | None = None,
                      pending_store=None,
                      memory_context: dict | None = None
                      ) -> AsyncGenerator[dict, None]:
    state = new_session_state(raw_require=ctx.raw_require, thread_id=ctx.thread_id)
    validator_passed = False
    log.info("[%s] session start user=%s raw_require=%.120s resume=%s",
             ctx.thread_id, ctx.user_id, ctx.raw_require, resume_snapshot is not None)

    if resume_snapshot is not None:
        # Khoi phuc cau hoi goc — ctx.raw_require luc resume chi la cau tra loi
        # clarify; memory write path can luot gop "cau goc + bo sung" (spec).
        state["raw_require"] = resume_snapshot.get("raw_require") or state["raw_require"]
        state["tool_results"] = resume_snapshot.get("tool_results", {})
        state["history"] = resume_snapshot.get("history", [])
        state["retry_counts"] = resume_snapshot.get("retry_counts", {})
        validator_passed = False  # re-validate sau clarify
        log.info("[%s] HITL resume history_len=%d", ctx.thread_id, len(state["history"]))
    if ctx.clarification_response:
        state["raw_require"] = (f"{state['raw_require']}\n"
                                f"[Bo sung tu user]: {ctx.clarification_response}")
        log.info("[%s] clarification appended: %.120s", ctx.thread_id, ctx.clarification_response)

    while state["status"] == "running" and state["step_count"] < max_steps:
        decision = analyze(state, llm=llm_sm, memory_context=memory_context)
        state["last_decision"] = decision.model_dump()
        action = decision.action

        if action == "finish":
            if state["final_answer"] is None:
                state["final_answer"] = decision.message or ""
            state["status"] = "finished"
            break

        if action == "request_clarification":
            state["pending_clarification"] = {"message": decision.message or ""}
            state["status"] = "paused"
            log.info("[%s] HITL clarify: %.200s", ctx.thread_id, decision.message)
            if pending_store is not None:
                await pending_store.save(ctx.thread_id, {
                    "raw_require": ctx.raw_require, "thread_id": ctx.thread_id,
                    "tool_results": state["tool_results"], "history": state["history"],
                    "retry_counts": state["retry_counts"],
                    "pending_clarification": state["pending_clarification"]})
                log.debug("[%s] HITL snapshot saved", ctx.thread_id)
            yield _event("clarify", {"message": decision.message or "",
                                     "thread_id": ctx.thread_id})
            break

        if action == "replan":
            log.info("[%s] replan step=%d reasoning=%.120s",
                     ctx.thread_id, state["step_count"], decision.reasoning)
            state["history"].append({"action": "replan", "reasoning": decision.reasoning})
            state["step_count"] += 1
            continue

        tool = decision.tool_name
        if action == "retry_tool":
            current_retries = state["retry_counts"].get(tool, 0)
            if current_retries >= retry_cap:
                log.warning("[%s] retry_cap reached tool=%s cap=%d",
                            ctx.thread_id, tool, retry_cap)
                state["history"].append({"action": "retry_capped", "tool": tool})
                state["step_count"] += 1
                continue
            state["retry_counts"][tool] = current_retries + 1
            log.info("[%s] retry tool=%s attempt=%d/%d",
                     ctx.thread_id, tool, current_retries + 1, retry_cap)

        require = decision.resolved_require or state["raw_require"]
        if decision.resolved_require:
            log.info("[%s] resolved_require: %.120s", ctx.thread_id, decision.resolved_require)
        upstream = _build_upstream(state, decision.forward_data)
        log.info("[%s] step=%d dispatch tool=%s", ctx.thread_id, state["step_count"], tool)
        yield _event("tool_call", {"tool_name": tool, "reasoning": decision.reasoning})
        try:
            result = dispatch(tool, raw_require=require, upstream_data=upstream,
                              llm=llm_tool, deps=deps, validator_passed=validator_passed,
                              memory_summary=(memory_context or {}).get("summary"))
        except DispatchError as exc:
            log.warning("[%s] dispatch error tool=%s: %s", ctx.thread_id, tool, exc)
            state["history"].append({"action": "dispatch_error", "tool": tool, "error": str(exc)})
            state["step_count"] += 1
            continue

        output = result["output"] or {}
        state["tool_results"][tool] = output
        state["history"].append({"action": action, "tool": tool, "valid": result["valid"],
                                 "output": output})
        if result["valid"]:
            log.info("[%s] tool=%s valid=True", ctx.thread_id, tool)
        else:
            log.warning("[%s] tool=%s valid=False err=%s",
                        ctx.thread_id, tool, result["validation_error"])
        yield _event("tool_result", {"tool_name": tool, "valid": result["valid"],
                                     "validation_error": result["validation_error"]})

        if tool == "data_validator":
            validator_passed = (output.get("verdict") == "pass")
            log.info("[%s] data_validator verdict=%s reason=%.100s",
                     ctx.thread_id, output.get("verdict"), output.get("reason", ""))
        if tool == "answer_composer" and result["valid"]:
            state["final_answer"] = output.get("answer", "")
            state["status"] = "finished"
            break

        state["step_count"] += 1

    if state["status"] == "running" and state["step_count"] >= max_steps:
        state["status"] = "aborted"
        log.warning("[%s] step limit reached max_steps=%d, aborting", ctx.thread_id, max_steps)
        yield _event("error", {"message": "Da cham gioi han so buoc, dung an toan."})
        return

    if state["status"] == "finished":
        answer = state["final_answer"] or ""
        log.info("[%s] session finished answer_len=%d", ctx.thread_id, len(answer))
        yield _event("answer", {"text": answer})
        yield _event("done", {"thread_id": ctx.thread_id,
                              "raw_require": state["raw_require"]})
