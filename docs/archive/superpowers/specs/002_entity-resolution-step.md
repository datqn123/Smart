# Entity Resolution Step for SQL Pipeline

> **Goal:** Add a pre-`gen_sql` entity resolution step that loads actual entity names from the database and injects them into the LLM prompt, so generated SQL uses exact names (products, suppliers, categories, transaction types) instead of guessed ones.

---

## 1. Problem

When a user asks for products or other entities, the LLM often guesses names that don't match what's in the database. For example:
- User: *"doanh thu tháng 2 năm nay của áo thun nam"*
- LLM generates: `WHERE product_name = 'Áo Thun Nam'`
- But DB has: `Áo Thun Nam Tay Ngắn`, `Áo Thun Nam Tay Dài`, etc.
- Result: empty or incomplete

Existing `analyze_empty_result` detects this (exact name match heuristic) but cannot fix it — it has no entity list to correct the SQL against.

## 2. Solution

Add a single **`resolve_entities`** step that runs **before** `gen_sql` in the SQL pipeline. This step loads actual entity names from the database in batches, matches them against keywords from the user's question, and injects exact names into the prompt.

## 3. Architecture

### 3.1 Pipeline Position

New step inserted in `sql_subgraph.py`:

```
Current:                           New:
START                               START
  │                                   │
  v                                   v
schema_explore                     schema_explore
  │                                   │
  v                                   v
gen_sql                  ──→     resolve_entities  ←── MỚI
  │                                   │
  v                                   v
verify_sql_intent                 gen_sql (receives entity_context)
  │                                   │
  v                                   v
sql_review                        verify_sql_intent (unchanged)
...                                 ...
```

### 3.2 Entity Mapping

Based on domain (detected by existing `detect_sql_query_domain()`):

| Domain | Entity Table | Column | Table Schema |
|--------|-------------|--------|-------------|
| inventory | `products` | `name` | `products(id, name, sku_code, ...)` |
| receipt | `products` | `name` | `products(id, name, ...)` |
| receipt | `suppliers` | `name` | `suppliers(id, name, ...)` |
| dispatch | `products` | `name` | `products(id, name, ...)` |
| ledger | `financeledger` | `transaction_type` | `financeledger(id, transaction_type, ...)` — distinct values |
| catalog_price | `products` | `name` | `products(id, name, ...)` |
| catalog_price | `categories` | `name` | `categories(id, name, ...)` |

Generic domain: skip entity resolution.

### 3.3 Batch Load Strategy

Use the existing `deps.sql_executor.aexecute()` (same as `execute` callable).

```python
async def load_entity_names(
    executor,
    table: str,
    column: str,
    user_keywords: list[str],
    batch_size: int = 500,
    max_batches: int = 3,
) -> dict:
    """
    SELECT DISTINCT {column} FROM {table} ORDER BY {column}
    
    Load batches sequentially:
      Batch 1: LIMIT 500 OFFSET 0
      Batch 2: LIMIT 500 OFFSET 500  (if no match yet)
      Batch 3: LIMIT 500 OFFSET 1000 (if no match yet)
    
    After each batch, check if any user_keyword matches loaded names
    (case-insensitive exact match OR contains match).
    
    Returns: { exact_matches: list[str], loaded_names: list[str], truncated: bool }
    """
```

**Match logic (per batch):**
1. For each `user_keyword`, check `name.lower() == keyword.lower()` — case-insensitive exact match
2. If exact match found → add to `exact_matches`, stop loading further batches (no more DB queries)
3. If no exact match after this batch but keyword is a **word-substring** of some name (i.e., `keyword.lower() in name.lower().split()`) → record as `fuzzy_matches`, continue next batch
4. After all batches exhausted: return `fuzzy_matches` if any, else return all `loaded_names` as reference

**Stop condition:** Exact match found OR max_batches reached.

**Keyword extraction from user question:**
1. Tokenize question into words (split on spaces + punctuation).
2. Filter out: domain-specific phrases from `sql_query_domain.py` (e.g., "tồn kho", "doanh thu"), common Vietnamese stopwords (của, và, các, những, cho, trong, tại, từ, đến, với, có, không, đã, đang, sẽ, này, kia, đó, những, một, hai, ba, bốn, năm, tháng, ngày, năm, quý, tuần).
3. Remaining words are candidate `user_keywords`.
4. If no keywords remain (e.g., generic question like "liệt kê sản phẩm"), use top 10 product names from first batch as fallback.

### 3.4 Prompt Injection

In `gen_sql` prompt, a new section is appended:

```
### Entity Reference (from database)
Products: ["Áo Thun Nam Tay Ngắn", "Áo Thun Nam Tay Dài", "Áo Sơ Mi", ...]
Suppliers: ["Công ty TNHH ABC", "Công ty XYZ", ...]

IMPORTANT: Use EXACT names from the lists above in WHERE clauses.
Do not guess or approximate entity names.
```

If entity resolution is disabled or returns no data, this section is omitted.

### 3.5 State

New key in `AgentState`:

```python
entity_context: dict[str, Any] = {
    "products": {"exact_matches": [...], "loaded_names": [...]},
    "suppliers": {"exact_matches": [...], "loaded_names": [...]},
    "categories": {"exact_matches": [...], "loaded_names": [...]},
    "transaction_types": {"exact_matches": [...], "loaded_names": [...]},
    "truncated": False,  # True if any entity hit max_batches without full scan
}
```

## 4. Config

New settings in `GraphSettings`:

| Setting | Default | Description |
|---------|---------|-------------|
| `entity_resolution_enabled` | `True` | Master on/off |
| `entity_resolution_batch_size` | `500` | Rows per batch |
| `entity_resolution_max_batches` | `3` | Max batches per entity type |

## 5. Files Changed

| File | Change |
|------|--------|
| `ai_python/app/graph/nodes/sql_pipeline.py` | Add `make_entity_resolution_node()` factory |
| `ai_python/app/graph/sql_subgraph.py` | Wire `resolve_entities` node before `gen_sql` |
| `ai_python/app/graph/tools/sql_query.py` | Integrate entity resolution into `_make_callables` generate closure |
| `ai_python/app/config/graph_settings.py` | Add 3 new config fields |
| `ai_python/tests/` | New test file `test_entity_resolution.py` + integration test updates |

## 6. Error Handling

- SQL executor failure during load → log warning, skip entity resolution, proceed without entity context
- Timeout on large table → truncated flag set, system proceeds with whatever names loaded
- Empty result from load (table has no rows) → skip, no entity section in prompt

## 7. Testing

| Test | Description |
|------|-------------|
| `test_loads_product_names_in_batches` | Mock executor returns pages, verify batch logic |
| `test_stops_after_exact_match` | First batch contains keyword, verify no more batches fetched |
| `test_exhausts_batches_returns_truncated` | No match after max_batches, verify truncated=True |
| `test_injects_entity_context_into_prompt` | Integration: verify gen_sql prompt contains entity section |
| `test_skips_when_disabled` | `entity_resolution_enabled=False`, verify no change to normal flow |
| `test_handles_executor_error` | Executor raises, verify graceful fallback |
