from __future__ import annotations
from typing import Any, AsyncGenerator
from app.harness.turn_context import TurnContext
from app.tools.session_manager import analyze
from app.graph.dispatcher import dispatch, DispatchError
from app.graph.state import new_session_state


def _event(type_: str, data: dict) -> dict:
    return {"type": type_, "data": data}


def _build_upstream(state, forward_data: dict) -> dict:
    """SM chi ra lay data tu tool nao ('from'); orchestrator dung payload."""
    src = forward_data.get("from")
    if src and src in state["tool_results"]:
        return dict(state["tool_results"][src])
    merged: dict[str, Any] = {}
    for out in state["tool_results"].values():
        if isinstance(out, dict):
            merged.update(out)
    return merged


async def run_session(ctx: TurnContext, *, llm_sm, llm_tool, deps: dict,
                      max_steps: int = 6, retry_cap: int = 2
                      ) -> AsyncGenerator[dict, None]:
    state = new_session_state(raw_require=ctx.raw_require, thread_id=ctx.thread_id)
    validator_passed = False

    while state["status"] == "running" and state["step_count"] < max_steps:
        decision = analyze(state, llm=llm_sm)
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
            yield _event("clarify", {"message": decision.message or "",
                                     "thread_id": ctx.thread_id})
            break

        if action == "replan":
            state["history"].append({"action": "replan", "reasoning": decision.reasoning})
            state["step_count"] += 1
            continue

        tool = decision.tool_name
        if action == "retry_tool":
            if state["retry_counts"].get(tool, 0) >= retry_cap:
                state["history"].append({"action": "retry_capped", "tool": tool})
                state["step_count"] += 1
                continue
            state["retry_counts"][tool] = state["retry_counts"].get(tool, 0) + 1

        upstream = _build_upstream(state, decision.forward_data)
        yield _event("tool_call", {"tool_name": tool, "reasoning": decision.reasoning})
        try:
            result = dispatch(tool, raw_require=ctx.raw_require, upstream_data=upstream,
                              llm=llm_tool, deps=deps, validator_passed=validator_passed)
        except DispatchError as exc:
            state["history"].append({"action": "dispatch_error", "tool": tool, "error": str(exc)})
            state["step_count"] += 1
            continue

        output = result["output"] or {}
        state["tool_results"][tool] = output
        state["history"].append({"action": action, "tool": tool, "valid": result["valid"],
                                 "output": output})
        yield _event("tool_result", {"tool_name": tool, "valid": result["valid"],
                                     "validation_error": result["validation_error"]})

        if tool == "data_validator":
            validator_passed = (output.get("verdict") == "pass")
        if tool == "answer_composer" and result["valid"]:
            state["final_answer"] = output.get("answer", "")
            state["status"] = "finished"
            break

        state["step_count"] += 1

    if state["status"] == "running" and state["step_count"] >= max_steps:
        state["status"] = "aborted"
        yield _event("error", {"message": "Da cham gioi han so buoc, dung an toan."})
        return

    if state["status"] == "finished":
        yield _event("answer", {"text": state["final_answer"] or ""})
        yield _event("done", {"thread_id": ctx.thread_id})
