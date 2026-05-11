# PRD Task006 — SQL Executor + DB Metadata Production Gaps

**STATUS: FINAL — Owner selected Option B (2026-05-10)**

---

## 1. Project Overview

- **Core goal:** Close the production readiness gaps in the `ai_python` FastAPI/LangGraph track by defining how SQL execution modes move beyond `StubSqlExecutor` and how DB metadata artifacts are produced, validated, and refreshed without requiring runtime graph changes or edits outside `ai_python/`.
- **Target users:** AI runtime maintainers, backend integration owners, QA/test owners, and deployment operators responsible for running the FastAPI/LangGraph service safely against real or delegated SQL execution surfaces.
- **Scope boundary:** All implementation artifacts must stay under `ai_python/`. Spring/Java and React/TypeScript changes are out of scope; any Spring HTTP execution contract is documented only as an integration dependency/handoff.

## 2. Current Context

LangGraph v1 is already implemented with the intended route:

- Intent classification routes to `chat_normal` or the SQL subgraph.
- SQL subgraph flow: `gen_sql -> sql_review -> validate_sql -> execute_sql -> validate_result`.
- Retry/fail-max behavior and final `summarize_answer` stage exist.

Known production gaps:

- `SQL_EXECUTOR_MODE` defaults to stub via `StubSqlExecutor`.
- `python_ro` and `http_spring` modes are recognized by `build_sql_executor`, including environment validation, but their concrete executors currently raise `NotImplementedError`.
- DB metadata is loaded at runtime from pre-built YAML, but the offline scan pipeline described in design material is not present in the `ai_python` app package.

## 3. Specifications

### Functional Requirements

- Implement or explicitly constrain SQL executor modes.
  - `stub` remains available for local development and tests.
  - `python_ro` must execute validated, read-only SQL using Python-side DB connectivity if selected.
  - `http_spring` must call a Spring-owned read-only SQL execution endpoint if selected, but this PRD may only define the client and expected integration surface under `ai_python/`.
  - `build_sql_executor` must fail fast on missing or invalid configuration for non-stub modes.
  - Runtime errors must return structured failure details to the graph without leaking secrets.

- Preserve SQL safety controls before execution.
  - Only SQL already accepted by `sql_review` and `validate_sql` can reach the executor.
  - Execution must reject non-read-only statements defensively.
  - Result shape must be deterministic for `validate_result` and `summarize_answer`.

- Add a DB metadata refresh path.
  - Produce a YAML artifact compatible with the existing runtime loader.
  - Capture table names, column names, basic types, nullable flags when available, primary-key hints when available, and optional sample/row-count metadata only when explicitly safe.
  - Include validation for generated YAML before it can be used by runtime.
  - Support a documented manual path if no live DB credentials are available.

- Add tests and operator documentation.
  - Unit tests for executor factory configuration behavior.
  - Unit tests for read-only enforcement and error mapping.
  - Tests for DB metadata artifact validation.
  - README or docs updates under `ai_python/` explaining modes, required environment variables, and refresh workflow.

### Non-Functional Requirements

