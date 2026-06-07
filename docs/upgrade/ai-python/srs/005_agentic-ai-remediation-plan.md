# SRS-005 (upgrade/ai-python): Agentic AI Runtime Remediation Plan

- **Status**: DRAFT - SRS_WRITER stage
- **Date**: 2026-06-07
- **Mode**: AUTO_DOCS
- **Scope**: AI runtime remediation for Agentic AI target completion
- **Source input**:
  - Review findings from `CODE_REVIEW_AGENT` on the current `ai_python` implementation.
  - Target design: `docs/dev/requires/Design Agentic AI.md`
  - Prior SRS: `docs/upgrade/ai-python/srs/004_agentic-ai-target-completion.md`
  - Prior Tech Spec: `docs/upgrade/ai-python/tech_lead/002_agentic-ai-target-completion.md`
  - Prior QA Spec: `docs/upgrade/ai-python/qa/002_agentic-ai-target-completion.md`
- **CodeGraph**: `status --json`, `context(...)`, `impact LangHarnessRuntime`, `impact SqlQueryTool`, `impact OpenAICompatibleChatClient`, `callers SelfCorrectingSqlRunner`, `affected ai_python/app/api/runtime.py ai_python/app/api/routes.py ai_python/app/api/schemas.py ai_python/app/harness/orchestrator.py ai_python/app/harness/policy.py ai_python/app/harness/capability.py ai_python/app/llm/openai_compatible.py ai_python/app/graph/tools/sql_query.py`
- **Superpowers alignment**: brainstorming principles for requirement framing; no code changes in this stage.

---

## 1. Executive Summary

The current Agentic AI implementation has a green unit test suite, but several target-design requirements are not enforced on the production path. The common root cause is **test-local helpers and standalone modules proving behavior in isolation while runtime wiring does not carry the same contracts through API, LLM provider, Harness, and tools**.

This SRS defines a remediation task to convert the currently partial implementation into production-wired behavior for:

1. Role/RBAC propagation and sensitive-column masking.
2. Token/cost usage capture from real LLM responses.
3. Native async streaming when `agentic_async_enabled=true`.
4. SQL self-correct budget/dedup/degrade wiring through `SqlQueryTool`.
5. Durable HITL pending state or an explicit durable-store fallback contract.

The remediation is AI-only. Backend and frontend code are read for auth/SSE evidence only; they are not primary implementation surfaces unless the coding stage discovers role claims are unavailable in the AI request boundary.

---

## 2. Evidence & GAP Analysis

| ID | Evidence | GAP |
| :-- | :-- | :-- |
| GAP-1 | `ai_python/app/api/schemas.py:21` has `ChatMetadata` without role/permissions. `ai_python/app/api/runtime.py:340` creates `TurnContext` without `role`. `ai_python/app/harness/capability.py:23` allows all actions when role is `None`. | Production RBAC and sensitive-column masking cannot distinguish owner/staff. Tests inject `role` directly into `TurnContext`, so they do not cover API wiring. |
| GAP-2 | `ai_python/app/llm/openai_compatible.py:36` initializes `last_usage`, but `invoke_text`, `ainvoke_text`, `structured_predict`, and `astructured_predict` do not update it from provider response metadata. `orchestrator.py:495` relies on `last_usage`. | Token/cost budgets and metrics are zero for real providers, so cost guardrails and observability are ineffective. |
| GAP-3 | `agentic_async_enabled` exists in `graph_settings.py:330`, but `runtime.py:374` always uses a sync iterator bridge and explicitly discards `graph_settings` at `runtime.py:386`. | The async feature flag is a no-op; streaming remains blocked by the sync bridge. |
| GAP-4 | `SelfCorrectingSqlRunner` exists in `sql_query.py:47`, but `SqlQueryTool.invoke()` at `sql_query.py:165` still delegates directly to the compiled legacy SQL subgraph. CodeGraph callers for `SelfCorrectingSqlRunner` returned none. | SQL regen/retry/dedup/degrade tests exercise the runner directly, not the harness tool used by production. |
| GAP-5 | `LangHarnessRuntime` stores pending HITL in `_pending_hitl: dict` at `runtime.py:148`, with write/read at `runtime.py:197` and `runtime.py:203`. | HITL pending state is lost on restart or multi-process routing, violating the target design persistence requirement. |

