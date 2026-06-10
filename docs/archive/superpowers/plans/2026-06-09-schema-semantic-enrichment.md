# Schema Semantic Enrichment Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Teach LLM what data lives in each table/column/relationship by enriching the schema artifact with semantic descriptions — eliminating wrong-table / wrong-filter errors (e.g., filtering `products.name` instead of `categories.name` for "gạo").

**Architecture:** Use existing `ai_column_description` registry + new `ai_relationship_description` registry to store semantic context. Both are fetched during `_build_snapshot()` and rendered in the enriched schema block (`_lines_enriched()`). No new graph nodes, no new tools, no reduction in agentic flexibility.

**Tech Stack:** PostgreSQL (registry tables), Python (psycopg2), LangGraph (schema pipeline)

---

## File Structure

```
Data (registry SQL scripts):
  scripts/schema/seed_column_descriptions.sql    — INSERT semantic column descriptions
  scripts/schema/seed_relationship_descriptions.sql — INSERT relationship descriptions
  scripts/schema/create_relationship_registry.sql  — CREATE TABLE ai_relationship_description

Modify:
  ai_python/app/graph/pg_schema_context.py        — Add _fetch_relationship_descriptions() + enrich snapshot
  ai_python/app/graph/sql_prompts.py              — Add "Relationships:" section in _lines_enriched()
  ai_python/app/graph/dbmeta.py                   — Optional: add relationship_descriptions field
```

---

### Task 1: Create `ai_relationship_description` registry table

**Files:**
- Create: `scripts/schema/create_relationship_registry.sql`

- [ ] **Step 1: Write SQL to create registry table**

```sql
CREATE TABLE IF NOT EXISTS public.ai_relationship_description (
    id SERIAL PRIMARY KEY,
    from_table VARCHAR(255) NOT NULL,
    from_column VARCHAR(255) NOT NULL,
    to_table VARCHAR(255) NOT NULL,
    to_column VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (from_table, from_column, to_table, to_column)
);

COMMENT ON TABLE public.ai_relationship_description IS
    'Business description for FK relationships — tells LLM what the relationship means in business terms.';

COMMENT ON COLUMN public.ai_relationship_description.from_table IS 'Source table of the FK';
COMMENT ON COLUMN public.ai_relationship_description.from_column IS 'FK column in source table';
COMMENT ON COLUMN public.ai_relationship_description.to_table IS 'Referenced (target) table';
COMMENT ON COLUMN public.ai_relationship_description.to_column IS 'Referenced PK column';
COMMENT ON COLUMN public.ai_relationship_description.description IS
    'Business semantics of this relationship. E.g. "Mỗi sản phẩm thuộc một danh mục. Filter danh mục dùng categories.name"';
```

- [ ] **Step 2: Commit**

```bash
git add scripts/schema/create_relationship_registry.sql
git commit -m "feat(schema): create ai_relationship_description registry table"
```

---

### Task 2: Populate `ai_column_description` with semantic data

**Files:**
- Create: `scripts/schema/seed_column_descriptions.sql`

- [ ] **Step 1: Write seed SQL**

