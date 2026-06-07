# QA Spec 003 (upgrade/ai-python): Agentic AI Runtime Remediation Plan

- **SRS ref**: `docs/upgrade/ai-python/srs/005_agentic-ai-remediation-plan.md`
- **Tech Spec ref**: `docs/upgrade/ai-python/tech_lead/003_agentic-ai-remediation-plan.md`
- **Stage**: QA_SPEC_WRITER
- **Date**: 2026-06-07
- **Mode**: AUTO_DOCS
- **CodeGraph**: `status`, `context`, `impact`, `callers`, `affected`
- **Superpowers alignment**: test-driven-development principles; define failing tests before coding.
- **Readiness**: QA_READY_FOR_CODING

---

## 1. QA Strategy

This remediation is a test-first effort focused on production wiring gaps. The existing `ai_python` test suite was green (`454 passed, 1 warning`) while review found runtime defects, so the new tests must enter through runtime/tool/provider boundaries instead of only testing helper classes directly.

Test priority:

1. Fail-closed RBAC through API/runtime context.
2. Real LLM usage metadata through `OpenAICompatibleChatClient`.
3. Async stream flag behavior and SSE parity.
4. SQL self-correct behavior through `SqlQueryTool.invoke()`.
5. HITL pending persistence across runtime object recreation.

All tests must be deterministic and must not call real model, Spring, Postgres, or pgvector.

---

## 2. Test Files

| File | Purpose |
| :-- | :-- |
| `ai_python/tests/test_runtime_role_context.py` | API/runtime role derivation into `TurnContext`; fail-closed role behavior. |
| `ai_python/tests/test_llm_usage_capture.py` | Usage metadata extraction from fake LangChain messages and structured calls. |
| `ai_python/tests/test_runtime_async_stream.py` | `agentic_async_enabled` chooses native async path and preserves SSE contract. |
| `ai_python/tests/test_sql_query_tool_self_correct_integration.py` | SQL self-correct runner behavior through `SqlQueryTool.invoke()`. |
| `ai_python/tests/test_hitl_pending_store.py` | Pending HITL store TTL, tenant scoping, SQLite persistence. |
| Existing `test_harness_budget.py` | Regression for token/cost budget behavior. |
| Existing `test_agentic_integration.py` | Orchestrator-level reachability for role, cache, plan, SQL. |
| Existing `test_hitl_resume_flow.py` | Runtime resume behavior and frontend-compatible events. |

---

## 3. Test Matrix

### QP-A: Role/RBAC Propagation

| ID | Test | Expected Failure Before Fix | Expected Pass After Fix | Failure Class |
| :-- | :-- | :-- | :-- | :-- |
| QP-A-01 | `test_stream_claim_role_reaches_turn_context` | Captured `TurnContext.role` is `None`. | Captured role equals JWT-derived `staff` or `owner`. | contract-drift |
| QP-A-02 | `test_missing_role_fails_closed_for_draft` | `catalog_draft` is allowed when role missing. | `HarnessPolicyError` with Vietnamese permission message. | guardrail |
| QP-A-03 | `test_none_role_masks_sensitive_data` | Missing role may behave as unrestricted in policy. | Missing role is treated as non-owner for sensitive output. | guardrail |
| QP-A-04 | `test_api_like_staff_context_masks_sql_tool_output` | Tool output test only passes when role manually injected. | Runtime-created context masks `cost_price` for staff. | tool-integration |
| QP-A-05 | `test_owner_role_keeps_sensitive_data` | Owner role not propagated through runtime. | Owner receives sensitive columns when backend/tool returns them. | contract-drift |

Test data:

```python
claims_staff = {
    "sub": "u1",
    "tenant_id": "t1",
    "roles": ["staff"],
}
claims_owner = {
    "sub": "u1",
    "tenant_id": "t1",
    "roles": ["owner"],
}
rows = [{"name": "Ao", "cost_price": 100, "sale_price": 150}]
```

Focused command:

```powershell
cd ai_python
python -m pytest tests/test_runtime_role_context.py tests/test_capability_rbac.py -q
```

---

### QP-B: LLM Usage Capture

