from __future__ import annotations


def test_cache_hit_skips_tool() -> None:
    from app.harness.cache import InMemorySemanticCache

    cache = InMemorySemanticCache()
    calls = 0

    def tool():
        nonlocal calls
        calls += 1
        return {"rows": [1]}

    first = cache.get_or_set("sql_query", {"query": "x"}, "t1", tool)
    second = cache.get_or_set("sql_query", {"query": "x"}, "t1", tool)

    assert first == second == {"rows": [1]}
    assert calls == 1
    assert cache.last_event == "cache_hit"


def test_cache_tenant_isolation() -> None:
    from app.harness.cache import InMemorySemanticCache

    cache = InMemorySemanticCache()
    cache.put("sql_query", {"query": "x"}, "t1", {"rows": ["tenant-1"]})

    assert cache.get("sql_query", {"query": "x"}, "t2") is None
    assert cache.last_event == "cache_miss"


def test_cache_only_deterministic_tools() -> None:
    from app.harness.cache import InMemorySemanticCache

    cache = InMemorySemanticCache()

    assert cache.is_cacheable("sql_query") is True
    assert cache.is_cacheable("catalog_draft") is False
