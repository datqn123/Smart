# Entity Resolution Step Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a pre-`gen_sql` entity resolution step that loads actual entity names from the database in batches and injects exact names into the LLM prompt.

**Architecture:** New module `entity_resolution.py` provides `load_entity_names()` (batch-load from DB, match against user keywords) and `resolve_entities_for_domain()` (orchestrator). A new node factory `make_entity_resolution_node()` in `sql_pipeline.py` wraps it for the LangGraph subgraph. The node is wired into `sql_subgraph.py` between `schema_explore` and `gen_sql`. The thin adapter path in `sql_query.py` gets an equivalent injection point. State key `entity_context` carries results to prompt builders.

**Tech Stack:** Python 3.12+, asyncio, LangGraph, PostgreSQL.

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `ai_python/app/graph/entity_resolution.py` | **Create** | Core logic: batch-load names, keyword extraction, matching |
| `ai_python/app/graph/nodes/sql_pipeline.py` | **Modify** | Add `make_entity_resolution_node()` factory + entity section in gen_sql prompt |
| `ai_python/app/graph/sql_subgraph.py` | **Modify** | Wire `resolve_entities` node between `schema_explore` and `gen_sql` |
| `ai_python/app/graph/tools/sql_query.py` | **Modify** | Integrate entity lookup into generate closure for thin-adapter path |
| `ai_python/app/config/graph_settings.py` | **Modify** | Add 3 config fields |
| `ai_python/app/graph/state.py` | **Modify** | Add `entity_context` key to `AgentState` |
| `ai_python/tests/test_entity_resolution.py` | **Create** | Unit tests for batch-load, matching, keyword extraction |
| `ai_python/tests/test_sql_subgraph_entity_resolution.py` | **Create** | Integration test for node wiring |

---

### Task 1: Add config settings

**Files:**
- Modify: `ai_python/app/config/graph_settings.py`

- [ ] **Step 1: Add 3 config fields**

Add after `sql_empty_retry_max`:

```python
    entity_resolution_enabled: bool = Field(
        default=True,
        description="Enable entity resolution step before gen_sql.",
    )
    entity_resolution_batch_size: int = Field(default=500, ge=1, le=5000)
    entity_resolution_max_batches: int = Field(default=3, ge=1, le=20)
```

Also add the 3 new field names to the `@classmethod` `coerce_sql_dialog_tail_ints` method so they're in the known-keys set:

```python
        "entity_resolution_batch_size",
        "entity_resolution_max_batches",
```

- [ ] **Step 2: Verify import works**

```bash
cd ai_python && python -c "from app.config.graph_settings import GraphSettings; s=GraphSettings(); assert s.entity_resolution_enabled is True; assert s.entity_resolution_batch_size == 500"
```

Expected: No error.

---

### Task 2: Create entity_resolution.py core module

**Files:**
- Create: `ai_python/app/graph/entity_resolution.py`

This module provides:
- `_extract_keywords(question: str, domain: str) -> list[str]` — extract search terms from user question
- `_load_names_batch(executor, tenant_id, table: str, column: str, offset: int, limit: int) -> list[str]` — single batch query
- `_match_keywords(names: list[str], keywords: list[str]) -> dict` — check loaded names against keywords
- `load_entity_names(executor, tenant_id, table: str, column: str, keywords: list[str], batch_size: int, max_batches: int) -> dict` — full batch-load + match orchestrator
- `resolve_entities_for_domain(deps, tenant_id, question: str, domain: str, settings) -> dict` — domain-aware dispatcher

- [ ] **Step 1: Write the test**

Create `ai_python/tests/test_entity_resolution.py`:

```python
"""Tests for entity resolution module — batch loading, keyword extraction, matching."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.graph.entity_resolution import (
    _extract_keywords,
    _load_names_batch,
    _match_keywords,
    load_entity_names,
    resolve_entities_for_domain,
)


class TestExtractKeywords:
    def test_extracts_product_name(self):
        q = "doanh thu tháng 2 của áo thun nam"
        kw = _extract_keywords(q, "inventory")
        assert "áo" in kw
        assert "thun" in kw
        assert "nam" in kw
        assert "của" not in kw  # stopword
        assert "tháng" not in kw  # stopword

    def test_empty_when_all_stopwords(self):
        q = "liệt kê sản phẩm"
        kw = _extract_keywords(q, "inventory")
        assert isinstance(kw, list)
        assert "liệt" not in kw  # stopword
        assert "kê" not in kw  # stopword

    def test_generic_domain_returns_empty(self):
        q = "cho tôi xem danh sách"
        kw = _extract_keywords(q, "generic")
        assert kw == []


class TestLoadNamesBatch:
    @pytest.mark.asyncio
    async def test_returns_names_from_executor(self):
        executor = AsyncMock()
        executor.aexecute.return_value = {
            "rows": [{"name": "Áo Thun"}, {"name": "Áo Sơ Mi"}]
        }
        names = await _load_names_batch(executor, "t1", "products", "name", 0, 500)
        assert names == ["Áo Thun", "Áo Sơ Mi"]

    @pytest.mark.asyncio
    async def test_handles_executor_error(self):
        executor = AsyncMock()
        executor.aexecute.side_effect = Exception("DB down")
        names = await _load_names_batch(executor, "t1", "products", "name", 0, 500)
        assert names == []


class TestMatchKeywords:
    def test_exact_match_found(self):
        names = ["Áo Thun Nam", "Áo Sơ Mi", "Quần Jean"]
        result = _match_keywords(names, ["áo thun nam"])
        assert result["exact_matches"] == ["Áo Thun Nam"]
        assert result["found_exact"] is True

    def test_exact_match_case_insensitive(self):
        names = ["Áo Thun Nam", "Áo Sơ Mi"]
        result = _match_keywords(names, ["AO THUN NAM"])
        assert result["exact_matches"] == ["Áo Thun Nam"]

    def test_word_substring_fuzzy(self):
        names = ["Áo Thun Nam Tay Ngắn", "Áo Sơ Mi", "Quần Jean"]
        result = _match_keywords(names, ["thun"])
        assert result["fuzzy_matches"] == ["Áo Thun Nam Tay Ngắn"]
        assert result["found_exact"] is False

    def test_no_match_returns_empty(self):
        names = ["Áo Sơ Mi", "Quần Jean"]
        result = _match_keywords(names, ["giày"])
        assert result["exact_matches"] == []
        assert result["fuzzy_matches"] == []
        assert result["found_exact"] is False


class TestLoadEntityNames:
    @pytest.mark.asyncio
    async def test_stops_after_exact_match(self):
        executor = AsyncMock()

        async def fake_execute(sql, **kw):
            if "OFFSET 0" in sql:
                return {"rows": [{"name": "Áo Sơ Mi"}, {"name": "Áo Thun Nam"}]}
            return {"rows": []}

        executor.aexecute = fake_execute
        result = await load_entity_names(
            executor, "t1", "products", "name",
            keywords=["áo thun nam"], batch_size=500, max_batches=3,
        )
        assert result["exact_matches"] == ["Áo Thun Nam"]
        assert result["truncated"] is False

    @pytest.mark.asyncio
    async def test_exhausts_batches_returns_truncated(self):
        executor = AsyncMock()
        call_count = [0]

        async def fake_execute(sql, **kw):
            call_count[0] += 1
            return {"rows": [{"name": f"Product {i}"} for i in range(500)]}

        executor.aexecute = fake_execute
        result = await load_entity_names(
            executor, "t1", "products", "name",
            keywords=["nonexistent"], batch_size=500, max_batches=2,
        )
        assert result["truncated"] is True
        assert call_count[0] == 2

    @pytest.mark.asyncio
    async def test_no_keywords_returns_early(self):
        result = await load_entity_names(
            AsyncMock(), "t1", "products", "name",
            keywords=[], batch_size=500, max_batches=3,
        )
        assert result["loaded_names"] == []


class TestResolveEntitiesForDomain:
    @pytest.mark.asyncio
    async def test_dispatches_by_domain_inventory(self):
        deps = AsyncMock()
        deps.settings.entity_resolution_enabled = True
        deps.settings.entity_resolution_batch_size = 500
        deps.settings.entity_resolution_max_batches = 3

        executor = AsyncMock()
        executor.aexecute.return_value = {"rows": [{"name": "Áo Thun Nam"}]}
        deps.sql_executor = executor

        result = await resolve_entities_for_domain(deps, "t1", "áo thun nam", "inventory")
        assert "products" in result
        assert result["products"]["exact_matches"] == ["Áo Thun Nam"]

    @pytest.mark.asyncio
    async def test_skips_when_disabled(self):
        deps = AsyncMock()
        deps.settings.entity_resolution_enabled = False
        result = await resolve_entities_for_domain(
            deps, "t1", "áo thun", "inventory",
        )
        assert result == {}
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd ai_python && pytest tests/test_entity_resolution.py -v
```
Expected: All tests FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement the core module**