| ID | Test | Expected Failure Before Fix | Expected Pass After Fix | Failure Class |
| :-- | :-- | :-- | :-- | :-- |
| QP-B-01 | `test_extract_usage_from_usage_metadata` | Extractor missing or returns zero. | `InvokeUsage(prompt_tokens=10, completion_tokens=5)`. | guardrail |
| QP-B-02 | `test_extract_usage_from_response_metadata_token_usage` | Provider metadata ignored. | Token usage captured from `response_metadata.token_usage`. | tool-integration |
| QP-B-03 | `test_astructured_predict_updates_last_usage` | `last_usage` remains default zero. | `last_usage.total_tokens == 15`. | contract-drift |
| QP-B-04 | `test_structured_predict_updates_last_usage` | Sync structured path remains zero. | Sync structured path updates usage. | contract-drift |
| QP-B-05 | `test_budget_uses_real_client_usage_metadata` | Budget never hits with real adapter-style metadata. | Cost/token budget stops turn at expected threshold. | guardrail |
| QP-B-06 | `test_usage_unavailable_logs_zero_explicitly` | Missing metadata silently looks measured. | Log or metric marks usage unavailable. | observability |

Fake message shapes:

```python
AIMessage(content="{}", usage_metadata={"input_tokens": 10, "output_tokens": 5})
AIMessage(content="{}", response_metadata={"token_usage": {"prompt_tokens": 10, "completion_tokens": 5}})
AIMessage(content="{}", response_metadata={"usage": {"prompt_tokens": 10, "completion_tokens": 5}})
```

Focused command:

```powershell
cd ai_python
python -m pytest tests/test_llm_usage_capture.py tests/test_harness_budget.py tests/test_observability.py -q
```

---

### QP-C: Native Async Stream Flag

| ID | Test | Expected Failure Before Fix | Expected Pass After Fix | Failure Class |
| :-- | :-- | :-- | :-- | :-- |
| QP-C-01 | `test_agentic_async_enabled_uses_astream_without_private_loop` | Runtime still calls sync `_iter_harness_stream`. | Async path calls `_harness_events` directly via `astream`. | performance |
| QP-C-02 | `test_async_stream_preserves_progress_delta_done_order` | Async mapper missing or event order diverges. | Event order matches sync contract. | contract-drift |
| QP-C-03 | `test_pending_hitl_suppresses_done_in_async_path` | Pending HITL async path emits `done`. | `draft` emitted, `done` suppressed. | logic-flow |
| QP-C-04 | `test_async_flag_off_uses_sync_bridge` | Fallback removed or changed. | Existing sync bridge remains when flag off. | regression |
| QP-C-05 | `test_async_stream_error_maps_to_sse_error` | Exception path diverges. | User-facing `error` then `done`. | contract-drift |

Focused command:

```powershell
cd ai_python
python -m pytest tests/test_runtime_async_stream.py tests/test_harness_async_contracts.py tests/test_harness_clarify_flow.py -q
```

---

### QP-D: SQL Self-Correct Tool Integration

| ID | Test | Expected Failure Before Fix | Expected Pass After Fix | Failure Class |
| :-- | :-- | :-- | :-- | :-- |
| QP-D-01 | `test_tool_uses_regen_budget_from_settings` | `SqlQueryTool.invoke()` never calls runner or budgeted loop. | Regen count follows `settings.sql_regen_max`. | tool-integration |
| QP-D-02 | `test_tool_dedups_repeated_sql_review_failure` | Duplicate issue repeats through legacy subgraph or is unobservable. | Tool returns degraded/deduped result without repeated execute. | guardrail |
| QP-D-03 | `test_tool_degrades_with_partial_rows` | Tool raises/fails hard or drops partial rows. | Tool returns best rows plus Vietnamese warning. | logic-flow |
| QP-D-04 | `test_tool_blocks_write_sql_before_execute` | Write SQL reaches execute callback. | Execute callback is not called. | guardrail |
| QP-D-05 | `test_sql_tool_self_correct_reachable_through_orchestrator` | Orchestrator only reaches legacy compiled behavior. | Harness call to `sql_query` exercises self-correct path. | tool-integration |

Test data:

```python
review_fail_then_pass = [
    {"ok": False, "issues": ["missing join"], "retry_hint": "join orders"},
    {"ok": True, "issues": []},
]
empty_then_rows = [
    [],
    [{"month": "2026-06", "revenue": 1000000}],
]
duplicate_review_failure = {"ok": False, "issues": ["same reason"], "retry_hint": "same"}
```

