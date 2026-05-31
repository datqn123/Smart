# SRS - AI Python - Task006 / SQL DB Metadata Production

**Status:** Approved  
**Date:** 2026-05-11  
**MCP_PHASE:** 0  
**PRD:** `docs/ai-python/prd/PRD_task006-sql-dbmeta-production.md`  
**Task ID:** `Task006`  
**Slug:** `sql-dbmeta-production`

---

## 1. Summary & Scope

**Locked decision:** this SRS follows PRD final architecture **Option B**:

- Phase 1 production executor is `http_spring`: Python implements the client-side executor, configuration, tests, and mocks under `ai_python/`.
- `python_ro` is deferred and must remain explicitly unavailable with an actionable failure message.
- DB metadata refresh is a CLI scan + validate workflow that produces YAML compatible with the existing runtime loader.
- Runtime graph flow remains unchanged: `gen_sql -> sql_review -> validate_sql -> execute_sql -> validate_result -> summarize_answer`.

**In scope (`ai_python/`):**

- Define and implement the Python-side SQL executor result/error contract for graph compatibility.
- Implement `HttpSpringSqlExecutor` as an HTTP client for a Spring-owned read-only SQL execution endpoint.
- Harden `build_sql_executor` configuration validation for `stub`, `http_spring`, deferred `python_ro`, timeout, and row limits.
- Preserve defensive read-only SQL checks before dispatching to any non-stub executor.
- Add DB metadata YAML schema validation and a CLI scan/validate workflow.
- Add pytest coverage and operator documentation under `ai_python/`.

**Out of scope:**

- Java/Spring controller, service, security, database, or audit implementation.
- React/TypeScript UI changes.
- Production database schema changes.
- Replacing the existing LangGraph SQL subgraph or runtime graph topology.
- Runtime DB scanning on app startup or request path.

**Handoff note (cross-scope):**

- Spring must own the actual read-only SQL execution endpoint, authorization, auditing, DB connectivity, and production DB policy. Task006 only documents the conceptual contract and implements the Python client side. No Java code is required or permitted for this task.

---

## 2. Stakeholders & Flows

| Actor | Role |
| :-- | :-- |
| AI runtime maintainers | Implement and maintain executor modes, graph compatibility, and metadata loading behavior. |
| Spring integration owners | Provide the downstream read-only SQL execution endpoint and enforce DB authorization/auditing. |
| QA/test owners | Validate safety controls, config behavior, metadata validation, and deterministic graph outputs. |
| Deployment operators | Configure executor mode, endpoint URL, timeouts, row limits, and metadata refresh workflow. |
| Product/Owner | Accept that Task006 ships `http_spring` first, with `python_ro` deferred to a follow-up phase. |

**Main flow - SQL execution via Spring HTTP:**

```text
Graph validates intent and generates SQL
  -> sql_review and validate_sql accept the statement
  -> execute_sql calls HttpSpringSqlExecutor
  -> executor performs defensive read-only, limit, and timeout checks
  -> executor POSTs to Spring read-only SQL endpoint
  -> Spring returns columns/rows/metrics or structured error
  -> executor maps response to graph query_result shape
  -> validate_result and summarize_answer consume deterministic output
```

**Main flow - DB metadata refresh:**

```text
Operator runs metadata scan CLI with safe DB metadata access
  -> CLI introspects table and column metadata
  -> CLI writes candidate YAML artifact
  -> CLI validates artifact against schema
  -> deployment points SCHEMA_DIR/runtime config at validated YAML
  -> runtime loads pre-built YAML only
```

**Manual metadata flow:**

```text
Operator authors or edits YAML manually
  -> operator runs validation CLI
  -> invalid YAML fails with actionable errors
  -> valid YAML can be used by runtime loader
```

**Alternative/error flows:**

