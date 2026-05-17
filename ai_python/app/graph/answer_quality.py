"""Answer quality gate — heuristic check + optional LLM enrich."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from dataclasses import dataclass, field
from app.graph.answer_fallbacks import get_fallback_template
from app.graph.deps import GraphDeps
from app.prompts.load import load_agent_prompt

logger = logging.getLogger(__name__)

_GUIDANCE_KEYWORDS = ("bạn có thể", "hãy thử", "ví dụ", "gợi ý")
_NO_DATA_PATTERNS = (
    "không có dữ liệu",
    "không tìm thấy",
    "không có thông tin",
    "hiện tại không",
)


@dataclass(frozen=True)
class ScenarioProfile:
    min_chars: int = 80
    require_guidance: bool = False
    check_no_data_patterns: bool = False
    skip_quality: bool = False
    enrich_allowed: bool = True


SCENARIO_PROFILES: dict[str, ScenarioProfile] = {
    "chat": ScenarioProfile(min_chars=80, require_guidance=False),
    "sql_summary": ScenarioProfile(min_chars=180),
    "sql_empty": ScenarioProfile(
        min_chars=200,
        require_guidance=True,
        check_no_data_patterns=True,
    ),
    "sql_error": ScenarioProfile(min_chars=150, require_guidance=True),
    "domain_reject": ScenarioProfile(min_chars=150, require_guidance=True),
    "domain_clarify": ScenarioProfile(skip_quality=True),
    "chart_success": ScenarioProfile(min_chars=40),
    "chart_review": ScenarioProfile(min_chars=120, require_guidance=True),
    "chart_fail": ScenarioProfile(min_chars=120, require_guidance=True),
    "draft_confirm": ScenarioProfile(min_chars=60, require_guidance=True),
    "sql_clarify": ScenarioProfile(skip_quality=True),
    "draft_clarify": ScenarioProfile(skip_quality=True),
}

DEFAULT_FALLBACK_BY_SCENARIO: dict[str, str] = {
    "sql_empty": "sql_empty_vi",
    "sql_error": "sql_error_vi",
    "chart_fail": "chart_fail_vi",
    "domain_reject": "domain_reject_stub_vi",
}


@dataclass(frozen=True)
class QualityContext:
    node_name: str
    scenario: str
    skip_quality: bool = False
    has_query_result: bool | None = None
    user_question: str | None = None
    enrich_allowed: bool = True
    fallback_template_id: str | None = None
    query_result: dict | None = None


@dataclass
class QualityVerdict:
    passed: bool
    issues: list[str] = field(default_factory=list)
    enrichment_hints: list[str] = field(default_factory=list)


_FABRICATION_PHRASES = (
    "bao gồm",
    "gồm các",
    "các mặt hàng như",
    "sản phẩm như",
    "như **",
)


def _rows_are_aggregate_only(qr: dict | None) -> bool:
    """True when every non-null cell in rows is numeric (scalar / SUM / COUNT)."""
    if not isinstance(qr, dict):
        return False
    rows = qr.get("rows")
    if not isinstance(rows, list) or not rows:
        return False
    for row in rows:
        if not isinstance(row, dict):
            return False
        for val in row.values():
            if val is None:
                continue
            if isinstance(val, bool):
                return False
            if isinstance(val, (int, float)):
                continue
            if isinstance(val, str):
                stripped = val.strip()
                if not stripped:
                    continue
                try:
                    float(stripped.replace(",", ""))
                except ValueError:
                    return False
            elif str(val).strip():
                return False
    return True


def _answer_fabricates_entities(answer: str, qr: dict | None) -> bool:
    """Detect product names / examples when SQL rows only contain aggregates."""
    if not _rows_are_aggregate_only(qr):
        return False
    low = answer.lower()
    return any(p in low for p in _FABRICATION_PHRASES)


def _answer_reflects_query_rows(answer: str, qr: dict | None) -> bool:
    """True if answer contains at least one substantive value from rows (codes, numbers)."""
    if not isinstance(qr, dict):
        return True
    rows = qr.get("rows")
    if not isinstance(rows, list) or not rows:
        return True
    norm_ans = _norm_for_row_match(answer)
    for row in rows[:8]:
        if not isinstance(row, dict):
            continue
        for val in row.values():
            if val is None:
                continue
            if isinstance(val, (int, float)) and not isinstance(val, bool):
                if str(int(round(float(val)))) in norm_ans:
                    return True
            text = str(val).strip()
            if len(text) >= 2 and _norm_for_row_match(text) in norm_ans:
                return True
    return False


def _norm_for_row_match(text: str) -> str:
    return text.lower().replace(",", "").replace(".", "").replace(" ", "").replace("-", "")


def _profile_for(ctx: QualityContext) -> ScenarioProfile:
    base = SCENARIO_PROFILES.get(ctx.scenario, ScenarioProfile())
    if ctx.skip_quality:
        return ScenarioProfile(skip_quality=True)
    return base


def check_answer_quality(answer: str, *, ctx: QualityContext) -> QualityVerdict:
    profile = _profile_for(ctx)
    if profile.skip_quality:
        return QualityVerdict(passed=True)

    issues: list[str] = []
    hints: list[str] = []
    clean = answer.strip()
    n = len(clean)

    min_chars = profile.min_chars
    if (
        ctx.scenario == "sql_summary"
        and ctx.query_result
        and _rows_are_aggregate_only(ctx.query_result)
    ):
        min_chars = min(min_chars, 60)

    if n < min_chars:
        issues.append(f"Answer too short ({n} < {min_chars})")
        hints.append(
            "Add brief business context and a follow-up suggestion — "
            "do not invent product names or line items not in the query result"
        )

    if profile.check_no_data_patterns and any(p in clean.lower() for p in _NO_DATA_PATTERNS):
        if n < profile.min_chars:
            issues.append("Short 'no data' response — should suggest alternatives")
            hints.append("Suggest what the user CAN ask; give 3 example questions")

    if (
        ctx.has_query_result is True
        and ctx.scenario == "sql_summary"
        and any(p in clean.lower() for p in _NO_DATA_PATTERNS)
    ):
        issues.append("Claims 'no data' but SQL returned rows — use values from rows")
        hints.append(
            "If a numeric field is null, explain NULL/uncomputable; if it is a number, state it with formatting"
        )

    if (
        ctx.has_query_result is True
        and ctx.scenario == "sql_summary"
        and ctx.query_result
        and not _answer_reflects_query_rows(clean, ctx.query_result)
    ):
        issues.append("Answer omits concrete values from SQL rows (codes, amounts, names)")
        hints.append(
            "Quote receipt_code/SKU and numeric amounts exactly as in the query result rows"
        )

    if (
        ctx.has_query_result is True
        and ctx.scenario == "sql_summary"
        and ctx.query_result
        and _answer_fabricates_entities(clean, ctx.query_result)
    ):
        issues.append("Answer invents product or entity names not present in query rows")
        hints.append(
            "For aggregate-only results: state the number only; suggest follow-up questions "
            "without listing example product names"
        )

    need_guidance = profile.require_guidance or (
        ctx.has_query_result is False and ctx.scenario in ("sql_empty", "sql_error")
    )
    if need_guidance and not any(kw in clean.lower() for kw in _GUIDANCE_KEYWORDS):
        issues.append("Missing actionable guidance")
        hints.append("Add phrases like «Bạn có thể thử…» with 2–3 concrete examples")

    return QualityVerdict(passed=len(issues) == 0, issues=issues, enrichment_hints=hints)


def _truncate(answer: str, max_chars: int) -> str:
    if max_chars <= 0 or len(answer) <= max_chars:
        return answer
    return answer[: max_chars - 1].rstrip() + "…"


def _fill_prompt_template(
    template: str,
    *,
    previous_answer: str,
    issues: list[str],
    hints: list[str],
    user_question: str | None,
    scenario: str,
) -> str:
    return (
        template.replace("{previous_answer}", previous_answer)
        .replace("{issues}", "\n".join(f"- {i}" for i in issues) or "(none)")
        .replace("{hints}", "\n".join(f"- {h}" for h in hints) or "(none)")
        .replace("{user_question}", (user_question or "").strip() or "(not provided)")
        .replace("{scenario}", scenario)
    )


def _invoke_enrich_llm(
    deps: GraphDeps,
    *,
    previous_answer: str,
    verdict: QualityVerdict,
    ctx: QualityContext,
) -> str | None:
    reg = deps.llm_registry
    if reg is None or not ctx.enrich_allowed:
        return None
    system_tpl = load_agent_prompt("answer_enrich")
    system = _fill_prompt_template(
        system_tpl,
        previous_answer=previous_answer,
        issues=verdict.issues,
        hints=verdict.enrichment_hints,
        user_question=ctx.user_question,
        scenario=ctx.scenario,
    )
    user = "Rewrite and expand the previous answer following the system rules."
    timeout = float(deps.settings.answer_enrich_timeout_sec)

    def _call() -> str:
        return reg.get("chat").invoke_text(user, system=system)

    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(_call)
            return future.result(timeout=timeout)
    except FuturesTimeoutError:
        logger.warning(
            "answer_enrich timeout after %ss node=%s scenario=%s",
            timeout,
            ctx.node_name,
            ctx.scenario,
        )
    except Exception:
        logger.warning(
            "answer_enrich failed node=%s scenario=%s",
            ctx.node_name,
            ctx.scenario,
            exc_info=True,
        )
    return None


def enforce_answer_quality(
    answer: str,
    *,
    ctx: QualityContext,
    deps: GraphDeps,
    max_enrich_attempts: int = 1,
) -> str:
    """Run quality gate; optionally enrich once via LLM ``chat`` role."""
    if not deps.settings.answer_quality_enabled:
        return _truncate(answer.strip(), deps.settings.answer_quality_max_chars)

    profile = _profile_for(ctx)
    if profile.skip_quality:
        return _truncate(answer.strip(), deps.settings.answer_quality_max_chars)

    current = answer.strip()
    fallback_id = ctx.fallback_template_id or DEFAULT_FALLBACK_BY_SCENARIO.get(ctx.scenario)
    enriched_once: str | None = None

    for attempt in range(max_enrich_attempts + 1):
        verdict = check_answer_quality(current, ctx=ctx)
        if verdict.passed:
            break
        if attempt >= max_enrich_attempts:
            break
        if not profile.enrich_allowed or not ctx.enrich_allowed:
            break

        enriched = _invoke_enrich_llm(deps, previous_answer=current, verdict=verdict, ctx=ctx)
        if enriched and enriched.strip():
            candidate = enriched.strip()
            if _answer_fabricates_entities(candidate, ctx.query_result):
                logger.warning(
                    "answer_enrich rejected fabricated entities node=%s scenario=%s",
                    ctx.node_name,
                    ctx.scenario,
                )
                break
            enriched_once = candidate
            current = candidate
        else:
            tpl = get_fallback_template(fallback_id)
            if tpl:
                current = tpl
            break

        emit_quality_trace(
            deps,
            ctx=ctx,
            phase="answer_enrich",
            detail=f"attempt={attempt + 1} chars={len(current)}",
        )

    if not check_answer_quality(current, ctx=ctx).passed:
        tpl = get_fallback_template(fallback_id)
        if tpl and len(current) < len(tpl):
            current = tpl
        elif enriched_once:
            current = enriched_once

    emit_quality_trace(
        deps,
        ctx=ctx,
        phase="answer_quality_done",
        detail=(
            f"chars={len(current)} passed={check_answer_quality(current, ctx=ctx).passed} "
            f"scenario={ctx.scenario}"
        ),
    )
    return _truncate(current, deps.settings.answer_quality_max_chars)


def finalize_answer(
    answer: str,
    *,
    deps: GraphDeps,
    node_name: str,
    scenario: str,
    user_question: str | None = None,
    has_query_result: bool | None = None,
    fallback_template_id: str | None = None,
    skip_quality: bool = False,
    enrich_allowed: bool = True,
    query_result: dict | None = None,
) -> str:
    ctx = QualityContext(
        node_name=node_name,
        scenario=scenario,
        user_question=user_question,
        has_query_result=has_query_result,
        fallback_template_id=fallback_template_id,
        skip_quality=skip_quality,
        enrich_allowed=enrich_allowed,
        query_result=query_result,
    )
    return enforce_answer_quality(answer, ctx=ctx, deps=deps)


def emit_quality_trace(
    deps: GraphDeps,
    *,
    ctx: QualityContext,
    phase: str,
    detail: str,
) -> None:
    from app.graph.agent_trace import emit_agent_trace

    emit_agent_trace(
        logger,
        deps.settings,
        agent=ctx.node_name,
        phase=phase,
        detail=detail[:1200],
    )
