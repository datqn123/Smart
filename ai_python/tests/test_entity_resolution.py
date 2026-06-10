from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
import pytest_asyncio

from app.graph.entity_resolution import (
    _extract_keywords,
    _load_names_batch,
    _match_keywords,
    load_entity_names,
    resolve_entities_for_domain,
)
from app.graph.sql_query_domain import SqlQueryDomain
from app.graph.tools.sql_query import SqlQueryTool


class TestExtractKeywords:
    def test_extracts_product_name(self) -> None:
        result = _extract_keywords("máy tính để bàn dell", "inventory")
        assert "dell" in result
        assert "bàn" in result
        assert "máy" in result
        assert "tính" in result
        assert len(result) == 5

    def test_empty_when_all_stopwords(self) -> None:
        result = _extract_keywords("của và các", "inventory")
        assert result == []

    def test_generic_domain_returns_empty(self) -> None:
        result = _extract_keywords("máy tính để bàn", "generic")
        assert result == []


class TestLoadNamesBatch:
    @pytest.mark.asyncio
    async def test_returns_names_from_executor(self) -> None:
        executor = AsyncMock()
        executor.aexecute.return_value = {
            "rows": [{"name": "Product A"}, {"name": "Product B"}],
        }
        result = await _load_names_batch(executor, "t1", "products", "name", 0, 500)
        assert result == ["Product A", "Product B"]
        executor.aexecute.assert_awaited_once()
        call_sql = executor.aexecute.call_args[0][0]
        assert "SELECT DISTINCT" in call_sql
        assert '"products"' in call_sql
        assert '"name"' in call_sql

    @pytest.mark.asyncio
    async def test_handles_executor_error(self) -> None:
        executor = AsyncMock()
        executor.aexecute.side_effect = RuntimeError("DB error")
        result = await _load_names_batch(executor, "t1", "products", "name", 0, 500)
        assert result == []

    @pytest.mark.asyncio
    async def test_rejects_invalid_table(self) -> None:
        executor = AsyncMock()
        result = await _load_names_batch(executor, "t1", "users", "name", 0, 500)
        assert result == []
        executor.aexecute.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_rejects_invalid_column(self) -> None:
        executor = AsyncMock()
        result = await _load_names_batch(executor, "t1", "products", "password", 0, 500)
        assert result == []
        executor.aexecute.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_returns_empty_for_none_tenant_id(self) -> None:
        executor = AsyncMock()
        result = await _load_names_batch(executor, None, "products", "name", 0, 500)
        assert result == []
        executor.aexecute.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_forwards_bearer_token(self) -> None:
        executor = AsyncMock()
        executor.aexecute.return_value = {
            "rows": [{"name": "Product A"}],
        }
        result = await _load_names_batch(executor, "t1", "products", "name", 0, 500, bearer_token="tok_abc")
        assert result == ["Product A"]
        executor.aexecute.assert_awaited_once_with(
            executor.aexecute.call_args[0][0],
            tenant_id="t1",
            bearer_token="tok_abc",
        )

    @pytest.mark.asyncio
    async def test_rejects_valid_table_wrong_column_pair(self) -> None:
        executor = AsyncMock()
        result = await _load_names_batch(executor, "t1", "financeledger", "name", 0, 500)
        assert result == []
        executor.aexecute.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_rejects_valid_table_wrong_column_pair(self) -> None:
        executor = AsyncMock()
        result = await _load_names_batch(executor, "t1", "categories", "email", 0, 500)
        assert result == []
        executor.aexecute.assert_not_awaited()


class TestMatchKeywords:
    def test_exact_match(self) -> None:
        result = _match_keywords(["Product A", "Product B"], ["product a"])
        assert result["exact_matches"] == ["Product A"]
        assert result["found_exact"] is True

    def test_case_insensitive(self) -> None:
        result = _match_keywords(["Product A"], ["PRODUCT a"])
        assert result["exact_matches"] == ["Product A"]

    def test_word_substring_fuzzy(self) -> None:
        result = _match_keywords(
            ["Máy tính để bàn", "Chuột không dây"],
            ["bàn", "chuột"],
        )
        assert "Máy tính để bàn" in result["fuzzy_matches"]
        assert "Chuột không dây" in result["fuzzy_matches"]

    def test_no_match(self) -> None:
        result = _match_keywords(["Product A"], ["xyz"])
        assert result["exact_matches"] == []
        assert result["fuzzy_matches"] == []
        assert result["found_exact"] is False

    def test_empty_names_list(self) -> None:
        result = _match_keywords([], ["test"])
        assert result["exact_matches"] == []
        assert result["fuzzy_matches"] == []
        assert result["found_exact"] is False

    def test_keyword_longer_than_name(self) -> None:
        result = _match_keywords(["abc"], ["abcdefghijk"])
        assert result["exact_matches"] == []
        assert result["fuzzy_matches"] == []
        assert result["found_exact"] is False