- `SQL_EXECUTOR_MODE=stub` remains available for local development and deterministic tests.
- `SQL_EXECUTOR_MODE=python_ro` fails fast as deferred for Task006, with a message pointing to Phase 2 implementation.
- Missing `SPRING_SQL_URL`, invalid timeout, invalid row limit, or unsupported mode fails during configuration/startup.
- Unsafe SQL, multi-statement SQL, DDL/DML, or transaction-control SQL is rejected before HTTP dispatch.
- Spring timeout, 4xx/5xx, malformed response, or policy rejection maps to sanitized graph feedback without leaking secrets.
- Missing or invalid metadata YAML fails fast at runtime load or validation command time.

---

## 3. Functional Requirements

| ID | Requirement (testable) | Trace |
| :-- | :-- | :-- |
| **FR-EXEC-01** | Define a stable executor result contract consumed by `execute_sql`, `validate_result`, and `summarize_answer`: rows, columns, row count, execution metadata, and sanitized error details. | PRD §3, §9 Task 2 |
| **FR-EXEC-02** | Keep `stub` mode available for local development and CI with deterministic output. | PRD §3, §5.1 |
| **FR-EXEC-03** | Implement `http_spring` as the only Phase 1 production executor mode under `ai_python/`. | PRD §5.1, §7 |
| **FR-EXEC-04** | Keep `python_ro` recognized but explicitly unavailable in Task006, failing fast with an actionable deferred-mode error. | PRD §5.1, §8 |
| **FR-EXEC-05** | `build_sql_executor` must fail fast for unknown mode, missing required env vars, invalid timeout, invalid row limit, and unsupported production mode. | PRD §3, §9 Task 3 |
| **FR-SAFE-01** | Before dispatch, every non-stub executor must reject `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, DDL, DML, transaction-control statements, and multi-statement payloads. | PRD §3, §3 NFR Safety |
| **FR-SAFE-02** | Only SQL accepted by prior `sql_review` and `validate_sql` stages may reach executor dispatch, while executor-level defensive checks remain mandatory. | PRD §3, §8 |
| **FR-SAFE-03** | Enforce row limit defaults and hard maximums at executor boundary even when Spring also enforces them downstream. | PRD §3 NFR Result limits |
| **FR-HTTP-01** | Python HTTP client request must include sanitized SQL, optional parameters if supported, tenant/correlation context when available, row limit hint, timeout hint, and metadata safe for Spring policy decisions. | PRD §7 Spring HTTP Handoff Dependency |
| **FR-HTTP-02** | Python HTTP client must map Spring success response to deterministic `query_result` shape with columns, rows, row_count, execution_ms, and meta. | PRD §7, §9 Task 2 |
| **FR-HTTP-03** | Python HTTP client must map Spring failure response, timeout, network error, and malformed payload to sanitized structured failure details for graph retry/feedback. | PRD §3, §7 |
| **FR-META-01** | Define and validate YAML metadata artifact schema compatible with the current runtime loader and safe future fields. | PRD §3, §9 Task 5 |
| **FR-META-02** | Add a CLI scan command that produces YAML with `generated_at`, source mode, schema identifier, tables, columns, basic types, nullable flags when available, primary-key hints when available, and optional safe metadata only when explicitly enabled. | PRD §3, §5.1, §9 Task 6 |
| **FR-META-03** | Add a CLI validate command usable by CI/deploy checks and manual metadata workflows. | PRD §3, §9 Task 5-6 |
| **FR-META-04** | Runtime continues loading pre-built YAML from configured schema directory and must not scan live DB on request path or startup. | PRD §5.1, §8 |
| **FR-DOC-01** | Update `ai_python` operator docs and `.env.example` to explain executor modes, required env vars, metadata commands, Spring handoff dependency, and deferred `python_ro`. | PRD §3, §9 Task 7 |
| **FR-TEST-01** | Add pytest coverage for factory config, HTTP executor success/failure mapping, read-only enforcement, row limits, timeout handling, metadata validation, and no-secret error behavior. | PRD §3, §9 Task 8 |

---

## 4. API / Integration Contracts

### 4.1 Python Executor Port

Existing port remains conceptually:

```python
class SqlExecutor(Protocol):
    def execute(self, sql: str, *, tenant_id: str | None) -> dict[str, Any]:
        ...
