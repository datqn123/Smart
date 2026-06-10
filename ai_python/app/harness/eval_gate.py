"""K12 golden-eval route gate (SRS-006 ER-1, NFR-11, FR-9.4).

Computes tool-route accuracy over golden eval cases and decides whether the v3
rollout flag may be enabled. A case passes only when every ``required_tools`` was
called and no ``must_not_tools`` was called.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


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
    result = EvalCaseResult(
        case_id=case.case_id,
        passed=not missing and not forbidden,
        missing_required=missing,
        called_forbidden=forbidden,
    )
    logger.info("eval_case case=%s passed=%s missing=%s forbidden=%s", result.case_id, result.passed, result.missing_required, result.called_forbidden)
    return result


def route_accuracy(results: list[EvalCaseResult]) -> float:
    if not results:
        return 0.0
    passed = sum(1 for r in results if r.passed)
    accuracy = passed / len(results)
    logger.info("eval_accuracy accuracy=%.2f total=%s passed=%s", accuracy, len(results), passed)
    return accuracy


def v3_rollout_allowed(accuracy: float, threshold: float) -> bool:
    """FR-9.4 / NFR-11: block rollout when route accuracy is below threshold."""
    allowed = accuracy >= threshold
    logger.info("eval_rollout allowed=%s accuracy=%.2f threshold=%.2f", allowed, accuracy, threshold)
    return allowed
