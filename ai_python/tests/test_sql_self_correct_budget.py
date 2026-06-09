from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_sql_regen_within_budget() -> None:
    from app.graph.tools.sql_query import SelfCorrectingSqlRunner

    generated: list[str] = []

    async def gen(hint: str | None):
        sql = f"SELECT {len(generated)} AS v LIMIT 10"
        generated.append(sql)
        return sql

    reviews = iter([
        {"ok": False, "issues": ["forced fail"], "retry_hint": "fix"},
        {"ok": False, "issues": ["forced fail 2"], "retry_hint": "fix again"},
        {"ok": True, "issues": []},
    ])

    async def review(sql: str):
        return next(reviews)

    async def execute(sql: str):
        return [{"v": 1}]

    result = await SelfCorrectingSqlRunner(
        sql_regen_max=3,
        sql_empty_retry_max=2,
        generate=gen,
        review=review,
        execute=execute,
    ).run()

    assert result.ok is True
    assert result.regen_count == 2
    assert result.rows == [{"v": 1}]


@pytest.mark.asyncio
async def test_sql_empty_result_returns_immediately() -> None:
    from app.graph.tools.sql_query import SelfCorrectingSqlRunner

    executions = 0

    async def gen(hint: str | None):
        return "SELECT 1 AS v LIMIT 10"

    async def review(sql: str):
        return {"ok": True, "issues": []}

    async def execute(sql: str):
        nonlocal executions
        executions += 1
        return []

    result = await SelfCorrectingSqlRunner(
        sql_regen_max=3,
        sql_empty_retry_max=2,
        generate=gen,
        review=review,
        execute=execute,
    ).run()

    assert result.ok is True
    assert result.empty_retry_count == 0
    assert result.degraded is False
    assert result.warning == ""
    assert result.rows == []
    assert executions == 1


@pytest.mark.asyncio
async def test_sql_dedup_short_circuits() -> None:
    from app.graph.tools.sql_query import SelfCorrectingSqlRunner

    calls = 0

    async def gen(hint: str | None):
        return "SELECT * FROM missing LIMIT 10"

    async def review(sql: str):
        nonlocal calls
        calls += 1
        return {"ok": False, "issues": ["same issue"], "retry_hint": "same hint"}

    async def execute(sql: str):
        raise AssertionError("execute must not run when review fails")

    result = await SelfCorrectingSqlRunner(
        sql_regen_max=3,
        sql_empty_retry_max=2,
        generate=gen,
        review=review,
        execute=execute,
    ).run()

    assert calls == 2
    assert result.deduped is True
    assert result.degraded is True


@pytest.mark.asyncio
async def test_sql_empty_result_not_retried() -> None:
    from app.graph.tools.sql_query import SelfCorrectingSqlRunner

    async def gen(hint: str | None):
        return "SELECT 1 AS v LIMIT 10"

    async def review(sql: str):
        return {"ok": True, "issues": []}

    async def execute(sql: str):
        return []

    result = await SelfCorrectingSqlRunner(
        sql_regen_max=1,
        sql_empty_retry_max=1,
        generate=gen,
        review=review,
        execute=execute,
    ).run()

    assert result.ok is True
    assert result.degraded is False
    assert result.warning == ""
    assert result.empty_retry_count == 0


@pytest.mark.asyncio
async def test_sql_write_blocked_by_readonly() -> None:
    from app.graph.tools.sql_query import SelfCorrectingSqlRunner

    async def gen(hint: str | None):
        return "UPDATE products SET name = 'x'"

    async def review(sql: str):
        return {"ok": True, "issues": []}

    async def execute(sql: str):
        raise AssertionError("write SQL must be blocked before execute")

    result = await SelfCorrectingSqlRunner(
        sql_regen_max=1,
        sql_empty_retry_max=0,
        generate=gen,
        review=review,
        execute=execute,
    ).run()

    assert result.ok is False
    assert "read-only" in result.warning.lower()


@pytest.mark.asyncio
async def test_legit_empty_result_not_degraded():
    """SQL passed review but returns 0 rows legitimately — should return ok=True, degraded=False."""

    from app.graph.tools.sql_query import SelfCorrectingSqlRunner

    async def _gen(hint):
        return "SELECT name FROM products WHERE category_name ILIKE '%NonExistent%'"

    async def _review(sql):
        return {"ok": True, "issues": []}

    async def _execute(sql):
        return []

    runner = SelfCorrectingSqlRunner(
        sql_regen_max=1,
        sql_empty_retry_max=1,
        generate=_gen,
        review=_review,
        execute=_execute,
    )
    result = await runner.run()
    assert result.ok is True
    assert result.degraded is False
    assert result.warning == ""


@pytest.mark.asyncio
async def test_analyze_warning_propagates_to_result():
    """When analyze callable returns a warning, SelfCorrectingSqlResult.warning contains it."""

    from app.graph.tools.sql_query import SelfCorrectingSqlResult, SelfCorrectingSqlRunner

    async def _gen(hint):
        return "SELECT 1"

    async def _review(sql):
        return {"ok": True, "issues": []}

    async def _execute(sql):
        return []

    async def _analyze(sql, query):
        return {
            "verdict": "suspicious",
            "warning": "Table 'nonexistent' not found in schema",
            "reason": "missing table",
        }

    runner = SelfCorrectingSqlRunner(
        sql_regen_max=2,
        sql_empty_retry_max=1,
        generate=_gen,
        review=_review,
        execute=_execute,
        analyze=_analyze,
        query="test query",
    )
    result: SelfCorrectingSqlResult = await runner.run()
    assert result.ok is True
    assert result.warning == "Table 'nonexistent' not found in schema"


@pytest.mark.asyncio
async def test_analyze_exception_caught_gracefully():
    """When analyze callable raises, runner catches exception and returns empty warning."""

    from app.graph.tools.sql_query import SelfCorrectingSqlResult, SelfCorrectingSqlRunner

    async def _gen(hint):
        return "SELECT 1"

    async def _review(sql):
        return {"ok": True, "issues": []}

    async def _execute(sql):
        return []

    async def _analyze(sql, query):
        raise RuntimeError("analyze exploded")

    runner = SelfCorrectingSqlRunner(
        sql_regen_max=2,
        sql_empty_retry_max=1,
        generate=_gen,
        review=_review,
        execute=_execute,
        analyze=_analyze,
        query="test query",
    )
    result: SelfCorrectingSqlResult = await runner.run()
    assert result.ok is True
    assert result.warning == ""


@pytest.mark.asyncio
async def test_analyze_none_returns_empty_warning():
    """When analyze is None, empty result returns warning == ''."""

    from app.graph.tools.sql_query import SelfCorrectingSqlResult, SelfCorrectingSqlRunner

    async def _gen(hint):
        return "SELECT 1"

    async def _review(sql):
        return {"ok": True, "issues": []}

    async def _execute(sql):
        return []

    runner = SelfCorrectingSqlRunner(
        sql_regen_max=2,
        sql_empty_retry_max=1,
        generate=_gen,
        review=_review,
        execute=_execute,
        analyze=None,
        query="test query",
    )
    result: SelfCorrectingSqlResult = await runner.run()
    assert result.ok is True
    assert result.warning == ""