```

Task006 may extend implementation internals, but graph-facing behavior must remain compatible with `make_execute_sql_node`, which expects either a `dict` result or an exception mapped to validation feedback.

### 4.2 Conceptual Spring HTTP Contract (Python Client Side Only)

**Method/path:** configurable by `SPRING_SQL_URL`, expected to be a Spring-owned HTTPS endpoint such as `POST /internal/ai/sql/read-only/execute`.

**Request headers:**

| Header | Required | Rule |
| :-- | :-- | :-- |
| `Content-Type: application/json` | Yes | JSON payload only. |
| `X-Correlation-Id` | When available | Propagated from request/runtime context. |
| `Authorization` or service credential header | Deployment-specific | Python may send configured service credential only if required; logs must redact it. |

**Request body:**

```json
{
  "sql": "SELECT name, total FROM orders LIMIT 100",
  "params": {},
  "tenant_id": "tenant-a",
  "schema_version": "erp-v1",
  "limit": 100,
  "timeout_ms": 10000,
  "correlation_id": "req-123"
}
```

**Success response:**

```json
{
  "columns": [
    {"name": "name", "type": "text"},
    {"name": "total", "type": "numeric"}
  ],
  "rows": [
    {"name": "Ha Noi", "total": 1200000}
  ],
  "row_count": 1,
  "execution_ms": 42,
  "meta": {
    "mode": "http_spring",
    "source": "spring_read_only_sql"
  }
}
```

**Failure response:**

```json
{
  "error": {
    "code": "SQL_POLICY_REJECTED",
    "message": "Query is not allowed",
    "category": "policy"
  },
  "execution_ms": 7
}
```

**Python-side mapping rules:**

- Success maps to `query_result.rows`, `query_result.columns`, and `query_result.meta`.
- Empty row sets are valid and map to `rows: []`.
- Failure maps to a sanitized executor error with `code`, `category`, and safe message only.
- Transport timeout maps to `category=timeout`.
- 401/403 maps to `category=auth`.
- 4xx policy errors map to `category=policy`.
- 5xx and malformed responses map to `category=upstream`.

**Spring handoff only:**

- Spring endpoint implementation, authentication policy, DB session policy, audit fields, and row-level security enforcement are outside Task006.

### 4.3 Environment / Configuration

| Variable | Required when | Rule |
| :-- | :-- | :-- |
| `SQL_EXECUTOR_MODE` | Always | One of `stub`, `http_spring`, `python_ro`; production requires `http_spring` for Task006. |
| `APP_ENV` | Always | `prod`/`production` must reject non-`http_spring` mode. |
| `SPRING_SQL_URL` | `http_spring` | Absolute HTTP(S) URL for Spring read-only SQL endpoint. |
| `DATABASE_URL_RO` | Deferred `python_ro` | Not sufficient to enable `python_ro` in Task006; mode still fails as deferred. |
| `SQL_TIMEOUT_SECONDS` | Optional | Default <= 10; valid range 1-30 seconds. |
| `SQL_RESULT_LIMIT_DEFAULT` | Optional | Default <= 100 rows. |
| `SQL_RESULT_LIMIT_MAX` | Optional | Hard max <= 500 rows. |
| `SCHEMA_DIR` | Optional | Directory containing validated runtime YAML artifacts. |

Names may align to existing `GraphSettings` fields during implementation, but operator docs must clearly state the final env contract.

---

## 5. Data / State Shapes

### 5.1 Executor Success Result

```python
class SqlColumn(TypedDict, total=False):
    name: str
    type: str | None

class SqlExecutorMeta(TypedDict, total=False):
    mode: Literal["stub", "http_spring"]
    source: str
    execution_ms: int
    row_count: int
    correlation_id: str
    timeout_ms: int
    limit: int

class SqlExecutorResult(TypedDict):
    rows: list[dict[str, Any]]
    columns: list[SqlColumn]
    meta: SqlExecutorMeta
