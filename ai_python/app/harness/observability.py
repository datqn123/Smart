"""Trace and metrics helpers for harness observability."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import median


@dataclass
class TurnMetrics:
    intent: str
    steps: int
    replans: int
    hitl: bool
    tokens: int
    cost_usd: float
    latency_ms: float
    budget_hit: str | None = None


class TraceRecorder:
    def __init__(self, *, intent: str) -> None:
        self._intent = intent
        self._steps = 0
        self._replans = 0
        self._hitl = False
        self._tokens = 0
        self._cost = 0.0
        self._latency = 0.0
        self._budget_hit: str | None = None

    def record_step(
        self,
        *,
        step: int,
        tool: str,
        ok: bool,
        tokens: int,
        cost_usd: float,
        latency_ms: float,
    ) -> None:
        _ = tool, ok
        self._steps = max(self._steps, int(step))
        self._tokens += int(tokens or 0)
        self._cost += float(cost_usd or 0.0)
        self._latency += float(latency_ms or 0.0)

    def record_replan(self) -> None:
        self._replans += 1

    def record_hitl(self) -> None:
        self._hitl = True

    def record_budget_hit(self, kind: str) -> None:
        self._budget_hit = kind

    def finalize(self) -> TurnMetrics:
        return TurnMetrics(
            intent=self._intent,
            steps=self._steps,
            replans=self._replans,
            hitl=self._hitl,
            tokens=self._tokens,
            cost_usd=self._cost,
            latency_ms=self._latency,
            budget_hit=self._budget_hit,
        )


def aggregate_metrics(metrics: list[TurnMetrics]) -> dict[str, dict[str, float]]:
    grouped: dict[str, list[TurnMetrics]] = {}
    for item in metrics:
        grouped.setdefault(item.intent, []).append(item)
    out: dict[str, dict[str, float]] = {}
    for intent, rows in grouped.items():
        latencies = sorted(row.latency_ms for row in rows)
        p95_idx = max(0, int(len(latencies) * 0.95 + 0.999) - 1)
        out[intent] = {
            "p50_latency_ms": float(median(latencies)),
            "p95_latency_ms": float(latencies[p95_idx]),
            "avg_cost_usd": sum(row.cost_usd for row in rows) / len(rows),
        }
    return out
