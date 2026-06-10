# Kế hoạch Triển khai Schema Data Introspection

> **Dành cho agent workers:** BẮT BUỘC SUB-SKILL: Sử dụng superpowers:subagent-driven-development (khuyến nghị) hoặc superpowers:executing-plans để triển khai plan này theo từng task. Các bước dùng checkbox (`- [ ]`) để theo dõi tiến độ.

**Mục tiêu:** Loại bỏ các lần retry empty-result bằng cách cung cấp cho LLM dữ liệu thực tế (sample rows, distinct values của enum columns) trước khi nó sinh SQL.

**Kiến trúc:** Mở rộng pipeline `_build_snapshot` → `_SchemaSnapshot` → `SchemaArtifact` hiện tại với các truy vấn introspection dữ liệu tại thời điểm build snapshot. Cache dữ liệu introspection cùng với schema metadata bằng `SchemaArtifactCache` hiện có (cùng fingerprint + TTL). Thêm background warmer để trigger snapshot build lúc app startup, giúp introspection data có sẵn trước câu hỏi đầu tiên. Thêm block "Introspection" vào enriched schema prompt section.

**Tech Stack:** psycopg2, threading, pydantic, `SchemaArtifactCache` hiện tại

---

## Cấu trúc File

| File | Thay đổi | Trách nhiệm |
|------|----------|-------------|
| `app/graph/dbmeta.py` | Sửa | Thêm `sample_rows` và `distinct_values` vào `TableMeta` |
| `app/graph/pg_schema_context.py` | Sửa | Thêm introspection queries trong `_build_snapshot`; thêm fields vào `_SchemaSnapshot`; thêm class `SchemaWarmupWarmer` |
| `app/graph/sql_prompts.py` | Sửa | Thêm introspection block trong `_lines_enriched` |
| `app/config/graph_settings.py` | Sửa | Thêm 4 config flags mới |
| `main.py` | Sửa | Start `SchemaWarmupWarmer` trong lifespan |

---

### Task 1: Mở rộng `TableMeta` và `_SchemaSnapshot`

**Files:**
- Modify: `app/graph/dbmeta.py:25-33`
- Modify: `app/graph/pg_schema_context.py:19-28`

- [ ] **Bước 1: Thêm fields vào `TableMeta`**

```python
class TableMeta(BaseModel):
    name: str
    columns: list[ColumnMeta] = Field(default_factory=list)
    pk: list[str] = Field(default_factory=list)
    fks: list[dict[str, Any]] = Field(default_factory=list)
    description: str | None = Field(default=None)
    sample_rows: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Up to N sample rows for LLM to infer data format.",
    )
    distinct_values: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Column name -> distinct non-null values for enum-like text columns.",
    )
```

- [ ] **Bước 2: Thêm fields vào `_SchemaSnapshot`**

```python
@dataclass(frozen=True)
class _SchemaSnapshot:
    rows: list[tuple[str, str]]
    desc_map: dict[str, str]
    reg_names: set[str]
    fk_edges: list[tuple[str, str, str, str]]
    cols: dict[str, list[ColumnMeta]]
    pks: dict[str, list[str]]
    fks: dict[str, list[dict[str, Any]]]
    col_desc_map: dict[tuple[str, str], str]
    sample_rows: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    distinct_values: dict[str, dict[str, list[str]]] = field(default_factory=dict)
```

- [ ] **Bước 3: Cập nhật helper `_snapshot()` trong `tests/test_pg_schema_cache.py`** — thêm `sample_rows={}, distinct_values={}`

- [ ] **Bước 4: Chạy tests**

Run: `pytest tests/test_pg_schema_cache.py -v`
Expected: 2 PASSED

- [ ] **Bước 5: Commit**

```bash
git add ai_python/app/graph/dbmeta.py ai_python/app/graph/pg_schema_context.py ai_python/tests/test_pg_schema_cache.py
git commit -m "feat: add sample_rows and distinct_values fields to TableMeta and _SchemaSnapshot"
```

---

### Task 2: Thêm introspection queries

**Files:**
- Modify: `app/graph/pg_schema_context.py` — thêm 3 functions trước `_build_snapshot`

- [ ] **Bước 1: Thêm import**

```python
try:
    from psycopg2 import sql as pysql
except ImportError:
    pysql = None
```

- [ ] **Bước 2: Viết `_introspect_sample_rows`**