```sql
-- Semantic descriptions for critical columns.
-- Each description tells LLM what kind of data lives in the column.
-- Format: (table_name, column_name, description)

INSERT INTO public.ai_column_description (table_name, column_name, description)
VALUES
    -- Categories
    ('categories', 'name',
     'Tên danh mục sản phẩm (vd: Gạo, Điện tử, Thực phẩm, Nước giải khát, Hóa mỹ phẩm). '
     'Khi user hỏi theo danh mục (gạo, điện tử...), FILTER bằng cột này, KHÔNG filter products.name.'),

    -- Products
    ('products', 'name',
     'Tên sản phẩm cụ thể (vd: Gạo ST25 5kg, Nước mắm Nam Ngư 500ml, Bột giặt OMO 1kg). '
     'Không chứa tên danh mục chung chung. Để lọc theo danh mục, dùng categories.name qua JOIN categories.'),

    ('products', 'status',
     'Trạng thái master data: Active (đang kinh doanh) hoặc Inactive (ngưng). '
     'Không dùng status để xác định hàng tồn / hết hàng.'),

    -- Inventory
    ('inventory', 'quantity',
     'Số lượng tồn kho thực tế hiện tại (snapshot). Đây là fact, không tính toán từ chứng từ. '
     'out-of-stock = quantity = 0; low_stock = quantity > 0 AND quantity <= min_stock.'),

    -- Finance Ledger
    ('financeledger', 'amount',
     'Số tiền giao dịch tài chính. Dương với doanh thu/thu, âm với chi phí/trả hàng. '
     'transaction_type xác định bản chất: SalesRevenue = doanh thu, PurchaseCost = giá vốn, OperatingExpense = chi phí.'),

    ('financeledger', 'transaction_type',
     'Loại giao dịch tài chính: SalesRevenue (doanh thu), PurchaseCost (giá vốn), '
     'OperatingExpense (chi phí), Refund (trả hàng/hoàn tiền).'),

    ('financeledger', 'transaction_date',
     'Ngày ghi nhận giao dịch tài chính (ngày chứng từ, không phải ngày tạo). '
     'Dùng cho lọc thời gian: tháng/năm/quý.'),

    -- Sales Orders
    ('salesorders', 'order_channel',
     'Kênh bán hàng: Retail (bán lẻ tại quầy/POS), Wholesale (bán sỉ), Return (đơn trả). '
     'Chỉ filter Retail khi user hỏi cụ thể "bán lẻ" hoặc "tại quầy".'),

    ('salesorders', 'status',
     'Trạng thái đơn hàng: Pending, Processing, Partial, Shipped, Delivered, Cancelled. '
     'Đơn đã huỷ (Cancelled) không tính vào doanh số.'),

    -- Stock Receipts
    ('stockreceipts', 'status',
     'Trạng thái phiếu nhập: Draft, Pending, Approved, Rejected. '
     'Chỉ Approved mới là nhập kho chính thức.'),

    -- Stock Dispatches
    ('stockdispatches', 'status',
     'Trạng thái phiếu xuất: Pending, Full, Partial, Cancelled, WaitingDispatch, Delivering, Delivered. '
     'Đơn đã huỷ (Cancelled) không tính. active rows: deleted_at IS NULL.')
ON CONFLICT (table_name, column_name) DO UPDATE
    SET description = EXCLUDED.description,
        updated_at = now();
```

- [ ] **Step 2: Commit**

```bash
git add scripts/schema/seed_column_descriptions.sql
git commit -m "feat(schema): seed semantic column descriptions for key tables"
```

---

### Task 3: Populate `ai_relationship_description` with semantic data

**Files:**
- Create: `scripts/schema/seed_relationship_descriptions.sql`

- [ ] **Step 1: Write seed SQL**

```sql
INSERT INTO public.ai_relationship_description (from_table, from_column, to_table, to_column, description)
VALUES
    ('products', 'category_id', 'categories', 'id',
     'Mỗi sản phẩm thuộc về một danh mục. Khi user hỏi "gạo", "điện tử", "thực phẩm" — '
     'đó là categories.name. JOIN categories và filter c.name, KHÔNG filter products.name.'),

    ('inventory', 'product_id', 'products', 'id',
     'Mỗi dòng tồn kho tương ứng với một sản phẩm. JOIN products để lấy tên, mã SKU, min_stock.'),

    ('inventory', 'location_id', 'warehouselocations', 'id',
     'Mỗi dòng tồn kho thuộc một vị trí kho. JOIN warehouselocations để lấy tên kho/giá.'),

    ('stockreceiptdetails', 'receipt_id', 'stockreceipts', 'id',
     'Chi tiết của phiếu nhập — mỗi dòng là một sản phẩm trong phiếu nhập. '
     'stockreceipts.status phải là Approved mới tính.'),

    ('stockreceiptdetails', 'product_id', 'products', 'id',
     'Sản phẩm trong phiếu nhập. JOIN products để lấy tên/mã.'),

    ('stockdispatch_lines', 'dispatch_id', 'stockdispatches', 'id',
     'Chi tiết của phiếu xuất — mỗi dòng là một sản phẩm trong phiếu xuất.'),

    ('stockdispatch_lines', 'product_id', 'products', 'id',
     'Sản phẩm trong phiếu xuất.'),

    ('orderdetails', 'order_id', 'salesorders', 'id',
     'Chi tiết đơn hàng — mỗi dòng là một sản phẩm trong đơn. salesorders.status != Cancelled.'),

    ('orderdetails', 'product_id', 'products', 'id',
     'Sản phẩm trong đơn hàng. Dùng để tính số lượng bán.'),

    ('financeledger', 'reference_type', NULL, NULL,
     'Phân loại tham chiếu: SalesOrder, PurchaseInvoice, ... '
     'JOIN với bảng tương ứng theo reference_id khi cần thông tin chi tiết.'),

    ('productpricehistory', 'product_id', 'products', 'id',
     'Lịch sử giá sản phẩm. Mỗi sản phẩm có nhiều dòng giá theo thời gian. '
     'JOIN bằng LATERAL hoặc DISTINCT ON để lấy giá mới nhất.'),

    ('productpricehistory', 'unit_id', 'productunits', 'id',
     'Đơn vị tính của giá. Giá theo đơn vị cơ sở khi is_base_unit = TRUE.')
ON CONFLICT (from_table, from_column, to_table, to_column) DO UPDATE
    SET description = EXCLUDED.description,
        updated_at = now();
```

