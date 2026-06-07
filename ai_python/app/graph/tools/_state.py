"""State helpers for harness tool adapters."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage

from app.graph.feedback import empty_feedback
from app.graph.state import default_initial_state, fresh_turn_overlay
from app.harness.tool_registry import TurnContext


def build_tool_state(question: str, ctx: TurnContext, settings: Any) -> dict[str, Any]:
    state = dict(default_initial_state())
    state.update(fresh_turn_overlay())
    state["messages"] = [HumanMessage(content=question)]
    state["correlation_id"] = ctx.correlation_id
    state["tenant_id"] = ctx.tenant_id
    state["user_id"] = ctx.user_id
    state["thread_id"] = ctx.thread_id
    state["schema_version"] = ctx.schema_version
    state["spring_bearer_token"] = ctx.bearer_token
    state["sql_attempt_count"] = 0
    state["sql_repair_max_attempts"] = int(getattr(settings, "sql_repair_max_attempts", 3))
    state["validation_feedback"] = empty_feedback()
    return state


def build_tool_config(ctx: TurnContext) -> dict[str, Any]:
    return {
        "configurable": {
            "correlation_id": ctx.correlation_id,
            "tenant_id": ctx.tenant_id,
            "user_id": ctx.user_id,
            "thread_id": ctx.thread_id,
            "schema_version": ctx.schema_version,
        },
    }