Focused command:

```powershell
cd ai_python
python -m pytest tests/test_sql_query_tool_self_correct_integration.py tests/test_sql_self_correct_budget.py tests/test_sql_query_domain.py tests/test_agentic_integration.py -q
```

---

### QP-E: Durable HITL Pending Store

| ID | Test | Expected Failure Before Fix | Expected Pass After Fix | Failure Class |
| :-- | :-- | :-- | :-- | :-- |
| QP-E-01 | `test_sqlite_store_round_trips_pending_record` | No persistent store exists. | Record survives store recreation. | contract-drift |
| QP-E-02 | `test_expired_record_returns_none_and_is_deleted` | Expired records may remain in dict until same runtime reads. | Store returns none and deletes expired record. | guardrail |
| QP-E-03 | `test_tenant_mismatch_cannot_resume_pending_hitl` | Resume key alone may fetch another tenant's pending record. | Resume fails with `HITL_EXPIRED` or permission error before tool call. | guardrail |
| QP-E-04 | `test_runtime_recreation_can_resume_hitl_with_sqlite_store` | New runtime has empty `_pending_hitl`. | New runtime resolves pending record from SQLite store. | logic-flow |
| QP-E-05 | `test_expired_resume_does_not_call_spring_confirm` | Expired flow may still call tool if stale payload present. | Confirm tool is not called. | guardrail |

Focused command:

```powershell
cd ai_python
python -m pytest tests/test_hitl_pending_store.py tests/test_hitl_resume_flow.py tests/test_checkpoint_persist.py -q
```

---

## 4. E2E Regression Matrix

| ID | Scenario | Expected |
| :-- | :-- | :-- |
| E2E-R-01 | Staff asks data query returning `cost_price`. | `data_table` and final answer do not include `cost_price`. |
| E2E-R-02 | Owner asks same data query. | Owner receives `cost_price` when backend/tool returned it. |
| E2E-R-03 | Cost budget set to low value with fake provider metadata. | Turn stops with best-effort answer and budget metric. |
| E2E-R-04 | `agentic_async_enabled=true` data query. | `progress -> data_table -> delta_full -> done` order preserved. |
| E2E-R-05 | Catalog draft pending then runtime recreated then resume. | Resume succeeds with SQLite store. |
| E2E-R-06 | All agentic flags off. | Legacy path still passes existing tests. |

Command:

```powershell
cd ai_python
python -m pytest tests/test_e2e_agentic_flow.py tests/test_agentic_integration.py -q
```

---

## 5. Failure-Mode Matrix

| Failure | Expected Behavior | Covered By |
| :-- | :-- | :-- |
| JWT role missing | Fail closed for draft; data-read masked as non-owner. | QP-A-02, QP-A-03 |
| JWT role staff | Sensitive columns masked in output and observation. | QP-A-01, QP-A-04 |
| Provider usage metadata present | Budget and metrics use it. | QP-B-01..05 |
| Provider usage metadata absent | Usage zero plus explicit unavailable signal. | QP-B-06 |
| Async flag on | No private event loop bridge; SSE order preserved. | QP-C-01..03 |
| Async flag off | Sync bridge remains. | QP-C-04 |
| Repeated SQL review failure | Dedup short-circuit and degrade. | QP-D-02 |
| SQL write generated by LLM | Blocked before execute. | QP-D-04 |
| HITL pending expired | Clear error; no confirm call. | QP-E-02, QP-E-05 |
| HITL tenant mismatch | Cannot resume. | QP-E-03 |

---

## 6. Test Execution Checklist

- [ ] Write failing tests for Slice A before changing production code.
- [ ] Run Slice A focused command and confirm failures are for missing role wiring.
- [ ] Implement Slice A and rerun focused command until green.
- [ ] Repeat red/green for Slices B, C, D, and E.
- [ ] Run all focused commands.
- [ ] Run full regression:

```powershell
cd ai_python
python -m pytest tests -q
```

Expected final result:

```text
all tests pass
```

---

## 7. QA Readiness

- **Readiness**: QA_READY_FOR_CODING
- **Known risks**:
  - JWT role claim name may require mapping adjustment.
  - Provider usage metadata may vary; extractor tests must include at least three shapes.
  - Async path may expose hidden SSE ordering assumptions; keep sync fallback until async tests pass.