---

## 3. Scope

### In Scope

- `ai_python/app/api/schemas.py`
- `ai_python/app/api/routes.py`
- `ai_python/app/api/runtime.py`
- `ai_python/app/harness/tool_registry.py`
- `ai_python/app/harness/policy.py`
- `ai_python/app/harness/capability.py`
- `ai_python/app/harness/orchestrator.py`
- `ai_python/app/harness/runtime.py`
- `ai_python/app/llm/openai_compatible.py`
- `ai_python/app/llm/structured.py`
- `ai_python/app/graph/tools/sql_query.py`
- `ai_python/app/graph/checkpointing.py`
- `ai_python/tests/**`

### Out of Scope

- Changing Spring database schema.
- Changing frontend SSE event names.
- Replacing the existing LangGraph SQL subgraph wholesale.
- Direct write operations without HITL confirmation.
- New LLM providers.

---

## 4. Architecture Requirements

### AR-1: Separation of Responsibilities

- **LangGraph** keeps graph state, legacy fallback, SQL subgraph internals, and routing for the old path.
- **Harness** owns execution guardrails, role/capability validation, budgets, metrics, HITL pending lifecycle, and tool-call audit.
- **Tools** remain scoped integrations. `SqlQueryTool` may call LangGraph SQL generation/review/execute primitives, but must not bypass Harness policy and budget contracts.

### AR-2: Production Path Must Match Test Path

Every target-design behavior must be tested through the same boundary production uses:

- API request/auth claims -> runtime context -> Harness policy/tool.
- OpenAI-compatible client -> `last_usage` -> budget/metrics.
- `LangHarnessRuntime.stream()` -> SSE iterator.
- `SqlQueryTool.invoke()` -> SQL self-correct runner.
- HITL pending store -> resume.

Unit tests for isolated helpers remain useful, but are not sufficient acceptance evidence.

---

## 5. Functional Requirements

### FR-1: Role and Permission Propagation

- FR-1.1: The AI request boundary must derive a stable role or permission set from authenticated claims, not from user-provided body fields alone.
- FR-1.2: `TurnContext.role` must be populated before any Harness policy check or tool invocation.
- FR-1.3: If role is unavailable in a non-dev request, Harness must fail closed for privileged capabilities and treat data-read masking as non-owner.
- FR-1.4: Staff must not receive sensitive columns in SSE payloads, tool output, observations, or answer-composer inputs.
- FR-1.5: Owner must retain access to sensitive columns when allowed by backend/JWT policy.

### FR-2: Real LLM Usage Capture

- FR-2.1: `OpenAICompatibleChatClient` must update `last_usage` after sync text, async text, sync structured, and async structured calls.
- FR-2.2: Usage extraction must support LangChain/OpenAI metadata shapes commonly exposed as `usage_metadata`, `response_metadata.token_usage`, or provider-specific equivalents.
- FR-2.3: If provider metadata is absent, usage must be explicitly set to zero and logged as `usage_unavailable`, not silently treated as measured usage.
- FR-2.4: `TurnBudget` and `TraceRecorder` must receive nonzero values when fake or real response metadata provides them.

### FR-3: Native Async Harness Streaming

- FR-3.1: When `agentic_async_enabled=true`, the `/stream` path must use an async generator without creating a private event loop per request.
- FR-3.2: When `agentic_async_enabled=false`, existing sync bridge behavior must remain available for rollback.
- FR-3.3: SSE event names and ordering must remain compatible: `progress`, `data_table`, `chart`, `draft`, `inventory_draft`, `clarify`, `delta_full`, `delta`, `error`, `done`.
- FR-3.4: Pending HITL must still suppress `done` until user confirmation, matching current frontend contract.

### FR-4: SQL Self-Correct Tool Wiring