- [ ] **Step 2: Commit**

```bash
git add scripts/schema/seed_relationship_descriptions.sql
git commit -m "feat(schema): seed semantic relationship descriptions for key FK relationships"
```

---

### Task 4: Fetch relationship descriptions in schema snapshot

**Files:**
- Modify: `ai_python/app/graph/pg_schema_context.py`

- [ ] **Step 1: Add `_fetch_relationship_descriptions()` function**

Add after `_fetch_column_descriptions()` (after line 158):

```python
def _fetch_relationship_descriptions(
    cur: Any, *, schema: str, registry_table: str
) -> list[dict[str, str]]:
    """Fetch business descriptions for FK relationships from ai_relationship_description."""
    if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", schema) or not re.match(
        r"^[A-Za-z_][A-Za-z0-9_]*$", registry_table
    ):
        raise ValueError("invalid schema or registry_table identifier for ai_relationship_description")
    q = f"""
        SELECT from_table, from_column, to_table, to_column, COALESCE(description, '')
        FROM {schema}.{registry_table}
        ORDER BY from_table, from_column
    """
    cur.execute(q)
    return [
        {
            "from_table": str(r[0]),
            "from_column": str(r[1]),
            "to_table": str(r[2]) if r[2] else "",
            "to_column": str(r[3]) if r[3] else "",
            "description": str(r[4]),
        }
        for r in cur.fetchall()
    ]
```

- [ ] **Step 2: Add field to `_SchemaSnapshot`**

Add `rel_desc_map` to `_SchemaSnapshot` (after `col_desc_map` at line 34):

Change:
```python
    col_desc_map: dict[tuple[str, str], str]
```
to:
```python
    col_desc_map: dict[tuple[str, str], str]
    rel_desc_map: dict[tuple[str, str, str, str], str]
```

- [ ] **Step 3: Call the fetcher in `_build_snapshot()`**

In `_build_snapshot()`, after the `col_desc_map` block (after line 501), add:

```python
    rel_desc_map: dict[tuple[str, str, str, str], str] = {}
    try:
        raw_rels = _fetch_relationship_descriptions(
            cur,
            schema=schema,
            registry_table=col_desc_table.replace("ai_column_description", "ai_relationship_description"),
        )
        for r in raw_rels:
            key = (r["from_table"].lower(), r["from_column"].lower(),
                   (r["to_table"] or "").lower(), (r["to_column"] or "").lower())
            rel_desc_map[key] = r["description"]
    except Exception as exc:  # noqa: BLE001
        logger.warning("ai_relationship_description unavailable: %s", exc)
```

Update the `_SchemaSnapshot` constructor return at the bottom of `_build_snapshot()` to include `rel_desc_map`.

- [ ] **Step 4: Add relationship descriptions to `_artifact_from_snapshot()`**

In `_artifact_from_snapshot()` (around line 556), before appending to `tmeta`, merge relationship descriptions into the table:

```python
        # Gather relationship descriptions for this table's FKs
        rel_lines: list[str] = []
        for fk in tmeta_fks:
            key = (tname.lower(), fk.get("column", "").lower(),
                   (fk.get("ref_table") or "").lower(), (fk.get("ref_column") or "").lower())
            desc = snapshot.rel_desc_map.get(key)
            if desc:
                rel_lines.append(f"  {fk['column']} → {fk['ref_table']}.{fk['ref_column']}: {desc}")
```

But wait — `TableMeta` doesn't have a field for relationship descriptions yet. I need to either:
- Add a field to `TableMeta`, or
- Just enrich the FK dicts, or
- Store it differently

The simplest approach: just pass it as metadata in the table for rendering. Let me add a `relationship_hints: list[str]` field to `TableMeta`.

- [ ] **Step 5: Run tests to verify no regression**

Run: `$env:PYTHONPATH="D:\do_an_tot_nghiep\project\ai_python"; python -m pytest ai_python/tests/ -q --tb=short`
Expected: Same as baseline (2 pre-existing failures)

- [ ] **Step 6: Commit**

```bash
git add ai_python/app/graph/pg_schema_context.py
git commit -m "feat(schema): fetch relationship descriptions from registry"
```