```python
def _introspect_sample_rows(
    cur: Any, schema: str, table: str, limit: int = 5,
) -> list[dict[str, Any]]:
    safe_name = pysql.Identifier(schema, table)
    cur.execute(pysql.SQL("SELECT * FROM {} LIMIT %s").format(safe_name), (limit,))
    col_names = [desc[0] for desc in cur.description] if cur.description else []
    rows: list[dict[str, Any]] = []
    for row in cur.fetchall():
        d: dict[str, Any] = {}
        for i, c in enumerate(col_names):
            val = row[i]
            if isinstance(val, (bytes, bytearray)):
                val = str(val)[:200]
            elif not isinstance(val, (str, int, float, bool, type(None))):
                val = str(val)[:200]
            d[c] = val
        rows.append(d)
    return rows
```

- [ ] **Bước 3: Viết `_is_categorical_column` và `_introspect_distinct_values`**

```python
_CATEGORICAL_TYPE_KEYWORDS = ("char", "text", "enum", "varchar")

def _is_categorical_column(col: ColumnMeta) -> bool:
    if col.name.lower() in ("id", "created_at", "updated_at", "deleted_at"):
        return False
    if col.type is None:
        return False
    t = col.type.lower()
    return any(kw in t for kw in _CATEGORICAL_TYPE_KEYWORDS) and "[]" not in t

def _introspect_distinct_values(
    cur: Any, schema: str, table: str, columns: list[ColumnMeta], limit: int = 100,
) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for col in columns:
        if not _is_categorical_column(col):
            continue
        safe_table = pysql.Identifier(schema, table)
        safe_col = pysql.Identifier(col.name)
        try:
            cur.execute(
                pysql.SQL("SELECT DISTINCT {} FROM {} WHERE {} IS NOT NULL ORDER BY 1 LIMIT %s")
                .format(safe_col, safe_table, safe_col),
                (limit,),
            )
            vals = [str(r[0]) for r in cur.fetchall() if r[0] is not None]
            if vals:
                result[col.name] = vals
        except Exception:
            logger.warning("introspect distinct failed for %s.%s", table, col.name)
    return result
```

- [ ] **Bước 4: Run static check**

Run: `python -c "import ast; ast.parse(open('ai_python/app/graph/pg_schema_context.py').read())"`

- [ ] **Bước 5: Commit**

---

### Task 3: Tích hợp introspection vào `_build_snapshot` và `_artifact_from_snapshot`

**Files:**
- Modify: `app/graph/pg_schema_context.py`

- [ ] **Bước 1: Trong `_build_snapshot`, sau khi fetch column descriptions, thêm vòng lặp introspection**

```python
    sample_rows: dict[str, list[dict[str, Any]]] = {}
    distinct_values: dict[str, dict[str, list[str]]] = {}
    for tname in all_tables:
        t_cols = cols.get(tname)
        if not t_cols:
            continue
        try:
            sample_rows[tname] = _introspect_sample_rows(cur, schema, tname, limit=5)
        except Exception:
            pass
        try:
            dv = _introspect_distinct_values(cur, schema, tname, t_cols, limit=100)
            if dv:
                distinct_values[tname] = dv
        except Exception:
            pass
```

- [ ] **Bước 2: Thêm `sample_rows` và `distinct_values` vào return `_SchemaSnapshot`**

- [ ] **Bước 3: Trong `_artifact_from_snapshot`, copy introspection data vào `TableMeta`**

```python
tmeta.append(TableMeta(
    name=tname, columns=merged_cols,
    pk=snapshot.pks.get(tname, []), fks=snapshot.fks.get(tname, []),
    description=snapshot.desc_map.get(tname),
    sample_rows=snapshot.sample_rows.get(tname, []),
    distinct_values=snapshot.distinct_values.get(tname, {}),
))
```

- [ ] **Bước 4: Chạy tests** — `pytest tests/test_pg_schema_cache.py -v` → 2 PASSED

- [ ] **Bước 5: Commit**

---

### Task 4: Thêm config settings

**Files:**
- Modify: `app/config/graph_settings.py`

- [ ] **Bước 1: Thêm 4 fields sau dòng 113**

```python
    sql_introspection_enabled: bool = Field(default=True, description="Collect sample rows + distinct values during schema snapshot build.")
    sql_introspection_sample_limit: int = Field(default=5, ge=0, le=20)
    sql_introspection_distinct_limit: int = Field(default=100, ge=0, le=500)
    sql_introspection_warmup_enabled: bool = Field(default=True, description="Build schema snapshot + introspection at app startup.")
```