Create `ai_python/app/graph/entity_resolution.py`:

```python
"""Entity resolution for SQL pipeline — batch-load actual entity names from DB and match against user keywords."""

from __future__ import annotations

import logging
import re
from typing import Any

from app.graph.deps import GraphDeps
from app.graph.sql_query_domain import SqlQueryDomain

logger = logging.getLogger(__name__)

_STOPWORDS: frozenset[str] = frozenset({
    "của", "và", "các", "những", "cho", "trong", "tại", "từ", "đến",
    "với", "có", "không", "đã", "đang", "sẽ", "này", "kia", "đó",
    "một", "hai", "ba", "bốn", "năm", "tháng", "ngày", "năm", "quý",
    "tuần", "liệt", "kê", "danh", "sách", "xem", "tìm", "kiếm",
    "bao", "nhiêu", "nào", "số", "lượng", "giá", "trị", "tổng",
    "cộng", "tất", "cả", "đơn", "hàng", "mới", "cũ", "còn",
})

_DOMAIN_PHRASES: dict[str, frozenset[str]] = {
    "inventory": frozenset({"tồn kho", "hết hàng", "còn bao nhiêu", "sắp hết"}),
    "receipt": frozenset({"phiếu nhập", "nhập kho", "stockreceipt"}),
    "dispatch": frozenset({"phiếu xuất", "xuất kho", "giao hàng", "stockdispatch"}),
    "ledger": frozenset({"doanh thu", "chi phí", "dòng tiền", "sổ cái"}),
    "catalog_price": frozenset({"giá vốn", "giá bán", "giá niêm yết", "đơn giá"}),
}

_ENTITY_MAP: dict[str, list[dict[str, str]]] = {
    "inventory": [{"table": "products", "column": "name"}],
    "receipt": [
        {"table": "products", "column": "name"},
        {"table": "suppliers", "column": "name"},
    ],
    "dispatch": [{"table": "products", "column": "name"}],
    "ledger": [{"table": "financeledger", "column": "transaction_type"}],
    "catalog_price": [
        {"table": "products", "column": "name"},
        {"table": "categories", "column": "name"},
    ],
}


def _extract_keywords(question: str, domain: str) -> list[str]:
    """Extract search keywords from user question, filtering stopwords and domain phrases."""
    if domain == "generic":
        return []
    q = (question or "").lower()
    q_clean = re.sub(r"[^\w\s]", " ", q)
    tokens = q_clean.split()

    domain_stop = _DOMAIN_PHRASES.get(domain, frozenset())
    result: list[str] = []
    for t in tokens:
        t = t.strip()
        if not t or len(t) < 2:
            continue
        if t in _STOPWORDS:
            continue
        if t in domain_stop:
            continue
        result.append(t)

    seen: set[str] = set()
    unique: list[str] = []
    for t in result:
        if t not in seen:
            seen.add(t)
            unique.append(t)
    return unique


async def _load_names_batch(
    executor: Any,
    tenant_id: str,
    table: str,
    column: str,
    offset: int,
    limit: int,
) -> list[str]:
    """Load a single batch of DISTINCT {column} values from {table}."""
    sql = f'SELECT DISTINCT "{column}" FROM "{table}" ORDER BY "{column}" LIMIT {int(limit)} OFFSET {int(offset)}'
    try:
        result = await executor.aexecute(sql, tenant_id=tenant_id)
        rows = result.get("rows", []) if isinstance(result, dict) else []
        return [str(r[column]) for r in rows if isinstance(r, dict) and column in r]
    except Exception as exc:
        logger.warning("entity batch load failed: table=%s col=%s offset=%d err=%s", table, column, offset, exc)
        return []


def _match_keywords(names: list[str], keywords: list[str]) -> dict[str, Any]:
    """Match loaded names against user keywords.

    Returns:
        exact_matches: names that exactly match a keyword (case-insensitive)
        fuzzy_matches: names where keyword is a word-substring of name
        found_exact: True if any exact match found
    """
    exact: list[str] = []
    fuzzy: list[str] = []
    kw_lower = [k.lower() for k in keywords]

    for name in names:
        name_lower = name.lower()
        for kw in kw_lower:
            if name_lower == kw:
                exact.append(name)
                break
        else:
            name_words = set(name_lower.split())
            for kw in kw_lower:
                if kw in name_words:
                    fuzzy.append(name)
                    break

    exact = list(dict.fromkeys(exact))
    fuzzy = [n for n in dict.fromkeys(fuzzy) if n not in exact]

    return {
        "exact_matches": exact,
        "fuzzy_matches": fuzzy,
        "found_exact": bool(exact),
    }


async def load_entity_names(
    executor: Any,
    tenant_id: str,
    table: str,
    column: str,
    keywords: list[str],
    batch_size: int = 500,
    max_batches: int = 3,
) -> dict[str, Any]:
    """Load entity names in batches, stopping early if exact match found.

    Returns:
        exact_matches: names exactly matching user keywords
        fuzzy_matches: word-substring matches
        loaded_names: all names loaded so far
        truncated: True if max_batches reached without scanning all rows
    """
    if not keywords:
        return {"exact_matches": [], "fuzzy_matches": [], "loaded_names": [], "truncated": False}

    all_names: list[str] = []
    for batch_idx in range(max_batches):
        offset = batch_idx * batch_size
        names = await _load_names_batch(executor, tenant_id, table, column, offset, batch_size)
        if not names:
            break
        all_names.extend(names)

        result = _match_keywords(all_names, keywords)
        if result["found_exact"]:
            return {
                "exact_matches": result["exact_matches"],
                "fuzzy_matches": result["fuzzy_matches"],
                "loaded_names": all_names,
                "truncated": False,
            }

    result = _match_keywords(all_names, keywords)
    return {
        "exact_matches": result["exact_matches"],
        "fuzzy_matches": result["fuzzy_matches"],
        "loaded_names": all_names,
        "truncated": True,
    }


async def resolve_entities_for_domain(
    deps: GraphDeps,
    tenant_id: str,
    question: str,
    domain: SqlQueryDomain,
) -> dict[str, Any]:
    """Orchestrate entity resolution for a given domain.

    Returns dict keyed by entity type (e.g. "products", "suppliers"),
    each containing {exact_matches, fuzzy_matches, loaded_names, truncated}.
    Returns empty dict if disabled, generic domain, or no entities mapped.
    """
    settings = getattr(deps, "settings", None)
    if not settings or not getattr(settings, "entity_resolution_enabled", True):
        return {}
    if domain == "generic":
        return {}
    executor = getattr(deps, "sql_executor", None)
    if executor is None:
        return {}

    batch_size = int(getattr(settings, "entity_resolution_batch_size", 500))
    max_batches = int(getattr(settings, "entity_resolution_max_batches", 3))
    keywords = _extract_keywords(question, domain)
    entities = _ENTITY_MAP.get(domain, [])

    result: dict[str, Any] = {}
    for ent in entities:
        table = ent["table"]
        column = ent["column"]
        ent_result = await load_entity_names(
            executor, tenant_id, table, column, keywords,
            batch_size=batch_size, max_batches=max_batches,
        )
        if ent_result["loaded_names"]:
            result[table] = ent_result

    return result
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd ai_python && pytest tests/test_entity_resolution.py -v
```
Expected: All tests PASS.