- FR-4.1: `SqlQueryTool.invoke()` must route through `SelfCorrectingSqlRunner` or remove the runner and prove the legacy subgraph enforces the same budgets through the tool boundary.
- FR-4.2: `sql_regen_max` and `sql_empty_retry_max` must affect the tool used by the Harness, not only standalone runner tests.
- FR-4.3: Duplicate SQL failure fingerprint must short-circuit at tool level.
- FR-4.4: Degraded SQL result must return a user-safe Vietnamese warning and preserve the best valid partial data.
- FR-4.5: Read-only SQL enforcement remains defense-in-depth in both Harness policy and SQL tool execution.

### FR-5: Durable HITL Pending State

- FR-5.1: Pending HITL records must be stored through a dedicated `PendingHitlStore` abstraction keyed by `thread_id` and scoped by tenant/user/correlation metadata.
- FR-5.2: The default development store may be in-memory, but runtime must surface `HITL_EXPIRED` clearly when durable persistence is unavailable or expired.
- FR-5.3: A SQLite-backed store must be available for deterministic tests and single-instance deployment.
- FR-5.4: Resume must validate tenant/user/thread match before invoking draft confirmation.
- FR-5.5: Expired records must be removed and must not call Spring confirmation.

---

## 6. Non-Functional Requirements

- NFR-1: Cost budget enforcement must be measurable in tests and production logs.
- NFR-2: Async stream path must avoid blocking the FastAPI event loop when enabled.
- NFR-3: RBAC fail-closed behavior must avoid leaking privileged data when claims are missing.
- NFR-4: SQL remediation must not change frontend SSE payload shape.
- NFR-5: HITL persistence must not store bearer tokens or raw PII.
- NFR-6: All new test paths must be deterministic and avoid real model, Spring, Postgres, or pgvector calls.

---

## 7. Acceptance Criteria

- AC-1: API/auth integration test proves `role=staff` reaches `TurnContext` and masks `cost_price`; owner keeps it.
- AC-2: Missing role in protected mode cannot create drafts and does not expose sensitive columns.
- AC-3: Fake LangChain response metadata updates `OpenAICompatibleChatClient.last_usage`; orchestrator budget hits cost/token thresholds using client metadata.
- AC-4: `agentic_async_enabled=true` uses a native async stream path and preserves SSE event order.
- AC-5: `SqlQueryTool.invoke()` test proves SQL regen/retry/dedup/degrade through the tool boundary, not only through `SelfCorrectingSqlRunner`.
- AC-6: HITL pending state survives runtime object recreation when SQLite store is configured.
- AC-7: `cd ai_python && python -m pytest tests -q` passes.
- AC-8: Legacy fallback with all `agentic_*` flags disabled remains green.

---

## 8. Risks

| Risk | Level | Mitigation |
| :-- | :-- | :-- |
| JWT claims do not include role directly. | Medium | Derive from existing claims/permissions; if absent, fail closed for privileged operations and document mapping in tests. |
| LangChain provider metadata shape differs by model gateway. | Medium | Implement tolerant extraction and tests for multiple metadata shapes. |
| Async stream path changes SSE timing. | High | Keep sync fallback flag; add event-order tests for both paths. |
| SQL runner integration duplicates logic already inside SQL subgraph. | Medium | Choose a thin adapter: use existing graph primitives where possible, but enforce budgets at `SqlQueryTool` boundary. |
| HITL store persistence creates cleanup concerns. | Medium | TTL cleanup on read/write; no bearer token persistence. |

---

## 9. Open Questions

- OQ-1: Which JWT claim should be the source of truth for AI role mapping: `role`, `roles`, `permissions`, or a backend-derived authority list? This is not a blocker if implementation supports a mapping chain and fail-closed fallback.
- OQ-2: Should production HITL pending store be SQLite for now or a backend/Spring endpoint later? This SRS requires SQLite for deterministic AI runtime remediation; backend store can be a future upgrade.

---

## 10. Handoff

- **Next stage**: TECH_SPEC_WRITER
- **Readiness**: READY_FOR_TECH_SPEC
- **Priority order for coding later**:
  1. Role/claims propagation and fail-closed policy.
  2. LLM usage extraction and budget/metrics.
  3. Async stream flag wiring.
  4. SQL self-correct tool wiring.
  5. HITL pending store.