---

### Task 5: Render relationship descriptions in enriched schema block

**Files:**
- Modify: `ai_python/app/graph/sql_prompts.py`
- Modify: `ai_python/app/graph/dbmeta.py`

- [ ] **Step 1: Add `relationship_hints` field to `TableMeta`**

In `dbmeta.py`, add field to `TableMeta` class (after `distinct_values`):

```python
    relationship_hints: list[str] = Field(
        default_factory=list,
        description="Business descriptions of FK relationships, e.g. 'products.category_id → categories.id: Each product belongs to a category'.",
    )
```

- [ ] **Step 2: Store relationship hints in `_artifact_from_snapshot()`**

In `pg_schema_context.py`, in `_artifact_from_snapshot()`, after building `merged_cols`, before creating `TableMeta`:

```python
        # Build relationship hints for this table
        rel_hints: list[str] = []
        for fk in snapshot.fks.get(tname, []):
            key = (tname.lower(), fk.get("column", "").lower(),
                   (fk.get("ref_table") or "").lower(), (fk.get("ref_column") or "").lower())
            desc = snapshot.rel_desc_map.get(key)
            if desc:
                rel_hints.append(f"{fk['column']} → {fk['ref_table']}.{fk['ref_column']}: {desc}")
```

Add `relationship_hints=rel_hints` to the `TableMeta` constructor call.

- [ ] **Step 3: Render relationship hints in `_lines_enriched()`**

In `sql_prompts.py`, in `_lines_enriched()`, after the FKs block (after line 72), add:

```python
        if t.relationship_hints:
            head += "\nRelationships:\n" + "\n".join(f"  {h}" for h in t.relationship_hints)
```

- [ ] **Step 4: Run tests**

Run: `$env:PYTHONPATH="D:\do_an_tot_nghiep\project\ai_python"; python -m pytest ai_python/tests/ -q --tb=short`
Expected: Same as baseline (2 pre-existing failures)

- [ ] **Step 5: Commit**

```bash
git add ai_python/app/graph/sql_prompts.py ai_python/app/graph/dbmeta.py ai_python/app/graph/pg_schema_context.py
git commit -m "feat(schema): render relationship descriptions in enriched schema block"
```

---

### Task 6: Verify the enriched output reaches gen_sql

**Files:** None (verification only)

- [ ] **Step 1: Run a test query to verify schema enrichment**

```bash
$env:PYTHONPATH="D:\do_an_tot_nghiep\project\ai_python"; python -c "
from unittest.mock import MagicMock, patch
from app.graph.sql_prompts import _lines_enriched
from app.graph.dbmeta import SchemaArtifact, TableMeta, ColumnMeta

t = TableMeta(
    name='products',
    columns=[ColumnMeta(name='name', type='varchar', description='Tên sản phẩm cụ thể...')],
    pk=['id'],
    fks=[{'column': 'category_id', 'ref_table': 'categories', 'ref_column': 'id'}],
    relationship_hints=['category_id → categories.id: Mỗi sản phẩm thuộc một danh mục...'],
    description='Product master data',
)
a = SchemaArtifact(schema_version='test', tables=[t])
lines = _lines_enriched(a, table_names=['products'])
output = '\n\n'.join(lines)
print(output)
assert 'category_id → categories.id' in output
assert 'Tên sản phẩm' in output
assert 'Relationships:' in output
print('VERIFIED: enriched schema block contains semantic descriptions')
"
```

Expected: Output shows products table with column descriptions + FK descriptions + Relationships section.

- [ ] **Step 2: Full regression test**

Run: `$env:PYTHONPATH="D:\do_an_tot_nghiep\project\ai_python"; python -m pytest ai_python/tests/ -q --tb=short`
Expected: 2 pre-existing failures, no new failures

---

## Summary

| Task | What | Type | Code change |
|------|------|------|-------------|
| 1 | Create `ai_relationship_description` table | Data infra | 1 SQL file |
| 2 | Seed `ai_column_description` | Data | 1 SQL file (~11 rows) |
| 3 | Seed `ai_relationship_description` | Data | 1 SQL file (~12 rows) |
| 4 | Fetch relationship descriptions | Code | ~30 lines in pg_schema_context.py |
| 5 | Render in enriched schema | Code | ~10 lines in sql_prompts.py + 3 in dbmeta.py |
| 6 | Verify output | Check | None |

Total code added: ~45 lines across 3 Python files + 3 SQL seed files.
Total new infrastructure: 1 registry table + 2 seed scripts.
Zero new tools, zero new graph nodes, zero reduction in agentic flexibility.
