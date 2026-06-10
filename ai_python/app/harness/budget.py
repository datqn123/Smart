"""Turn-level budget guardrails for the harness loop."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class BudgetExceeded(Exception):
    def __init__(self, kind: str) -> None:
        super().__init__(kind)
        self.kind = kind


@dataclass
class TurnBudget:
    max_steps: int
    token_budget: int = 0
    cost_budget_usd: float = 0.0
    wallclock_timeout_s: float = 30.0
    _started: float = 0.0
    used_tokens: int = 0
    used_cost_usd: float = 0.0

    def start(self) -> None:
        self._started = time.monotonic()

    def add_usage(self, tokens: int, cost_usd: float) -> None:
        self.used_tokens += max(0, int(tokens or 0))
        self.used_cost_usd += max(0.0, float(cost_usd or 0.0))

    def check(self, step: int) -> None:
        _ = step
        if self.token_budget and self.used_tokens >= self.token_budget:
            logger.warning("budget_exceeded kind=%s used=%s limit=%s step=%s", "token", self.used_tokens, self.token_budget, step)
            raise BudgetExceeded("token")
        if self.cost_budget_usd and self.used_cost_usd >= self.cost_budget_usd:
            logger.warning("budget_exceeded kind=%s used=%s limit=%s step=%s", "cost", self.used_cost_usd, self.cost_budget_usd, step)
            raise BudgetExceeded("cost")
        if self.wallclock_timeout_s and self._started:
            elapsed = time.monotonic() - self._started
            if elapsed >= self.wallclock_timeout_s:
                logger.warning("budget_exceeded kind=%s used=%s limit=%s step=%s", "wallclock", elapsed, self.wallclock_timeout_s, step)
                raise BudgetExceeded("wallclock")