---

### Task 3: Add state key + prompt injection

**Files:**
- Modify: `ai_python/app/graph/state.py`
- Modify: `ai_python/app/graph/nodes/sql_pipeline.py`

- [ ] **Step 1: Add `entity_context` to AgentState**

In `ai_python/app/graph/state.py`, add key to the `AgentState` TypedDict:

```python
    entity_context: NotRequired[dict[str, Any]]
```

Also confirm import of `Any` is present.

- [ ] **Step 2: Add `make_entity_resolution_node()` factory in sql_pipeline.py**

Follow the pattern in `make_execute_sql_node` — synchronous function that wraps an async inner function with `loop.run_until_complete`:

```python
def make_entity_resolution_node(deps: GraphDeps):
    """Return a node function that resolves entity names before gen_sql."""
    from app.graph.entity_resolution import resolve_entities_for_domain

    async def _resolve(state: AgentState) -> dict[str, Any]:
        question = latest_human_question(state)
        if not question:
            return {}
        domain = detect_sql_query_domain(state)
        if domain == "generic":
            return {}
        tenant_id = str(state.get("tenant_id", ""))
        if not tenant_id:
            return {}

        entity_context = await resolve_entities_for_domain(
            deps, tenant_id, question, domain
        )
        return {"entity_context": entity_context}

    def resolve_node(state: AgentState) -> dict[str, Any]:
        try:
            import asyncio
            return asyncio.get_event_loop().run_until_complete(_resolve(state))
        except Exception as exc:
            logger.warning("entity resolution node failed: %s", exc)
            return {}

    return resolve_node
```