- [ ] **Bước 2: Thêm `"sql_introspection_enabled"` và `"sql_introspection_warmup_enabled"` vào `coerce_sql_factory_flags` validator list**

- [ ] **Bước 3: Verify** — `python -c "from app.config.graph_settings import GraphSettings; gs = GraphSettings(); print(gs.sql_introspection_enabled, gs.sql_introspection_sample_limit)"`

- [ ] **Bước 4: Commit**

---

### Task 5: Thêm introspection block vào prompt

**Files:**
- Modify: `app/graph/sql_prompts.py` — mở rộng `_lines_enriched`

- [ ] **Bước 1: Sau block FKs, thêm introspection rendering**

```python
        dv = getattr(t, "distinct_values", None)
        if dv:
            dv_lines = []
            for col_name, vals in dv.items():
                preview = ", ".join(str(v) for v in vals[:8])
                more = f" … and {len(vals) - 8} more" if len(vals) > 8 else ""
                dv_lines.append(f"  {col_name}: [{preview}{more}]")
            if dv_lines:
                head += "\nKnown distinct values:\n" + "\n".join(dv_lines)

        sample = getattr(t, "sample_rows", None)
        if sample:
            sample_lines = []
            for i, row in enumerate(sample[:3]):
                truncated = {k: (str(v)[:80] if v is not None else "NULL") for k, v in row.items()}
                sample_lines.append(f"  row{i+1}: {truncated}")
            if sample_lines:
                head += "\nSample rows:\n" + "\n".join(sample_lines)
```

- [ ] **Bước 2: Import check** — `python -c "from app.graph.sql_prompts import format_schema_block; print('ok')"`

- [ ] **Bước 3: Commit**

---

### Task 6: Background warmer lúc app startup

**Files:**
- Modify: `app/graph/pg_schema_context.py` — thêm class `SchemaWarmupWarmer` ở cuối
- Modify: `main.py` — start warmer trong lifespan

- [ ] **Bước 1: Thêm `SchemaWarmupWarmer` class**

```python
import threading

class SchemaWarmupWarmer:
    """Xây dựng schema + introspection cache lúc startup."""

    def __init__(self, settings: GraphSettings) -> None:
        self._settings = settings
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if not self._settings.sql_introspection_warmup_enabled:
            logger.info("schema warmup disabled by config")
            return
        dsn = _metadata_dsn(self._settings)
        if not dsn:
            logger.info("schema warmup skipped — no metadata DSN configured")
            return
        self._thread = threading.Thread(target=self._run, name="schema-warmer", daemon=True)
        self._thread.start()
        logger.info("schema warmup thread started")

    def _run(self) -> None:
        try:
            import psycopg2
        except ImportError:
            logger.warning("schema warmup: psycopg2 not installed")
            return
        dsn = _metadata_dsn(self._settings)
        schema = (self._settings.pg_metadata_schema or "public").strip()
        desc_table = (self._settings.pg_ai_description_table or "ai_table_description").strip()
        col_desc_table = (self._settings.pg_ai_column_description_table or "ai_column_description").strip()
        timeout = int(self._settings.pg_metadata_connect_timeout_seconds)
        try:
            conn = psycopg2.connect(dsn, connect_timeout=timeout)
            conn.set_session(readonly=True, autocommit=True)
            with conn.cursor() as cur:
                snapshot = _build_snapshot(cur, schema=schema, desc_table=desc_table, col_desc_table=col_desc_table)
            conn.close()
            namespace = _cache_namespace(self._settings, dsn)
            conn2 = psycopg2.connect(dsn, connect_timeout=timeout)
            conn2.set_session(readonly=True, autocommit=True)
            with conn2.cursor() as cur2:
                fp = _build_db_fingerprint(cur2, schema=schema, desc_table=desc_table, col_desc_table=col_desc_table)
            conn2.close()
            cache_key = f"{namespace}|{fp}" if fp else f"{namespace}|warmup"
            _SCHEMA_CACHE.set(cache_key, snapshot,
                              ttl_seconds=int(self._settings.schema_cache_ttl_seconds),
                              max_items=int(self._settings.schema_cache_max_items))
            logger.info("schema warmup complete (tables=%d)", len(snapshot.reg_names))
        except Exception:
            logger.warning("schema warmup failed — will lazy-build on first query", exc_info=True)
```

- [ ] **Bước 2: Cập nhật `main.py`**

