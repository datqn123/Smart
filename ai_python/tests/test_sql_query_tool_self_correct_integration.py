"""Integration tests for SqlQueryTool thin adapter + SelfCorrectingSqlRunner — Slice D (FR-4)."""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.graph.tools.sql_query import SqlQueryTool
from app.harness.tool_registry import TurnContext


def _make_deps(**kwargs):
    deps = MagicMock()
    deps.settings = MagicMock(
        sql_regen_max=2,
        sql_empty_retry_max=1,
        agentic_capability_guard_enabled=False,
    )
    deps.sql_executor = MagicMock()
    for k, v in kwargs.items():
        setattr(deps, k, v)
    return deps


def _ctx(**kwargs) -> TurnContext:
    return TurnContext(
        tenant_id=kwargs.get("tenant_id", "t1"),
        user_id=kwargs.get("user_id", "u1"),
        thread_id=kwargs.get("thread_id", "th1"),
        correlation_id=kwargs.get("correlation_id", "cid"),
        bearer_token=kwargs.get("bearer_token", None),
        schema_version=kwargs.get("schema_version", None),
        role=kwargs.get("role", "owner"),
    )


def _make_tool(gen_result="SELECT 1", review_ok=True, exec_rows=None):
    """Build SqlQueryTool with injectable test callables."""
    gen_calls = []
    review_calls = []

    async def _gen(hint):
        gen_calls.append(hint)
        return gen_result

    async def _review(sql):
        review_calls.append(sql)
        if review_ok:
            return {"ok": True, "issues": []}
        return {"ok": False, "issues": ["bad sql"], "retry_hint": "fix it"}

    async def _execute(sql):
        return exec_rows or [{"id": 1, "name": "row1"}]

    deps = _make_deps()
    tool = SqlQueryTool(
        deps,
        _test_generate=_gen,
        _test_review=_review,
        _test_execute=_execute,
    )
    return tool, gen_calls, review_calls


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_invoke_happy_path_returns_rows():
    tool, gen_calls, review_calls = _make_tool(
        gen_result="SELECT id, name FROM products",
        review_ok=True,
        exec_rows=[{"id": 1, "name": "Apple"}, {"id": 2, "name": "Banana"}],
    )
    result = await tool.invoke({"query": "list products"}, _ctx())
    assert result.ok is True
    assert result.output["query_result"]["rows"] == [{"id": 1, "name": "Apple"}, {"id": 2, "name": "Banana"}]
    assert "Apple" in result.observation_text or "rows" in result.observation_text.lower()


# ---------------------------------------------------------------------------
# SQL fails review → regenerates → passes
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_invoke_self_corrects_on_bad_review():
    call_count = [0]

    async def _gen(hint):
        call_count[0] += 1
        if call_count[0] == 1:
            return "SELECT * FROM bad_table"
        return "SELECT * FROM valid_table"

    async def _review(sql):
        if "bad_table" in sql:
            return {"ok": False, "issues": ["invalid table"], "retry_hint": "use valid_table"}
        return {"ok": True, "issues": []}

    async def _execute(sql):
        return [{"id": 99}]

    deps = _make_deps()
    tool = SqlQueryTool(deps, _test_generate=_gen, _test_review=_review, _test_execute=_execute)
    result = await tool.invoke({"query": "get something"}, _ctx())
    assert result.ok is True
    assert call_count[0] == 2


# ---------------------------------------------------------------------------
# Empty result retry
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_invoke_empty_retry_then_success():
    exec_calls = [0]

    async def _gen(hint):
        return "SELECT id FROM orders WHERE id = 999"

    async def _review(sql):
        return {"ok": True, "issues": []}

    async def _execute(sql):
        exec_calls[0] += 1
        if exec_calls[0] == 1:
            return []  # first call: empty
        return [{"id": 999}]  # second call: has data

    deps = _make_deps()
    tool = SqlQueryTool(deps, _test_generate=_gen, _test_review=_review, _test_execute=_execute)
    result = await tool.invoke({"query": "find order 999"}, _ctx())
    assert result.ok is True
    assert exec_calls[0] == 2


# ---------------------------------------------------------------------------
# Degrade after regen budget exhausted
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_invoke_degraded_when_regen_budget_exhausted():
    async def _gen(hint):
        return "SELECT bad"

    async def _review(sql):
        return {"ok": False, "issues": ["still bad"], "retry_hint": "fix it"}

    async def _execute(sql):
        return [{"id": 1}]

    deps = _make_deps()
    # sql_regen_max=1 means only 1 regen attempt
    deps.settings.sql_regen_max = 1
    tool = SqlQueryTool(deps, _test_generate=_gen, _test_review=_review, _test_execute=_execute)
    result = await tool.invoke({"query": "broken query"}, _ctx())
    # Should degrade gracefully, not raise
    assert isinstance(result.ok, bool)
    assert "Cảnh báo" in result.observation_text or "budget" in result.observation_text


# ---------------------------------------------------------------------------
# Non-SELECT SQL blocked by policy
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_invoke_blocks_non_select_sql():
    async def _gen(hint):
        return "DROP TABLE products"

    async def _review(sql):
        return {"ok": True, "issues": []}

    async def _execute(sql):
        return [{"id": 1}]

    deps = _make_deps()
    tool = SqlQueryTool(deps, _test_generate=_gen, _test_review=_review, _test_execute=_execute)
    result = await tool.invoke({"query": "drop products"}, _ctx())
    assert result.ok is False
    assert "policy" in result.observation_text.lower() or "SELECT" in result.observation_text


# ---------------------------------------------------------------------------
# Legacy path (no sql_executor) still works
# ---------------------------------------------------------------------------

def test_use_thin_adapter_false_without_sql_executor():
    deps = MagicMock()
    deps.sql_executor = None
    deps.llm_registry = None
    # Should not use thin adapter when sql_executor is None and no test callables
    tool = SqlQueryTool.__new__(SqlQueryTool)
    tool._deps = deps
    tool._test_generate = None
    tool._test_review = None
    tool._test_execute = None
    assert tool._use_thin_adapter() is False
