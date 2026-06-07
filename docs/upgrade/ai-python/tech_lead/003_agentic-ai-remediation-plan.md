# Tech Spec 003 (upgrade/ai-python): Agentic AI Runtime Remediation Plan

- **SRS ref**: `docs/upgrade/ai-python/srs/005_agentic-ai-remediation-plan.md`
- **Stage**: TECH_SPEC_WRITER
- **Date**: 2026-06-07
- **Mode**: AUTO_DOCS
- **CodeGraph**: `status`, `context`, `impact LangHarnessRuntime`, `impact SqlQueryTool`, `impact OpenAICompatibleChatClient`, `callers SelfCorrectingSqlRunner`, `affected ai_python/app/api/runtime.py ai_python/app/api/routes.py ai_python/app/api/schemas.py ai_python/app/harness/orchestrator.py ai_python/app/harness/policy.py ai_python/app/harness/capability.py ai_python/app/llm/openai_compatible.py ai_python/app/graph/tools/sql_query.py`
- **Superpowers alignment**: writing-plans principles; exact slices, files, commands, and expected results.
- **Readiness**: READY_FOR_CODING

---

## 1. Architecture Decision

Implement remediation as five small runtime-wiring slices, ordered by guardrail criticality. Do not add a new agent framework. Keep the current split:

- **FastAPI/API runtime** derives auth/role and creates `TurnContext`.
- **Harness** validates role, tenant, budget, HITL lifecycle, and audit.
- **LLM adapter** captures provider usage for budget and metrics.
- **SQL tool** owns the production tool contract and calls LangGraph SQL internals only through a budgeted self-correct adapter.
- **LangGraph legacy path** remains the fallback when harness flags are off.

The implementation must make production wiring and tests share the same boundary. Test-only direct construction of `TurnContext(role=...)` remains allowed for unit tests, but at least one integration test per remediated capability must enter through API/runtime or the real tool adapter.

---

## 2. Implementation Slices

### Slice A: Role/RBAC Propagation

**Problem class**: execution guardrail flaw + cross-layer contract drift.

**Files to read**

- `ai_python/app/api/auth.py`
- `ai_python/app/api/routes.py`
- `ai_python/app/api/schemas.py`
- `ai_python/app/api/runtime.py`
- `ai_python/app/harness/tool_registry.py`
- `ai_python/app/harness/capability.py`
- `ai_python/app/harness/policy.py`
- `ai_python/tests/test_agentic_integration.py`
- `ai_python/tests/test_capability_rbac.py`

**Files likely to edit**

- `ai_python/app/api/routes.py`
- `ai_python/app/api/runtime.py`
- `ai_python/app/harness/tool_registry.py`
- `ai_python/app/harness/capability.py`
- `ai_python/app/harness/policy.py`
- `ai_python/tests/test_runtime_role_context.py` (new)
- `ai_python/tests/test_capability_rbac.py`

**Contract**

```python
@dataclass(frozen=True)
class AiAuthContext:
    user_id: str
    tenant_id: str
    role: str | None
    permissions: tuple[str, ...] = ()
```

Add a helper in `routes.py` or a small auth module:

```python
def derive_ai_auth_context(claims: dict[str, Any]) -> AiAuthContext:
    user_id, tenant_id = derive_identity_context(claims)
    role = _first_role_claim(claims)
    permissions = _permission_claims(claims)
    return AiAuthContext(user_id=user_id, tenant_id=tenant_id, role=role, permissions=permissions)
```

Pass `role` to `runtime.stream()` and `runtime.invoke()` through a new optional parameter:

```python
runtime.stream(request, correlation_id=correlation_id, bearer_token=token, role=auth.role)
```

Then pass role into `_build_turn_context(...)`:

```python
return TurnContext(..., role=role)
```

**Policy rules**

- `role is None`: deny `DRAFT_CREATE`; allow data read only with non-owner masking.
- `role == "owner"`: all existing tool capabilities allowed.
- `role == "staff"`: `DATA_READ` allowed, sensitive output masked, `DRAFT_CREATE` denied unless permissions explicitly include a draft capability.
- Tenant mismatch remains blocked before tool execution.

**Focused tests**

- `tests/test_runtime_role_context.py::test_stream_claim_role_reaches_turn_context`
- `tests/test_runtime_role_context.py::test_missing_role_fails_closed_for_draft`
- `tests/test_capability_rbac.py::test_none_role_masks_sensitive_data`
- `tests/test_agentic_integration.py::test_api_like_staff_context_masks_sql_tool_output`

