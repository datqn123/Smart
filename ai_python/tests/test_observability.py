from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_turn_metrics_has_cost_latency_retry() -> None:
    from app.harness.observability import TraceRecorder

    recorder = TraceRecorder(intent="data_query")
    recorder.record_step(step=1, tool="sql_query", ok=True, tokens=100, cost_usd=0.01, latency_ms=12.5)
    recorder.record_replan()
    metrics = recorder.finalize()

    assert metrics.tokens == 100
    assert metrics.cost_usd == 0.01
    assert metrics.latency_ms == 12.5
    assert metrics.replans == 1


def test_audit_warns_on_budget_hit() -> None:
    from app.harness.observability import TraceRecorder

    recorder = TraceRecorder(intent="data_query")
    recorder.record_budget_hit("cost")

    assert recorder.finalize().budget_hit == "cost"


def test_metrics_grouped_by_intent() -> None:
    from app.harness.observability import TurnMetrics, aggregate_metrics

    grouped = aggregate_metrics(
        [
            TurnMetrics(intent="data_query", steps=1, replans=0, hitl=False, tokens=10, cost_usd=0.1, latency_ms=10),
            TurnMetrics(intent="data_query", steps=1, replans=0, hitl=False, tokens=10, cost_usd=0.1, latency_ms=30),
            TurnMetrics(intent="chat", steps=1, replans=0, hitl=False, tokens=5, cost_usd=0.01, latency_ms=3),
        ]
    )

    assert grouped["data_query"]["p50_latency_ms"] == 20
    assert grouped["data_query"]["p95_latency_ms"] == 30
    assert grouped["chat"]["p50_latency_ms"] == 3


def test_eval_golden_offline_passes_subset() -> None:
    script = Path(__file__).resolve().parents[1] / "scripts" / "eval_golden.py"

    result = subprocess.run(
        [sys.executable, str(script), "--offline", "--min-pass", "0.8"],
        cwd=script.parents[1],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "pass_rate" in result.stdout


def test_eval_detects_regression() -> None:
    script = Path(__file__).resolve().parents[1] / "scripts" / "eval_golden.py"

    result = subprocess.run(
        [sys.executable, str(script), "--offline", "--simulate-regression", "--min-pass", "0.8"],
        cwd=script.parents[1],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