- [ ] **Step 3: Inject entity_context into gen_sql prompt**

Inside `make_gen_sql_node` or wherever the SQL generation prompt is built, add a section for entity context. Look for where `additional_context` or similar injection happens and add:

```python
def _build_entity_context_section(state: AgentState) -> str:
    ec = state.get("entity_context")
    if not ec:
        return ""
    lines = ["### Entity Name References (from database)"]
    for table, data in ec.items():
        names = data.get("exact_matches") or data.get("loaded_names", [])[:10]
        if names:
            lines.append(f"- {table}: {', '.join(names)}")
    return "\n".join(lines) if len(lines) > 1 else ""
```

Add the output of `_build_entity_context_section(state)` to the prompt passed to the LLM for SQL generation.

---

### Task 4: Wire node into subgraph

**Files:**
- Modify: `ai_python/app/graph/sql_subgraph.py`

- [ ] **Step 1: Import the factory at top of sql_subgraph.py**

```python
from app.graph.nodes.sql_pipeline import make_entity_resolution_node
```

- [ ] **Step 2: Add node and edge between schema_explore and gen_sql**

Inside the subgraph builder, after `schema_explore` is added:

```python
    # Entity resolution
    if deps.settings.entity_resolution_enabled:
        subgraph.add_node("resolve_entities", make_entity_resolution_node(deps))
        subgraph.add_edge("schema_explore", "resolve_entities")
        subgraph.add_edge("resolve_entities", "gen_sql")
    else:
        subgraph.add_edge("schema_explore", "gen_sql")
```