---

### Slice B: LLM Usage Extraction

**Problem class**: observability + budget guardrail flaw.

**Files to read**

- `ai_python/app/llm/openai_compatible.py`
- `ai_python/app/llm/structured.py`
- `ai_python/app/harness/orchestrator.py`
- `ai_python/app/harness/budget.py`
- `ai_python/app/harness/observability.py`
- `ai_python/tests/test_harness_budget.py`
- `ai_python/tests/test_llm_registry.py`

**Files likely to edit**

- `ai_python/app/llm/openai_compatible.py`
- `ai_python/app/llm/structured.py`
- `ai_python/tests/test_llm_usage_capture.py` (new)
- `ai_python/tests/test_harness_budget.py`
- `ai_python/tests/test_observability.py`

**Contract**

Add usage extractor:

```python
def extract_usage(message: Any) -> InvokeUsage:
    """Read usage from LangChain/OpenAI-compatible message metadata."""
```

Supported shapes:

- `message.usage_metadata = {"input_tokens": 10, "output_tokens": 5}`
- `message.response_metadata = {"token_usage": {"prompt_tokens": 10, "completion_tokens": 5}}`
- `message.response_metadata = {"usage": {"prompt_tokens": 10, "completion_tokens": 5}}`

Update `last_usage` in:

- `invoke_text`
- `ainvoke_text`
- `structured_predict`
- `astructured_predict`

For structured calls, `structured_invoke` and `astructured_invoke` should either return `(parsed, usage)` or expose a callback/hook that lets the wrapper capture the final successful `AIMessage`. Prefer returning a small result object:

```python
@dataclass(frozen=True)
class StructuredInvokeResult(Generic[T]):
    parsed: T
    usage: InvokeUsage
```

Keep public `structured_predict(...) -> T` by unwrapping internally while still updating `last_usage`.

**Focused tests**

- `tests/test_llm_usage_capture.py::test_extract_usage_from_usage_metadata`
- `tests/test_llm_usage_capture.py::test_extract_usage_from_response_metadata_token_usage`
- `tests/test_llm_usage_capture.py::test_astructured_predict_updates_last_usage`
- `tests/test_harness_budget.py::test_budget_uses_real_client_usage_metadata`

---

### Slice C: Native Async Stream Flag

**Problem class**: performance bottleneck + flag contract drift.

**Files to read**

- `ai_python/app/api/routes.py`
- `ai_python/app/api/runtime.py`
- `ai_python/app/harness/orchestrator.py`
- `ai_python/tests/test_harness_async_contracts.py`
- `ai_python/tests/test_harness_clarify_flow.py`
- `ai_python/tests/test_hitl_resume_flow.py`

**Files likely to edit**

- `ai_python/app/api/runtime.py`
- `ai_python/app/api/routes.py`
- `ai_python/tests/test_runtime_async_stream.py` (new)
- `ai_python/tests/test_harness_async_contracts.py`

**Contract**

Introduce a runtime stream result that can be either sync or async:

```python
class GraphRuntime(Protocol):
    def stream(...) -> Any: ...
    async def astream(...) -> AsyncIterator[Any]: ...
```

Implementation:

- `LangGraphRuntime.astream()` can bridge legacy graph with `asyncio.to_thread` or return async wrapper over sync chunks.
- `LangHarnessRuntime.astream()` uses `_harness_events(...)` directly when `agentic_async_enabled=true`.
- `_iter_harness_stream(...)` remains as sync fallback when flag is false.
- `routes.stream_chat()` selects async generator when runtime exposes async stream and flag is on.

**SSE mapping**

Move event-to-SSE translation into a shared function usable by sync and async paths:

```python
def stream_chunk_to_ui_events(chunk: Any, state: StreamAccumulator) -> list[str]:
    ...
```

This prevents divergence between sync and async SSE contracts.

**Focused tests**

- `tests/test_runtime_async_stream.py::test_agentic_async_enabled_uses_astream_without_private_loop`
- `tests/test_runtime_async_stream.py::test_async_stream_preserves_progress_delta_done_order`
- `tests/test_runtime_async_stream.py::test_pending_hitl_suppresses_done_in_async_path`
- `tests/test_runtime_async_stream.py::test_async_flag_off_uses_sync_bridge`

---

### Slice D: SQL Self-Correct Through `SqlQueryTool`

**Problem class**: improper tool integration + logic flow gap.

**Files to read**

