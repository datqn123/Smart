"""Tiered model routing for agentic subagents."""

from __future__ import annotations


WORK_MODEL_TIER = {
    "intent": "haiku",
    "compact": "haiku",
    "planner": "sonnet",
    "sql": "sonnet",
    "answer_composer": "sonnet",
}


class ModelRouter:
    def __init__(self, *, opt_escalate_replan_count: int = 2) -> None:
        self._escalate_at = int(opt_escalate_replan_count)

    def pick(self, work: str, *, replan_count: int = 0) -> str:
        if replan_count >= self._escalate_at:
            return "opus"
        return WORK_MODEL_TIER.get(work, "sonnet")
