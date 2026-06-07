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
async def test_sql_empty_result_retry() -> None:
    from app.graph.tools.sql_query import SelfCorrectingSqlRunner

    executions = 0

    async def gen(hint: str | None):
        return "SELECT 1 AS v LIMIT 10"

    async def review(sql: str):
        return {"ok": True, "issues": []}

    async def execute(sql: str):
        nonlocal executions
        executions += 1
        return [] if executions <= 2 else [{"v": 1}]

    result = await SelfCorrectingSqlRunner(
        sql_regen_max=3,
        sql_empty_retry_max=2,
        generate=gen,
        review=review,
        execute=execute,
    ).run()

    assert result.ok is True
    assert result.empty_retry_count == 2
    assert result.rows == [{"v": 1}]


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
async def test_sql_degrade_returns_partial() -> None:
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
    assert result.degraded is True
    assert "cảnh báo" in result.warning.lower()


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