- `ai_python/app/graph/tools/sql_query.py`
- `ai_python/app/graph/nodes/sql_pipeline.py`
- `ai_python/app/graph/sql_subgraph.py`
- `ai_python/app/graph/validate_sql.py`
- `ai_python/app/harness/policy.py`
- `ai_python/tests/test_sql_self_correct_budget.py`
- `ai_python/tests/test_sql_query_domain.py`
- `ai_python/tests/test_agentic_integration.py`

**Files likely to edit**

- `ai_python/app/graph/tools/sql_query.py`
- `ai_python/app/graph/nodes/sql_pipeline.py` only if existing gen/review/execute primitives need extraction.
- `ai_python/tests/test_sql_query_tool_self_correct_integration.py` (new)
- `ai_python/tests/test_sql_self_correct_budget.py`

**Contract**

`SqlQueryTool.invoke()` must enforce this production behavior:

```text
query/input_spec
  -> generate SQL
  -> review SQL
  -> execute SQL
  -> retry/regen with sql_regen_max and sql_empty_retry_max
  -> dedup repeated SQL+issue fingerprint
  -> mask/sanitize output
  -> emit data_table SSE
```

The implementation may use one of two approaches:

1. **Preferred thin adapter**: extract gen/review/execute callables from existing `sql_pipeline.py` and pass them into `SelfCorrectingSqlRunner`.
2. **Fallback adapter**: if extraction is too risky, wrap the compiled subgraph but enforce `sql_regen_max/sql_empty_retry_max` and dedup based on emitted `generated_sql`, review feedback, and result metadata.

Do not leave `SelfCorrectingSqlRunner` uncalled. If the runner is not used, remove it and tests must prove equivalent behavior through `SqlQueryTool.invoke()`.

**Focused tests**

- `tests/test_sql_query_tool_self_correct_integration.py::test_tool_uses_regen_budget_from_settings`
- `tests/test_sql_query_tool_self_correct_integration.py::test_tool_dedups_repeated_sql_review_failure`
- `tests/test_sql_query_tool_self_correct_integration.py::test_tool_degrades_with_partial_rows`
- `tests/test_sql_query_tool_self_correct_integration.py::test_tool_blocks_write_sql_before_execute`
- `tests/test_agentic_integration.py::test_sql_tool_self_correct_reachable_through_orchestrator`

---

### Slice E: Durable HITL Pending Store

**Problem class**: HITL lifecycle / execution boundary flaw.

**Files to read**

- `ai_python/app/api/runtime.py`
- `ai_python/app/graph/checkpointing.py`
- `ai_python/app/graph/tools/catalog_draft.py`
- `ai_python/app/graph/tools/inventory_draft.py`
- `ai_python/tests/test_hitl_resume_flow.py`
- `ai_python/tests/test_checkpoint_persist.py`

**Files likely to edit**

- `ai_python/app/api/runtime.py`
- `ai_python/app/graph/checkpointing.py`
- `ai_python/app/harness/hitl_store.py` (new)
- `ai_python/tests/test_hitl_pending_store.py` (new)
- `ai_python/tests/test_hitl_resume_flow.py`

**Contract**

```python
@dataclass(frozen=True)
class PendingHitlRecord:
    tool_name: str
    payload: dict[str, Any]
    tenant_id: str | None
    user_id: str | None
    thread_id: str | None
    created_at: float

class PendingHitlStore(Protocol):
    def put(self, key: str, record: PendingHitlRecord) -> None: ...
    def get(self, key: str) -> PendingHitlRecord | None: ...
    def delete(self, key: str) -> None: ...
```

Implement:

- `InMemoryPendingHitlStore` for dev/tests.
- `SqlitePendingHitlStore` using configured `checkpoint_sqlite_path` or a dedicated `harness_hitl_sqlite_path` setting.
- TTL enforcement on `get`.
- Tenant/user/thread validation before returning a record for resume.

`LangHarnessRuntime` receives a store dependency instead of owning a raw dict. Runtime object recreation must still resolve a pending record when SQLite store is used.

**Focused tests**

- `tests/test_hitl_pending_store.py::test_sqlite_store_round_trips_pending_record`
- `tests/test_hitl_pending_store.py::test_expired_record_returns_none_and_is_deleted`
- `tests/test_hitl_pending_store.py::test_tenant_mismatch_cannot_resume_pending_hitl`
- `tests/test_hitl_resume_flow.py::test_runtime_recreation_can_resume_hitl_with_sqlite_store`
- `tests/test_checkpoint_persist.py::test_hitl_resume_expired_returns_clear_error`

