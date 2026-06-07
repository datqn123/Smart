"""K12 golden-eval route gate (SRS-006 ER-1, NFR-11, FR-9.4).

Computes tool-route accuracy over golden eval cases and decides whether the v3
rollout flag may be enabled. A case passes only when every ``required_tools`` was
called and no ``must_not_tools`` was called.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class EvalCase:
    case_id: str
    required_tools: tuple[str, ...] = ()
    must_not_tools: tuple[str, ...] = ()


@dataclass
class EvalCaseResult:
    case_id: str
    passed: bool
    missing_required: list[str] = field(default_factory=list)
    called_forbidden: list[str] = field(default_factory=list)


def evaluate_case(case: EvalCase, tools_called: list[str]) -> EvalCaseResult:
    called = set(tools_called)
    missing = [t for t in case.required_tools if t not in called]
    forbidden = [t for t in case.must_not_tools if t in called]
    return EvalCaseResult(
        case_id=case.case_id,
        passed=not missing and not forbidden,
        missing_required=missing,
        called_forbidden=forbidden,
    )


def route_accuracy(results: list[EvalCaseResult]) -> float:
    if not results:
        return 0.0
    passed = sum(1 for r in results if r.passed)
    return passed / len(results)


def v3_rollout_allowed(accuracy: float, threshold: float) -> bool:
    """FR-9.4 / NFR-11: block rollout when route accuracy is below threshold."""
    return accuracy >= threshold