- **Safety:** 100% of executor modes must reject `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, DDL, DML, multi-statement payloads, and transaction-control statements before dispatch.
- **Timeouts:** SQL execution must enforce a default timeout <= 10 seconds, configurable by environment with a documented safe range of 1-30 seconds.
- **Result limits:** SQL execution must enforce a default row limit <= 100 rows unless the graph already produced a stricter limit; hard maximum <= 500 rows.
- **Error hygiene:** Logs and graph errors must not include DB passwords, bearer tokens, JDBC URLs with credentials, or full authorization headers.
- **Observability:** Each non-stub execution must log mode, request id/correlation id when available, duration_ms, row_count, and sanitized error category.
- **Reliability:** Executor factory tests must cover all supported modes and missing-env branches; target >= 90% line coverage for new modules.
- **DB metadata freshness:** Generated artifact must include `generated_at`, source mode, and schema identifier. Production deployments should refresh before each schema-changing release or at least every 30 days.
- **Startup behavior:** Runtime must fail fast within 5 seconds if configured metadata YAML is missing or invalid.

## 4. Architecture Options

### Option A — Full Production Path: Implement `python_ro` + `http_spring`, Add CLI DB Meta Refresh

Implement both production executor modes under `ai_python`, while adding an offline CLI metadata scanner that writes and validates YAML artifacts consumed by runtime.

- **SQL executor approach:**
  - Implement `PythonRoSqlExecutor` using Python DB connectivity and strict read-only enforcement.
  - Implement `HttpSpringSqlExecutor` as an HTTP client for a Spring-owned read-only SQL execution endpoint.
  - Keep `StubSqlExecutor` as dev/test mode only.

- **DB metadata approach:**
  - Add a CLI command or script under `ai_python/` to scan DB metadata and generate YAML.
  - Add a validation command usable in CI/deploy checks.

- **Pros:**
  - Covers both deployment models immediately.
  - Reduces future rework if some environments execute SQL directly from Python and others delegate to Spring.
  - CLI refresh keeps metadata generation out of request path.

- **Cons:**
  - Highest implementation and testing cost.
  - Requires clear Spring HTTP contract alignment even though Java implementation is out of scope.
  - More environment variables and operator docs are needed up front.

- **Risks:**
  - `http_spring` may block on an external Spring endpoint not yet implemented or not contract-stable.
  - Python DB driver choice may vary by target database and deployment.
  - Broader surface increases security review burden.

- **Cost-to-change:** Medium. Both executor abstractions become real, so later refinements are incremental, but early contract mistakes can require migration.

- **When to choose it:** Choose A if Owner wants Task006 to make the AI runtime production-capable across both direct DB and Spring-delegated execution paths in one milestone.

### Option B — Phased Production Path: Implement One Real Executor First, CLI DB Meta Refresh Now

Implement the most immediately deployable executor mode first, keep the other production mode explicitly unavailable with clear docs/tests, and add the CLI metadata refresh pipeline now.

- **SQL executor approach:**
  - Implement `python_ro` first if the AI service can safely receive read-only DB credentials.
  - Or implement `http_spring` first if SQL execution must stay behind Spring authorization and auditing.
  - Keep the other mode recognized but intentionally failing with an actionable configuration error until its follow-up task.
  - Keep `stub` for dev/test.

- **DB metadata approach:**
  - Add CLI scan + validate workflow under `ai_python/`.
  - Runtime continues loading pre-built YAML only.

- **Pros:**
  - Produces a real production path with lower scope than Option A.
  - DB metadata pipeline is solved in the same milestone.
  - Easier to test, review, and deploy safely.

- **Cons:**
  - Only one execution topology becomes production-ready in Task006.
  - Requires Owner to choose which executor mode is first.
  - A follow-up task remains for the second executor.

- **Risks:**
  - Picking the wrong first executor can delay production adoption.
  - Documentation must clearly prevent operators from enabling the unimplemented production mode.

- **Cost-to-change:** Low to medium. The executor abstraction remains stable, and the second mode can be added later behind the same factory.

- **When to choose it:** Choose B if Owner wants the safest incremental production milestone while preserving a clear path to both executor modes.

### Option C — Dev-Safe Runtime: Keep Stub Default, Add Manual YAML Validation Only

Keep SQL execution non-production for now, improve failure clarity around non-stub modes, and formalize manual DB metadata YAML validation/documentation under `ai_python/`.

- **SQL executor approach:**
  - `stub` remains the only usable mode.
  - `python_ro` and `http_spring` fail fast with explicit "not production-ready in this build" errors.
  - Add docs explaining that real SQL execution is deferred.

- **DB metadata approach:**
  - Add YAML schema validation and manual authoring guidance.
  - No DB scanning CLI and no admin endpoint.

- **Pros:**
  - Lowest implementation cost.
  - Avoids premature DB credential and Spring contract decisions.
  - Useful if Task006 is only intended to document the gap and harden dev/test behavior.

- **Cons:**
  - Does not close the main production SQL execution gap.
  - DB metadata remains manually maintained.
  - Operators still cannot refresh metadata from live DB automatically.

- **Risks:**
  - Production readiness may be overstated unless docs are very clear.
  - Manual YAML drift can degrade SQL generation quality.

- **Cost-to-change:** Low initially, medium later. Deferred production work remains largely untouched.

- **When to choose it:** Choose C only if the current milestone is documentation and guardrails, not production execution.

## 5. Recommendation

**Recommended option: B — Phased Production Path.**

Rationale:

- It creates one real production SQL execution path without forcing both deployment models into the same milestone.
- The DB metadata CLI refresh pipeline is valuable regardless of which executor mode wins.
- It keeps all implementation under `ai_python/` and treats Spring execution as an integration surface instead of crossing into Java changes.
- It limits blast radius while still moving beyond the current stub-only production gap.

Default selection within Option B:

- Prefer `http_spring` first if production policy requires Spring to remain the sole DB execution authority for authorization, auditing, and network access.
- Prefer `python_ro` first if the AI service is allowed read-only DB credentials and the fastest path is direct Python execution.

### 5.1 Owner-locked decisions (post–Option B)

| Decision | Lock |
| :-- | :-- |
| Architecture package | **Option B** — phased production: one real executor in Task006, CLI DB metadata refresh in the same milestone. |
| Phase-1 production executor | **`http_spring`** — Python `HttpSpringSqlExecutor` + contract/tests/mocks under `ai_python/`; Spring endpoint remains a documented handoff (no Java in this task). Rationale: aligns with §5 default when Spring should own DB execution authority; consistent with prior Spring↔FastAPI integration work. |
| Deferred executor | **`python_ro`** — remains explicitly unavailable in this milestone (clear error if `SQL_EXECUTOR_MODE=python_ro` without Phase-2 implementation, or keep `NotImplementedError` with actionable message per implementation). |
| DB metadata | **CLI scan + validate** — artifact compatible with existing runtime YAML loader; no admin HTTP refresh by default. |

If production policy instead requires **python_ro** first, Owner may override Phase-1 executor in a follow-up note; SRS/ADR should then swap ordering without changing Option B structure.

## 6. Tech Stack

- **Frontend / UI:** None in scope.
- **Backend / business logic:** Python, FastAPI app package under `ai_python/app`, LangGraph runtime and SQL subgraph.
- **Database & storage:** Runtime DB metadata YAML artifact under `ai_python` configuration paths; optional read-only DB connectivity for `python_ro`; optional HTTP integration to Spring for `http_spring`.
- **Testing:** Pytest for unit/integration-style tests using fakes/mocks; no live production DB required for default test suite.
- **Configuration:** Environment variables validated by `build_sql_executor` and metadata loader; `.env.example` updates under `ai_python/` only.

## 7. Integration Surface and Out-of-Scope

### In Scope

- Python executor implementations or explicit mode gating under `ai_python/`.
- DB metadata scan/validation/manual workflow under `ai_python/`.
- FastAPI/LangGraph runtime compatibility with executor results.
- Tests and docs under `ai_python/`.

### Out of Scope

- Java/Spring controller, service, security, or database changes.
- React/TypeScript UI changes.
- Production database schema changes.
- Replacing the existing LangGraph v1 flow.

### Spring HTTP Handoff Dependency

If `http_spring` is selected, the Python client expects a Spring-owned read-only SQL execution endpoint with a stable conceptual contract:

- Request includes sanitized SQL, parameter payload if supported, limit/timeout hints, and correlation id.
- Response includes columns, rows, row_count, execution_ms, and structured error fields.
- Spring side owns authentication, authorization, DB access policy, and audit logging.

The exact Java implementation is a downstream handoff and must not be implemented in Task006.

## 8. Open Assumptions

- The existing SQL validation/review stages remain the primary gate before executor dispatch, but executors still perform defensive read-only checks.
- The target DB engine and Python driver are not locked in this PRD; implementation should use existing repo configuration or document the selected driver in follow-up.
- Runtime should continue loading DB metadata from YAML, not scan the DB on every app start.
- Admin HTTP endpoint for DB metadata refresh is not recommended by default because it increases runtime security surface.
- Phase-1 executor is **http_spring** per §5.1 unless Owner explicitly overrides.

## 9. Task Breakdown & Dependency Graph

- [x] Task 1: Lock selected Task006 option
  - Description: Owner chooses A, B, C, or "pick optimal"; update PRD status and selected architecture.
  - Input/Output: Input is Owner selection; output is finalized PRD with one selected path.
  - Acceptance Criteria: PRD no longer says "awaiting Owner selection"; selected option and rationale are explicit.
  - Depends on: None.

- [ ] Task 2: Define executor result/error contract
  - Description: Specify Python-side result DTO shape shared by stub, direct DB, and HTTP modes.
  - Input/Output: Input is current graph executor interface; output is documented result/error contract and tests for graph compatibility.
  - Acceptance Criteria: `execute_sql` and `validate_result` can consume all executor results deterministically; errors are structured and sanitized.
  - Depends on: Task 1.

- [ ] Task 3: Harden executor factory configuration
  - Description: Ensure `build_sql_executor` validates selected mode, required env vars, timeout, row limits, and unsupported production modes.
  - Input/Output: Input is environment configuration; output is fail-fast executor construction behavior.
  - Acceptance Criteria: Unit tests cover `stub`, selected production mode(s), missing env vars, invalid timeout/limit, and unsupported mode errors.
  - Depends on: Task 1, Task 2.

- [ ] Task 4: Implement selected SQL executor mode(s)
  - Description: Implement executor mode(s) according to selected option.
  - Input/Output: Input is validated SQL and runtime config; output is structured columns/rows or sanitized structured error.
  - Acceptance Criteria: Read-only enforcement rejects unsafe SQL; timeout and row-limit controls are applied; tests use fakes/mocks and do not require production DB.
  - Depends on: Task 2, Task 3.

- [ ] Task 5: Add DB metadata artifact schema validation
  - Description: Define and enforce validation for runtime YAML metadata artifacts.
  - Input/Output: Input is YAML path/content; output is validated metadata object or actionable validation errors.
  - Acceptance Criteria: Invalid YAML fails fast within 5 seconds at startup/check time; tests cover missing fields, type mismatches, empty schema, and valid sample metadata.
  - Depends on: Task 1.

- [ ] Task 6: Add DB metadata refresh workflow
  - Description: Implement selected refresh workflow: CLI scan for Options A/B, or manual validation-only workflow for Option C.
  - Input/Output: Input is DB metadata source or manual YAML; output is generated/validated YAML artifact compatible with runtime.
  - Acceptance Criteria: Generated artifact includes `generated_at`, source mode, schema identifier, tables, columns, and validation pass/fail result.
  - Depends on: Task 5.

- [ ] Task 7: Update `ai_python` operator documentation
  - Description: Document executor modes, required env vars, DB metadata refresh/validation commands, and production caveats.
  - Input/Output: Input is selected architecture and implementation behavior; output is docs under `ai_python/`.
  - Acceptance Criteria: Docs state default mode, production mode setup, expected failure modes, and Spring handoff dependency when relevant.
  - Depends on: Task 3, Task 4, Task 6.

- [ ] Task 8: Add focused test suite and CI-safe checks
  - Description: Add pytest coverage for new executor and DB metadata behavior without requiring live external services.
  - Input/Output: Input is implementation and fakes/mocks; output is passing tests.
  - Acceptance Criteria: New modules target >= 90% line coverage; tests include safety rejection, config validation, metadata validation, and sanitized error behavior.
  - Depends on: Task 4, Task 5, Task 6.

## 10. Exit Criteria

- PRD is finalized after Owner selection.
- Selected executor path is unambiguous.
- DB metadata refresh or validation path is unambiguous.
- All implementation tasks remain under `ai_python/`.
- Spring and frontend work, if any, are captured only as downstream handoff/dependency notes.