class TestLoadEntityNames:
    @pytest.mark.asyncio
    async def test_stops_after_exact_match(self) -> None:
        executor = AsyncMock()
        executor.aexecute.return_value = {
            "rows": [{"name": "Product A"}, {"name": "Product B"}],
        }
        result = await load_entity_names(
            executor, "t1", "products", "name",
            keywords=["Product A"],
            batch_size=5, max_batches=3,
        )
        assert "Product A" in result["exact_matches"]
        assert result["truncated"] is False

    @pytest.mark.asyncio
    async def test_exhausts_batches_returns_truncated(self) -> None:
        executor = AsyncMock()
        executor.aexecute.return_value = {
            "rows": [{"name": f"Product_{i}"} for i in range(5)],
        }
        result = await load_entity_names(
            executor, "t1", "products", "name",
            keywords=["not_found"],
            batch_size=5, max_batches=2,
        )
        assert result["exact_matches"] == []
        assert result["truncated"] is True
        assert executor.aexecute.await_count == 2

    @pytest.mark.asyncio
    async def test_no_keywords_returns_early(self) -> None:
        executor = AsyncMock()
        result = await load_entity_names(
            executor, "t1", "products", "name",
            keywords=[], batch_size=5, max_batches=3,
        )
        assert result["exact_matches"] == []
        assert result["fuzzy_matches"] == []
        assert result["truncated"] is True
        executor.aexecute.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_returns_empty_for_none_tenant_id(self) -> None:
        executor = AsyncMock()
        result = await load_entity_names(
            executor, None, "products", "name",
            keywords=["test"], batch_size=5, max_batches=3,
        )
        assert result["exact_matches"] == []
        assert result["loaded_names"] == []
        executor.aexecute.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_forwards_bearer_token(self) -> None:
        executor = AsyncMock()
        executor.aexecute.return_value = {
            "rows": [{"name": "Product A"}],
        }
        result = await load_entity_names(
            executor, "t1", "products", "name",
            keywords=["Product A"],
            batch_size=5, max_batches=1,
            bearer_token="tok_xyz",
        )
        assert "Product A" in result["exact_matches"]
        executor.aexecute.assert_awaited_once()
        assert executor.aexecute.call_args[1].get("bearer_token") == "tok_xyz"

    @pytest.mark.asyncio
    async def test_empty_names_list(self) -> None:
        executor = AsyncMock()
        result = await load_entity_names(
            executor, "t1", "products", "name",
            keywords=["test"], batch_size=5, max_batches=0,
        )
        assert result["exact_matches"] == []
        assert result["truncated"] is True


class TestResolveEntitiesForDomain:
    @pytest.mark.asyncio
    async def test_dispatches_by_domain_inventory(self) -> None:
        executor_mock = AsyncMock()
        executor_mock.aexecute.return_value = {
            "rows": [{"name": "Product A"}, {"name": "Product B"}],
        }
        deps = AsyncMock()
        deps.sql_executor = executor_mock
        deps.settings.entity_resolution_enabled = True
        deps.settings.entity_resolution_batch_size = 500
        deps.settings.entity_resolution_max_batches = 3
        result = await resolve_entities_for_domain(
            deps, "t1",
            "tình hình Product A tồn kho",
            "inventory",
        )
        assert "products" in result
        assert "Product A" in result["products"]["fuzzy_matches"]

    @pytest.mark.asyncio
    async def test_skips_when_disabled(self) -> None:
        deps = AsyncMock()
        deps.settings.entity_resolution_enabled = False
        result = await resolve_entities_for_domain(
            deps, "t1", "some question", "inventory",
        )
        assert result == {}

    @pytest.mark.asyncio
    async def test_returns_empty_for_none_tenant_id(self) -> None:
        deps = AsyncMock()
        deps.settings.entity_resolution_enabled = True
        result = await resolve_entities_for_domain(
            deps, None, "some question", "inventory",
        )
        assert result == {}

    @pytest.mark.asyncio
    async def test_returns_empty_for_empty_tenant_id(self) -> None:
        deps = AsyncMock()
        deps.settings.entity_resolution_enabled = True
        result = await resolve_entities_for_domain(
            deps, "", "some question", "inventory",
        )
        assert result == {}

    @pytest.mark.asyncio
    async def test_forwards_bearer_token(self) -> None:
        executor_mock = AsyncMock()
        executor_mock.aexecute.return_value = {
            "rows": [{"name": "Product A"}],
        }
        deps = AsyncMock()
        deps.sql_executor = executor_mock
        deps.settings.entity_resolution_enabled = True
        deps.settings.entity_resolution_batch_size = 500
        deps.settings.entity_resolution_max_batches = 1
        result = await resolve_entities_for_domain(
            deps, "t1",
            "Product A tồn kho",
            "inventory",
            bearer_token="tok_deps",
        )
        assert "products" in result
        executor_mock.aexecute.assert_awaited_once()
        assert executor_mock.aexecute.call_args[1].get("bearer_token") == "tok_deps"

    @pytest.mark.asyncio
    async def test_unknown_domain_returns_empty(self) -> None:
        deps = AsyncMock()
        deps.settings.entity_resolution_enabled = True
        deps.sql_executor = AsyncMock()
        result = await resolve_entities_for_domain(
            deps, "t1", "some question", "nonexistent_domain",
        )
        assert result == {}
        deps.sql_executor.aexecute.assert_not_awaited()

