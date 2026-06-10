# CODE_REVIEW — Task004

> Iteration 1 archived in history; this file records Iteration 2 re-review.

**Verdict:** PASS  
**Iteration:** 2  
**SRS:** `docs/ai-python/srs/SRS_AI_Task004_langgraph-gemma4-task4-spring-fastapi.md`  
**ADR:** `docs/ai-python/adr/ADR-004-langgraph-gemma4-task4-spring-fastapi.md`  
**Task:** `docs/ai-python/tasks/Task004.md`

## Re-review scope

- Re-check fixes after CR1 BLOCK for:
  - `user_id` propagation in state/runtime.
  - JWT claims vs request metadata enforcement.
  - New tests for stream runtime error terminal event and claims/metadata mismatch.

## Findings (Iteration 2)

- **Resolved — FR-CTX-01 (`user_id` propagation).**  
  Paths: `ai_python/app/api/runtime.py`, `ai_python/app/graph/state.py`  
  Runtime now forwards full context (`correlation_id`, `user_id`, `tenant_id`, `thread_id`, `schema_version`) into both state and graph config; state schema includes `user_id`.

- **Resolved — FR-SEC-01 (claims enforcement).**  
  Paths: `ai_python/app/api/routes.py`, `ai_python/app/api/auth.py`  
  Route now derives identity from JWT claims and enforces claim/body consistency. Mismatch returns canonical `403 AI_AUTH_FORBIDDEN` before runtime execution.

- **Resolved — FR-API-06/08 + FR-TEST-01 failure semantics coverage.**  
  Path: `ai_python/tests/test_api_task004.py`  
  Added stream failure test asserting single terminal `error` event with canonical payload; added mismatch test asserting `403` and runtime non-execution.

## Contract alignment

- **SRS/ADR status:** No remaining BLOCK items found in reviewed scope.
- **Decision:** PASS for Iteration 2 re-review.

## Verification note

- Static code review completed on requested files.
- Local `pytest` execution in this environment is blocked by missing dependency `jwt` (PyJWT), so runtime test execution could not be re-run here.