```python
from app.graph.pg_schema_context import SchemaWarmupWarmer
from app.config.graph_settings import load_graph_settings

@asynccontextmanager
async def lifespan(_app: FastAPI):
    setup_correlation_logging()
    setup_app_package_stderr_logging()
    validate_llm_required(load_llm_settings())
    gs = load_graph_settings()
    warmer = SchemaWarmupWarmer(gs)
    warmer.start()
    yield
```

- [ ] **Bước 3: Verify imports**

```bash
python -c "from app.graph.pg_schema_context import SchemaWarmupWarmer; print('ok')"
python -c "from main import app; print('ok')"
```

- [ ] **Bước 4: Commit**

---

### Task 7: Gắn introspection gate vào build

**Files:**
- Modify: `app/graph/pg_schema_context.py`

- [ ] **Bước 1: Thêm params `introspection_enabled`, `sample_limit`, `distinct_limit` vào `_build_snapshot`**

```python
def _build_snapshot(
    cur: Any, *, schema: str, desc_table: str, col_desc_table: str,
    introspection_enabled: bool = True,
    sample_limit: int = 5, distinct_limit: int = 100,
) -> _SchemaSnapshot:
```

- [ ] **Bước 2: Wrap vòng lặp introspection trong `if introspection_enabled:`**

- [ ] **Bước 3: Cập nhật tất cả call sites** — pass settings values

```python
snapshot = _build_snapshot(cur, schema=schema, desc_table=desc_table, col_desc_table=col_desc_table,
    introspection_enabled=bool(settings.sql_introspection_enabled),
    sample_limit=int(settings.sql_introspection_sample_limit),
    distinct_limit=int(settings.sql_introspection_distinct_limit))
```

- [ ] **Bước 4: Chạy tests** — `pytest tests/test_pg_schema_cache.py -v` → 2 PASSED

- [ ] **Bước 5: Commit**

---

### Task 8: Kiểm tra tích hợp

- [ ] **Bước 1: Verify warmup log**

```bash
cd ai_python && python -c "
from app.config.graph_settings import load_graph_settings
from app.graph.pg_schema_context import SchemaWarmupWarmer
gs = load_graph_settings()
w = SchemaWarmupWarmer(gs)
w.start()
import time; time.sleep(3)
print('warmer started')
"
```

- [ ] **Bước 2: Verify prompt format**

```bash
cd ai_python && python -c "
from app.graph.dbmeta import SchemaArtifact, TableMeta, ColumnMeta
from app.graph.sql_prompts import format_schema_block
artifact = SchemaArtifact(
    schema_version='test',
    tables=[TableMeta(name='orders', columns=[ColumnMeta(name='status', type='varchar')],
                      sample_rows=[{'id': 1, 'status': 'Completed'}],
                      distinct_values={'status': ['Completed', 'Pending', 'Cancelled']})])
block = format_schema_block(artifact, selected_tables=['orders'], enriched=True)
assert 'Known distinct values' in block
assert 'Sample rows' in block
print('Prompt format OK')
"
```

- [ ] **Bước 3: Commit**

---

## Self-Review

**Spec coverage:**
- Distinct values → Task 2 (`_introspect_distinct_values`), Task 5 (prompt)
- Sample data → Task 2 (`_introspect_sample_rows`), Task 5 (prompt)
- FK relationships → đã tồn tại, không cần task mới
- Prefetch/warmup → Task 6 (`SchemaWarmupWarmer`)
- Config on/off → Task 4 (settings), Task 7 (gate)
- Cache reuse → introspection nằm trong `_SchemaSnapshot` đã được cache bởi `SchemaArtifactCache`

**Placeholder scan:** Không có TBDs, TODOs.

**Type consistency:** Tất cả field names đồng nhất giữa các tasks.

**Ambiguity check:**
- Column selection cho distinct → heuristic `_is_categorical_column` bỏ qua ID, timestamps
- Large text → truncate 80 chars trong prompt
- Không có data → `sample_rows`/`distinct_values` rỗng → prompt section không được render

---

## Execution Handoff

Plan hoàn thành tại `docs/superpowers/plans/2026-06-09-schema-introspection.md`. Hai lựa chọn thực thi:

**1. Subagent-Driven (khuyến nghị)** — Dispatch subagent riêng cho từng task, review giữa các task

**2. Inline Execution** — Thực thi tuần tự trong session này, batch với checkpoints

**Bạn chọn cách nào?**