```

Compatibility note: existing `validate_result` already accepts a dict with `rows`. Task006 should preserve that minimum while adding deterministic columns/meta for downstream summarization and tests.

### 5.2 Executor Failure Detail

```python
class SqlExecutorErrorDetail(TypedDict, total=False):
    code: str
    category: Literal["policy", "timeout", "auth", "upstream", "config", "validation"]
    message: str
    retryable: bool
    correlation_id: str
```

Failure detail must never include DB passwords, bearer tokens, credentialed JDBC URLs, full `Authorization` headers, or raw upstream stack traces.

### 5.3 Metadata Artifact

Runtime-compatible fields should preserve the current loader shape:

```python
class ColumnMeta(BaseModel):
    name: str
    type: str | None = None
    nullable: bool | None = None
    allowlist: bool = True

class TableMeta(BaseModel):
    name: str
    columns: list[ColumnMeta] = []
    pk: list[str] = []
    fks: list[dict[str, Any]] = []
    row_count: int | None = None

class SchemaArtifact(BaseModel):
    schema_version: str
    tables: list[TableMeta]
    generated_at: str
    source_mode: Literal["cli_scan", "manual"]
    source_schema: str
    updated_at: str | None = None
```

Backward compatibility note: current runtime fields include `schema_version`, `tables`, `columns`, `pk`, `fks`, and `updated_at`. New validation may allow `generated_at`, `source_mode`, `source_schema`, `nullable`, and safe optional metadata while keeping runtime load compatibility.

### 5.4 Graph State Touchpoints

Task006 must preserve these state touchpoints:

- Input to executor: `generated_sql`, `tenant_id`, optional `schema_version`.
- Success output: `query_result` dict with at least `rows`.
- Failure output: `query_result=None` plus `validation_feedback.exec` containing sanitized message.
- Result validation: `result_ok`, `result_empty`, and retry routing remain compatible with current SQL subgraph.

---

## 6. Non-Functional Requirements

| ID | Requirement | Trace |
| :-- | :-- | :-- |
| **NFR-SAFE-01** | 100% of executor modes reject DDL, DML, multi-statement payloads, and transaction-control SQL before dispatch. | PRD §3 NFR Safety |
| **NFR-TIME-01** | SQL execution default timeout is <= 10 seconds and configurable within documented safe range 1-30 seconds. | PRD §3 NFR Timeouts |
| **NFR-LIMIT-01** | Default result limit is <= 100 rows; hard maximum is <= 500 rows. | PRD §3 NFR Result limits |
| **NFR-ERR-01** | Logs and graph feedback must not leak DB passwords, bearer tokens, credentialed URLs, or full auth headers. | PRD §3 NFR Error hygiene |
| **NFR-OBS-01** | Non-stub execution logs mode, correlation id/request id when available, duration_ms, row_count, and sanitized error category. | PRD §3 NFR Observability |
| **NFR-REL-01** | New executor factory and metadata modules target >= 90% line coverage. | PRD §3 NFR Reliability |
| **NFR-META-01** | Generated metadata includes `generated_at`, source mode, and schema identifier; production refresh should happen before schema-changing release or at least every 30 days. | PRD §3 NFR DB metadata freshness |
| **NFR-START-01** | Runtime fails fast within 5 seconds when configured metadata YAML is missing or invalid. | PRD §3 NFR Startup behavior |
| **NFR-SCOPE-01** | All implementation artifacts remain under `ai_python/`; Java and frontend work are handoff only. | PRD §1, §7, §10 |

---

## 7. Acceptance Criteria

### AC-EXEC-01 - Factory accepts supported modes safely

**Given** `SQL_EXECUTOR_MODE=stub`  
**When** the runtime builds dependencies  
**Then** `StubSqlExecutor` is constructed without external env vars.

**Given** `SQL_EXECUTOR_MODE=http_spring` and a valid `SPRING_SQL_URL`  
**When** the runtime builds dependencies  
**Then** `HttpSpringSqlExecutor` is constructed with validated timeout and row-limit config.

**Given** `SQL_EXECUTOR_MODE=http_spring` and missing `SPRING_SQL_URL`  
**When** the runtime builds dependencies  
**Then** startup fails fast with an actionable config error.

### AC-EXEC-02 - Deferred python_ro is explicit

**Given** `SQL_EXECUTOR_MODE=python_ro`  
**When** the runtime builds dependencies or executor is selected  
**Then** Task006 fails fast with a sanitized, actionable message that `python_ro` is deferred to Phase 2.

### AC-SAFE-01 - Unsafe SQL never dispatches

**Given** SQL containing `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, transaction control, or multiple statements  
**When** execution reaches executor boundary  
**Then** the executor rejects it before HTTP dispatch and records sanitized validation feedback.