This requires replacing the direct `schema_explore -> gen_sql` edge with a conditional.

- [ ] **Step 3: Add integration test**

Create `ai_python/tests/test_sql_subgraph_entity_resolution.py`:

```python
"""Test that entity resolution node is correctly wired into the subgraph."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.config.graph_settings import GraphSettings
from app.graph.deps import GraphDeps
from app.graph.nodes.sql_pipeline import make_entity_resolution_node


class TestEntityResolutionNodeWiring:
    @pytest.fixture
    def deps(self):
        d = MagicMock(spec=GraphDeps)
        d.settings = MagicMock(spec=GraphSettings)
        d.settings.entity_resolution_enabled = True
        d.settings.entity_resolution_batch_size = 500
        d.settings.entity_resolution_max_batches = 3
        executor = AsyncMock()
        executor.aexecute.return_value = {"rows": [{"name": "Áo Thun Nam"}]}
        d.sql_executor = executor
        return d

    def test_node_returns_entity_context(self, deps):
        node_fn = make_entity_resolution_node(deps)
        state = {
            "messages": [{"role": "user", "content": "doanh thu áo thun nam"}],
            "domain": "inventory",
            "tenant_id": "t1",
        }
        result = node_fn(state)
        assert "entity_context" in result
        entity_context = result["entity_context"]
        assert isinstance(entity_context, dict)

    def test_node_returns_empty_for_no_question(self, deps):
        node_fn = make_entity_resolution_node(deps)
        state = {"messages": [], "tenant_id": "t1"}
        result = node_fn(state)
        assert result == {}
```

---

### Task 5: Wire into thin-adapter path (sql_query.py)

**Files:**
- Modify: `ai_python/app/graph/tools/sql_query.py`

- [ ] **Step 1: Add entity resolution call before generate in thin-adapter closure**

In `sql_query.py`, find where `generate(...)` is called (the thin-adapter path that skips the full subgraph). Before the generate call, add:

```python
    # Entity resolution
    entity_context = {}
    try:
        import asyncio
        from app.graph.entity_resolution import resolve_entities_for_domain

        domain = detect_sql_query_domain(state)
        if domain != "generic":
            entity_context = asyncio.get_event_loop().run_until_complete(
                resolve_entities_for_domain(deps, tenant_id, question, domain)
            )
    except Exception as exc:
        logger.warning("entity resolution (thin adapter) failed: %s", exc)

    # Inject into prompt context
    additional_context = additional_context or ""
    if entity_context:
        ctx_lines = ["### Entity Name References (from database)"]
        for table, data in entity_context.items():
            names = data.get("exact_matches") or data.get("loaded_names", [])[:10]
            if names:
                ctx_lines.append(f"- {table}: {', '.join(names)}")
        additional_context += "\n" + "\n".join(ctx_lines)
```

---

### Task 6: Inject entity_context into gen_sql prompt

**Files:**
- Modify: `ai_python/app/graph/nodes/sql_pipeline.py`

- [ ] **Step 1: Enhance gen_sql system prompt with entity context**

Inside `make_gen_sql_node`, where the system prompt is assembled, add:

```python
    entity_section = _build_entity_context_section(state)
    if entity_section:
        sys_prompt += "\n\n" + entity_section
```

Where `_build_entity_context_section` is defined as a module-level helper in `sql_pipeline.py`.

---

### Verification

- [ ] **Step 1: Run all unit tests**

```bash
cd ai_python && pytest tests/test_entity_resolution.py tests/test_sql_subgraph_entity_resolution.py -v
```

- [ ] **Step 2: Run full test suite to ensure no regressions**

```bash
cd ai_python && pytest -x
```