---

## 3. Cross-Scope Contracts

### Auth and Role

- Do not trust a user-supplied `role` field in the request body.
- Prefer JWT claims.
- Dev bypass may assign `owner` only when existing auth bypass already marks request as dev bypass.
- Missing role in normal auth must not grant owner-level access.

### Usage and Budget

- `InvokeUsage.total_tokens` is `prompt + completion`.
- `cost_usd` remains zero if provider does not supply cost; this is allowed only when logs/metrics mark usage cost unavailable.
- Token budgets use token counts even when cost is unavailable.

### SSE

The following event names are frozen:

```text
progress, delta, delta_full, chart, draft, inventory_draft, data_table, clarify, error, done
```

Async and sync paths must share the same mapper.

### HITL Data Safety

Pending HITL store must not persist:

- bearer token
- raw JWT
- full request body beyond draft payload needed for confirmation
- raw PII outside existing draft payload

---

## 4. Implementation Order for Coding Agent

1. Write failing API/runtime role propagation tests.
2. Implement role propagation and fail-closed policy.
3. Write failing LLM usage metadata tests.
4. Implement usage extraction and structured-call usage capture.
5. Write failing async stream flag tests.
6. Implement shared sync/async SSE mapper and native async path.
7. Write failing `SqlQueryTool.invoke()` self-correct integration tests.
8. Wire SQL self-correct through the tool boundary.
9. Write failing HITL pending store persistence tests.
10. Implement pending store and runtime dependency injection.
11. Run focused AI tests after each slice.
12. Run full AI regression.

---

## 5. Verification Commands

Run these during coding:

```powershell
cd ai_python
python -m pytest tests/test_runtime_role_context.py tests/test_capability_rbac.py -q
python -m pytest tests/test_llm_usage_capture.py tests/test_harness_budget.py tests/test_observability.py -q
python -m pytest tests/test_runtime_async_stream.py tests/test_harness_async_contracts.py -q
python -m pytest tests/test_sql_query_tool_self_correct_integration.py tests/test_sql_self_correct_budget.py tests/test_sql_query_domain.py -q
python -m pytest tests/test_hitl_pending_store.py tests/test_hitl_resume_flow.py tests/test_checkpoint_persist.py -q
python -m pytest tests -q
```

Expected final result:

```text
all tests pass
```

The current baseline before coding was:

```text
454 passed, 1 warning
```

---

## 6. Horizontal Analysis

- **RBAC**: Check both policy-level denial and output-level masking. A fix in policy alone does not prevent `SELECT *` leakage if owner/staff role is absent in tool context.
- **Usage**: Check sync and async text plus sync and async structured calls. Updating only `ainvoke_text` does not fix harness planner decisions.
- **Async**: Check runtime and route layers. Adding `astream()` to runtime without selecting it in `routes.stream_chat()` leaves the flag dead.
- **SQL**: Check both standalone runner tests and orchestrator/tool integration. A green runner unit test does not prove production behavior.
- **HITL**: Check runtime object recreation, TTL expiry, tenant mismatch, and current in-memory fallback behavior.

---

## 7. Open Questions

- OQ-1: Exact JWT role claim mapping should be confirmed with backend auth owners. Coding can start with a mapping chain over `role`, `roles`, `authorities`, and `permissions`, plus fail-closed fallback.
- OQ-2: Production durable HITL store can be SQLite for this remediation. A backend-owned HITL store is a separate future architecture decision.

---

## 8. Coding Handoff

- **Readiness**: READY_FOR_CODING
- **Primary files to edit**:
  - `ai_python/app/api/routes.py`
  - `ai_python/app/api/runtime.py`
  - `ai_python/app/harness/tool_registry.py`
  - `ai_python/app/harness/capability.py`
  - `ai_python/app/harness/policy.py`
  - `ai_python/app/llm/openai_compatible.py`
  - `ai_python/app/llm/structured.py`
  - `ai_python/app/graph/tools/sql_query.py`
  - `ai_python/app/harness/hitl_store.py`
- **Primary tests to add**:
  - `ai_python/tests/test_runtime_role_context.py`
  - `ai_python/tests/test_llm_usage_capture.py`
  - `ai_python/tests/test_runtime_async_stream.py`
  - `ai_python/tests/test_sql_query_tool_self_correct_integration.py`
  - `ai_python/tests/test_hitl_pending_store.py`