### AC-HTTP-01 - Spring success maps to graph result

**Given** Spring returns valid columns, rows, row_count, and execution_ms  
**When** `HttpSpringSqlExecutor.execute()` completes  
**Then** graph state receives `query_result` with deterministic `rows`, `columns`, and `meta`, and `validate_result` can mark it valid.

### AC-HTTP-02 - Spring failure maps safely

**Given** Spring returns policy failure, auth failure, timeout, 5xx, or malformed response  
**When** `HttpSpringSqlExecutor.execute()` handles the failure  
**Then** graph feedback contains a sanitized structured category and no secrets.

### AC-META-01 - CLI generates valid YAML

**Given** safe DB metadata access is configured  
**When** the operator runs the scan CLI  
**Then** the CLI writes YAML containing schema identifier, generated_at, source mode, tables, columns, basic types, nullable flags when available, and primary-key hints when available.

### AC-META-02 - CLI validates generated or manual YAML

**Given** a valid metadata YAML artifact  
**When** the operator runs validation CLI  
**Then** validation passes and the artifact is compatible with runtime loading.

**Given** missing required fields, empty schema, malformed table/column definitions, or invalid types  
**When** validation CLI runs  
**Then** validation fails with actionable errors and non-zero exit code.

### AC-DOC-01 - Operator docs are complete

**Given** Task006 implementation is complete  
**When** an operator reads `ai_python` docs and `.env.example`  
**Then** they can identify supported executor modes, required env vars, metadata refresh/validate commands, row/timeout limits, `python_ro` deferred status, and Spring handoff requirements.

### AC-SCOPE-01 - Cross-scope work remains handoff

**Given** the Spring HTTP endpoint is required for production  
**When** Task006 is reviewed  
**Then** no Java/Spring or frontend files are modified for implementation; Spring work is documented as downstream handoff only.

---

## 8. Traceability Matrix

| SRS item | PRD source |
| :-- | :-- |
| Scope boundary under `ai_python/` and Spring handoff only | PRD §1, §7, §10 |
| Option B with Phase 1 `http_spring` | PRD §5.1 |
| `python_ro` deferred | PRD §5.1, §8 |
| Existing LangGraph route preserved | PRD §2 |
| Executor result/error contract | PRD §3 Functional Requirements, §9 Task 2 |
| Factory config validation | PRD §3 Functional Requirements, §9 Task 3 |
| Read-only enforcement | PRD §3 Functional Requirements, §3 NFR Safety |
| Spring HTTP conceptual request/response | PRD §7 Spring HTTP Handoff Dependency |
| DB metadata YAML generation | PRD §3 Functional Requirements, §9 Task 6 |
| Metadata validation and startup fail-fast | PRD §3 NFR Startup behavior, §9 Task 5 |
| Tests and coverage | PRD §3 Functional Requirements, §3 NFR Reliability, §9 Task 8 |
| Operator documentation | PRD §3 Functional Requirements, §9 Task 7 |
| Exit readiness | PRD §10 |

---

## 9. BA Gate

| Gate | Status |
| :-- | :-- |
| SRS file written to requested `OUT_PATH` | PASS |
| Structure covers AI_BA §2 minimum sections | PASS |
| Status is Approved for PM continuation | PASS |
| PRD insufficiency STOP triggered | NO |
| Cross-scope Java implementation triggered | NO - handoff only |

