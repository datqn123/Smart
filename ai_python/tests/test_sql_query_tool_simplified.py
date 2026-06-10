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


@pytest.mark.asyncio
async def test_sql_query_tool_success(mock_deps, mock_ctx):
    """Test successful SQL execution."""
    mock_artifact = MagicMock()
    with patch("app.graph.tools.sql_query.build_schema_artifact_from_postgres", return_value=(mock_artifact, None)):
        with patch("app.graph.tools.sql_query.load_agent_prompt", return_value="gen_sql prompt"):
            with patch("app.graph.tools.sql_query.format_schema_block", return_value="schema block"):
                llm_result = MagicMock()
                llm_result.sql = "SELECT * FROM products LIMIT 10"
                llm_result.explanation = "Test query"
                mock_deps.llm_registry.get.return_value.structured_predict.return_value = llm_result

                mock_deps.sql_executor.aexecute.return_value = {"rows": [{"id": 1, "name": "Product A"}]}

                tool = SqlQueryTool(mock_deps)
                result = await tool.invoke({"question": "list products"}, mock_ctx)

                assert result.ok is True
                assert len(result.output["rows"]) == 1
                assert result.output["generated_sql"] == "SELECT * FROM products LIMIT 10"


@pytest.mark.asyncio
async def test_sql_query_tool_empty_result(mock_deps, mock_ctx):
    """Test empty result handling."""
    mock_artifact = MagicMock()
    with patch("app.graph.tools.sql_query.build_schema_artifact_from_postgres", return_value=(mock_artifact, None)):
        with patch("app.graph.tools.sql_query.load_agent_prompt", return_value="gen_sql prompt"):
            with patch("app.graph.tools.sql_query.format_schema_block", return_value="schema block"):
                llm_result = MagicMock()
                llm_result.sql = "SELECT * FROM products WHERE id = 999"
                llm_result.explanation = "Test query"
                mock_deps.llm_registry.get.return_value.structured_predict.return_value = llm_result

                mock_deps.sql_executor.aexecute.return_value = {"rows": []}

                tool = SqlQueryTool(mock_deps)
                result = await tool.invoke({"question": "find product 999"}, mock_ctx)

                assert result.ok is True
                assert len(result.output["rows"]) == 0


@pytest.mark.asyncio
async def test_sql_query_tool_safety_check(mock_deps, mock_ctx):
    """Test SQL safety check blocks DDL."""
    mock_artifact = MagicMock()
    with patch("app.graph.tools.sql_query.build_schema_artifact_from_postgres", return_value=(mock_artifact, None)):
        with patch("app.graph.tools.sql_query.load_agent_prompt", return_value="gen_sql prompt"):
            with patch("app.graph.tools.sql_query.format_schema_block", return_value="schema block"):
                llm_result = MagicMock()
                llm_result.sql = "DROP TABLE products"
                llm_result.explanation = "Malicious query"
                mock_deps.llm_registry.get.return_value.structured_predict.return_value = llm_result

                tool = SqlQueryTool(mock_deps)
                result = await tool.invoke({"question": "drop table"}, mock_ctx)

                assert result.ok is False
                assert "safety check failed" in result.observation_text.lower()


@pytest.mark.asyncio
async def test_sql_query_tool_empty_question(mock_deps, mock_ctx):
    """Test empty question validation."""
    tool = SqlQueryTool(mock_deps)
    result = await tool.invoke({"question": ""}, mock_ctx)

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
async def test_sql_query_tool_llm_failure(mock_deps, mock_ctx):
    """Test LLM generation failure handling."""
    mock_artifact = MagicMock()
    with patch("app.graph.tools.sql_query.build_schema_artifact_from_postgres", return_value=(mock_artifact, None)):
        with patch("app.graph.tools.sql_query.load_agent_prompt", return_value="gen_sql prompt"):
            with patch("app.graph.tools.sql_query.format_schema_block", return_value="schema block"):
                mock_deps.llm_registry.get.return_value.structured_predict.side_effect = Exception("LLM timeout")

                tool = SqlQueryTool(mock_deps)
                result = await tool.invoke({"question": "list products"}, mock_ctx)

                assert result.ok is False
                assert "LLM generation failed" in result.error_message


@pytest.mark.asyncio
async def test_sql_query_tool_execution_failure(mock_deps, mock_ctx):
    """Test SQL execution failure handling."""
    mock_artifact = MagicMock()
    with patch("app.graph.tools.sql_query.build_schema_artifact_from_postgres", return_value=(mock_artifact, None)):
        with patch("app.graph.tools.sql_query.load_agent_prompt", return_value="gen_sql prompt"):
            with patch("app.graph.tools.sql_query.format_schema_block", return_value="schema block"):
                llm_result = MagicMock()
                llm_result.sql = "SELECT * FROM invalid_table"
                llm_result.explanation = "Test query"
                mock_deps.llm_registry.get.return_value.structured_predict.return_value = llm_result

                mock_deps.sql_executor.aexecute.side_effect = Exception("Table not found")

                tool = SqlQueryTool(mock_deps)
                result = await tool.invoke({"question": "list products"}, mock_ctx)

                assert result.ok is False
                assert "SQL execution failed" in result.error_message
