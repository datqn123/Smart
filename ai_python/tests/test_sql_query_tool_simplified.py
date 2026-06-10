"""Tests for simplified sql_query tool."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.config.graph_settings import GraphSettings
from app.graph.deps import GraphDeps
from app.graph.tools.sql_query import SqlQueryTool
from app.harness.tool_registry import TurnContext


@pytest.fixture
def mock_deps():
    """Create mock dependencies for SqlQueryTool."""
    deps = MagicMock(spec=GraphDeps)
    deps.settings = MagicMock(spec=GraphSettings)
    deps.llm_registry = MagicMock()
    deps.sql_executor = AsyncMock()
    deps.harness = MagicMock()
    return deps


@pytest.fixture
def mock_ctx():
    """Create mock TurnContext."""
    return TurnContext(
        tenant_id="test",
        user_id="user1",
        thread_id="thread1",
        correlation_id="corr1",
        bearer_token=None,
        schema_version=None,
    )


@pytest.fixture
def patched_schema(mock_artifact):
    """Patch schema loading."""
    with patch("app.graph.pg_schema_context.build_schema_artifact_from_postgres", return_value=(mock_artifact, None)):
        yield


@pytest.fixture
def mock_artifact():
    """Create mock schema artifact."""
    return MagicMock()


def _patch_tool_internals(mock_artifact):
    """Return a list of patches for tool internals."""
    return [
        patch("app.graph.tools.sql_query.build_schema_artifact_from_postgres", return_value=(mock_artifact, None)),
        patch("app.graph.tools.sql_query.load_agent_prompt", return_value="gen_sql prompt"),
        patch("app.graph.tools.sql_query.format_schema_block", return_value="schema block"),
    ]


def _apply_patches(patches):
    """Start all patches and return list of started patchers."""
    started = []
    for p in patches:
        started.append(p.start())
    return started


def _stop_patches(patches):
    """Stop all patches."""
    for p in patches:
        p.stop()


@pytest.mark.asyncio
async def test_sql_query_tool_success(mock_deps, mock_ctx, mock_artifact):
    """Test successful SQL execution."""
    patches = _patch_tool_internals(mock_artifact)
    _apply_patches(patches)
    try:
        llm_result = MagicMock()
        llm_result.sql = "SELECT * FROM products LIMIT 10"
        llm_result.explanation = "Test query"
        mock_llm_client = MagicMock()
        mock_llm_client.structured_predict.return_value = llm_result
        mock_deps.llm_registry.get.return_value = mock_llm_client

        mock_deps.sql_executor.aexecute.return_value = {"rows": [{"id": 1, "name": "Product A"}]}

        tool = SqlQueryTool(mock_deps)
        result = await tool.invoke({"question": "list products"}, mock_ctx)

        assert result.ok is True
        assert len(result.output["rows"]) == 1
        assert result.output["generated_sql"] == "SELECT * FROM products LIMIT 10"
        assert "rows returned" in result.observation_text.lower()
    finally:
        _stop_patches(patches)


@pytest.mark.asyncio
async def test_sql_query_tool_empty_result(mock_deps, mock_ctx, mock_artifact):
    """Test empty result handling."""
    patches = _patch_tool_internals(mock_artifact)
    _apply_patches(patches)
    try:
        llm_result = MagicMock()
        llm_result.sql = "SELECT * FROM products WHERE id = 999"
        llm_result.explanation = "Test query"
        mock_llm_client = MagicMock()
        mock_llm_client.structured_predict.return_value = llm_result
        mock_deps.llm_registry.get.return_value = mock_llm_client

        mock_deps.sql_executor.aexecute.return_value = {"rows": []}

        tool = SqlQueryTool(mock_deps)
        result = await tool.invoke({"question": "find product 999"}, mock_ctx)

        assert result.ok is True
        assert len(result.output["rows"]) == 0
        assert "rows returned" in result.observation_text.lower()
    finally:
        _stop_patches(patches)


@pytest.mark.asyncio
async def test_sql_query_tool_safety_check(mock_deps, mock_ctx, mock_artifact):
    """Test SQL safety check blocks DDL."""
    patches = _patch_tool_internals(mock_artifact)
    _apply_patches(patches)
    try:
        llm_result = MagicMock()
        llm_result.sql = "DROP TABLE products"
        llm_result.explanation = "Malicious query"
        mock_llm_client = MagicMock()
        mock_llm_client.structured_predict.return_value = llm_result
        mock_deps.llm_registry.get.return_value = mock_llm_client

        tool = SqlQueryTool(mock_deps)
        result = await tool.invoke({"question": "drop table"}, mock_ctx)

        assert result.ok is False
        assert "safety check failed" in result.observation_text.lower()
    finally:
        _stop_patches(patches)


@pytest.mark.asyncio
async def test_sql_query_tool_empty_question():
    """Test empty question validation."""
    tool = SqlQueryTool(MagicMock(spec=GraphDeps))
    result = await tool.invoke({"question": ""}, MagicMock())

    assert result.ok is False
    assert result.error_message == "Question is required"


@pytest.mark.asyncio
async def test_sql_query_tool_schema_load_failure(mock_deps, mock_ctx):
    """Test schema load failure handling."""
    with patch("app.graph.tools.sql_query.build_schema_artifact_from_postgres", return_value=(None, "Connection failed")):
        tool = SqlQueryTool(mock_deps)
        result = await tool.invoke({"question": "list products"}, mock_ctx)

        assert result.ok is False
        assert "Schema load failed" in result.error_message


@pytest.mark.asyncio
async def test_sql_query_tool_llm_failure(mock_deps, mock_ctx, mock_artifact):
    """Test LLM generation failure handling."""
    patches = _patch_tool_internals(mock_artifact)
    _apply_patches(patches)
    try:
        mock_llm_client = MagicMock()
        mock_llm_client.structured_predict.side_effect = Exception("LLM timeout")
        mock_deps.llm_registry.get.return_value = mock_llm_client

        tool = SqlQueryTool(mock_deps)
        result = await tool.invoke({"question": "list products"}, mock_ctx)

        assert result.ok is False
        assert "LLM generation failed" in result.error_message
    finally:
        _stop_patches(patches)


@pytest.mark.asyncio
async def test_sql_query_tool_execution_failure(mock_deps, mock_ctx, mock_artifact):
    """Test SQL execution failure handling."""
    patches = _patch_tool_internals(mock_artifact)
    _apply_patches(patches)
    try:
        llm_result = MagicMock()
        llm_result.sql = "SELECT * FROM invalid_table"
        llm_result.explanation = "Test query"
        mock_llm_client = MagicMock()
        mock_llm_client.structured_predict.return_value = llm_result
        mock_deps.llm_registry.get.return_value = mock_llm_client

        mock_deps.sql_executor.aexecute.side_effect = Exception("Table not found")

        tool = SqlQueryTool(mock_deps)
        result = await tool.invoke({"question": "list products"}, mock_ctx)

        assert result.ok is False
        assert "SQL execution failed" in result.error_message
    finally:
        _stop_patches(patches)


@pytest.mark.asyncio
async def test_sql_query_tool_sse_payload(mock_deps, mock_ctx, mock_artifact):
    """Test sse_payload is returned when rows exist."""
    patches = _patch_tool_internals(mock_artifact)
    _apply_patches(patches)
    try:
        llm_result = MagicMock()
        llm_result.sql = "SELECT * FROM products LIMIT 10"
        llm_result.explanation = "Test query"
        mock_llm_client = MagicMock()
        mock_llm_client.structured_predict.return_value = llm_result
        mock_deps.llm_registry.get.return_value = mock_llm_client
        mock_deps.sql_executor.aexecute.return_value = {"rows": [{"id": 1}]}

        tool = SqlQueryTool(mock_deps)
        result = await tool.invoke({"question": "list products"}, mock_ctx)

        assert result.sse_payload is not None
        assert result.sse_payload["_event"] == "data_table"
    finally:
        _stop_patches(patches)
