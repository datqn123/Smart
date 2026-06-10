# QA Spec 004 (upgrade/ai-python): Agentic AI v3.0 Planner-Brain Upgrade

- **SRS ref**: `docs/upgrade/ai-python/srs/006_agentic-ai-v3-planner-brain-upgrade.md`
- **Tech Spec ref**: `docs/upgrade/ai-python/tech_lead/004_agentic-ai-v3-planner-brain-upgrade.md`
- **Stage**: QA_SPEC_WRITER
- **Date**: 2026-06-07
- **Mode**: AUTO_DOCS
- **Scope**: AI Agentic runtime, tool contracts, planner ownership, K12/K15 eval gates
- **CodeGraph**: `status --json`, `context("SRS-006 Agentic AI v3 planner brain upgrade tech spec QA spec tool manifest observation contract execution tier")`
- **Superpowers alignment**: test-driven-development principles; every behavior-changing slice starts with an expected failing test.
- **Readiness**: QA_READY_FOR_CODING

---

## 1. Test Objective

Prove that Agentic AI v3.0 behaves as a planner-brain system without regressing safety, determinism, SSE compatibility, or common-intent latency:

- Planner chooses tools, plans, replans, clarifies, degrades, and finalizes.
- Harness enforces policy, validates contracts, stores full data behind `result_ref`, and emits safe observations.
- Tools remain scoped and do not become mini-agents.
- K12 route accuracy and K15 outcome history gate rollout.

---

## 2. Evidence Read

| Type | Path / symbol | Notes |
| :-- | :-- | :-- |
| SRS | `docs/upgrade/ai-python/srs/006_agentic-ai-v3-planner-brain-upgrade.md` | Source AC-1 through AC-18. |
| Tech Spec | `docs/upgrade/ai-python/tech_lead/004_agentic-ai-v3-planner-brain-upgrade.md` | Implementation slices A-G and concrete contracts. |
| Runtime | `ai_python/app/harness/plan_graph.py` | Current PlanGraph executor and callback replan behavior. |
| Runtime | `ai_python/app/harness/tool_registry.py` | Current minimal manifest and decision schema. |
| Runtime | `ai_python/app/harness/scratchpad.py` | Current text-only observation surface. |
| Runtime | `ai_python/app/api/runtime.py` | Registry, HITL pending store, SSE event mapper. |
| Existing tests | `ai_python/tests/test_plan_graph.py` | Topological order, output expectations, replan cap. |
| Existing tests | `ai_python/tests/test_harness_clarify_flow.py` | Clarify action and SSE mapping. |
| Existing tests | `ai_python/tests/test_hitl_pending_store.py` | In-memory and SQLite pending store behavior. |
| Existing tests | `ai_python/tests/test_e2e_agentic_flow.py` | Existing harness e2e slices. |
| K assets | `docs/ai-python/agentic-ai-supporting-assets/013_K12_golden_eval_set.md` | Required/must-not tool assertions. |
| K assets | `docs/ai-python/agentic-ai-supporting-assets/016_K15_intent_tool_success_history.md` | History event schema and privacy rules. |

---

## 3. Test Scope

### In Scope

- Unit tests for manifest, observation envelope, result refs, stores, policy classes.
- Runtime tests for planner-owned replan, bounded replan, duplicate fingerprint, degraded answer labeling.
- Integration tests for chart/data table/input draft artifact tools and SSE compatibility.
- Durable clarify and HITL replay/idempotency tests.
- K12/K15 eval tests and rollout gate behavior.

### Out of Scope

- Real LLM calls.
- Real Spring writes.
- Real Postgres fixtures unless existing ai_python integration fixtures already provide them.
- Frontend visual snapshot testing.
- Non-ERP general knowledge behavior beyond existing domain guard regressions.

---

## 4. Horizontal QA Analysis

| Risk / pattern | Similar scopes checked | Finding | Required test |
| :-- | :-- | :-- | :-- |
| Planner/Harness ownership drift | `execute_with_replan`, `_run_plan_mode` | Callback replan can blur ownership. | P0 tests assert Harness emits `replan_required` and Planner client receives decision context. |
| Raw data leak | `NodeResult.tool_result`, `TurnScratchpad` | Full rows can be visible to planner/answer composer. | P0 tests assert Planner prompt excludes full rows and contains only sample + `result_ref`. |
| Tool manifest ambiguity | `ToolManifest`, registry builder | Current manifest lacks capability/use boundaries. | P0 tests assert every v3 tool has required fields and prompt-visible subset. |
| Fixed-route regression | Plan template fast-path | Template can become v1 route unless provenance/version pinned. | P0 tests assert hand-authored templates are rejected and version mismatch invalidates. |
| RBAC drift | `HarnessPolicy`, K6, live role | K6 must not override live claim. | P0 policy tests for missing claim, staff finance, owner allowed. |
| HITL/clarify replay | HITL store, clarify continuation | Clarify state needs durable semantics. | P0 tests for restart resume and no side-effect node replay. |
| SSE compatibility | `_event_to_stream_chunk` | Frontend expects existing event keys. | P1 tests for `chart`, `data_table`, `draft`, `inventory_draft`, `clarify`, `delta`, `done`. |
| K15 poisoning | History outcome weighting | Degraded outcomes must not promote templates. | P0 tests for demotion/down-weight. |

---

## 5. Test Matrix

### TC-A: Rich Manifest and Registry

| ID | Level | Scenario | Input / setup | Expected result | Priority |
| :-- | :-- | :-- | :-- | :-- | :-- |
| TC-A-001 | Unit | Every registered v3 tool declares required manifest fields. | Build registry with all default tools and v3 flags enabled. | No manifest missing `capability`, `produces`, `consumes`, `side_effect_class`, `observation_schema`. | P0 |
| TC-A-002 | Unit | Planner prompt excludes governance-only fields. | Manifest includes `eval_cases`, `rbac_required`, `cache_policy`, internal `preconditions`. | `tools_manifest_text()` excludes governance-only values and includes use boundaries/examples. | P0 |
| TC-A-003 | Unit | Manifest version changes on contract change. | Register tool, compute version, change `args_schema`. | New `manifest_version` differs. | P0 |
| TC-A-004 | Unit | Similar tools have clear boundaries. | `answer_composer`, `data_table_builder`, `chart_builder`, `input_table_draft_builder`. | Each has non-empty `when_to_use` and `when_not_to_use`; no duplicate capability text. | P1 |
| TC-A-005 | Unit | Side-effect class drives policy/retry. | Manifest declares `non_idempotent_write`. | Retry helper refuses silent retry. | P0 |

Expected initial failure before code:

```text
AttributeError: 'ToolManifest' object has no attribute 'capability'
```

Command:

```powershell
cd ai_python
python -m pytest tests/test_tool_manifest_v3.py -q
```

---

### TC-B: Observation Contract and Result Ref

| ID | Level | Scenario | Input / setup | Expected result | Priority |
| :-- | :-- | :-- | :-- | :-- | :-- |
| TC-B-001 | Unit | Large row result is converted to safe observation. | ToolResult with 100 rows and sensitive fields. | Observation has `row_count=100`, <=20 `sample_rows`, `truncated=True`, `masked=True`, no full rows. | P0 |
| TC-B-002 | Unit | Full data stored behind tenant-scoped `result_ref`. | Store result under tenant `t1`; resolve as tenant `t1`. | Data resolves. | P0 |
| TC-B-003 | Unit | Tenant mismatch cannot resolve `result_ref`. | Store under `t1`; resolve as `t2`. | Store returns `None` or policy error; no data leak. | P0 |
| TC-B-004 | Runtime | Planner prompt contains result handle but not full rows. | SQL returns 30 rows; planner receives observation context. | Prompt contains `result_ref`, `row_count`, sample; does not contain row 21. | P0 |
| TC-B-005 | Integration | Chart builder renders from `result_ref`, not sample. | Full result has 30 rows; sample has 20. | Chart/data table uses all 30 rows through Harness resolution. | P0 |
| TC-B-006 | Unit | Raw SQL/stack/provider errors are sanitized. | Tool exception with SQL and stack trace text. | Observation has safe `error_kind`, no raw SQL or stack line. | P0 |

Expected initial failure before code:

```text
ModuleNotFoundError: No module named 'app.harness.observation'
```

Command:

```powershell
cd ai_python
python -m pytest tests/test_observation_contract.py tests/test_result_ref_store.py -q
```

---

### TC-C: Planner-Owned Replan

| ID | Level | Scenario | Input / setup | Expected result | Priority |
| :-- | :-- | :-- | :-- | :-- | :-- |
| TC-C-001 | Runtime | Failed tool emits `replan_required` observation. | Tool returns `ok=False`. | Node result/observation has `replan_required=True` and sanitized failure. | P0 |
| TC-C-002 | Runtime | Planner, not Harness, chooses replacement plan. | Fake planner receives failed node observation and returns new PlanGraph. | Orchestrator calls fake planner for decision; Harness does not directly synthesize plan. | P0 |
| TC-C-003 | Runtime | Duplicate failure fingerprint is short-circuited. | Same tool args fail twice with same fingerprint. | Replan stops and emits degraded final answer or clarify. | P0 |
| TC-C-004 | Runtime | Replan count bounded. | Fake planner keeps failing plan; max=2. | Exactly 2 replans, then degraded labeled final answer. | P0 |
| TC-C-005 | Runtime | Non-idempotent write is not retried silently. | Tool manifest `non_idempotent_write`, first failure. | No second tool execution; Planner receives explicit failure. | P0 |
| TC-C-006 | Security | Failure detail hides raw SQL internals. | Failure includes `SELECT * FROM financeledger`. | Planner/user observations do not include raw SQL. | P0 |

Expected initial failure before code:

```text
AssertionError: Harness called replan callback directly
```

Command:

```powershell
cd ai_python
python -m pytest tests/test_plan_replan_ownership.py tests/test_plan_graph.py -q
```

---

### TC-D: Execution Tier and Plan Templates

| ID | Level | Scenario | Input / setup | Expected result | Priority |
| :-- | :-- | :-- | :-- | :-- | :-- |
| TC-D-001 | Unit | Template promotion requires Planner provenance. | Plan record without `source="planner_generated"`. | Store rejects promotion. | P0 |
| TC-D-002 | Unit | Template pins manifest/K/policy versions. | Store template with versions. | Retrieved record has all pinned versions. | P0 |
| TC-D-003 | Runtime | Version mismatch invalidates template. | Current `manifest_version` differs from stored. | No template hit; full Planner pass occurs. | P0 |
| TC-D-004 | Runtime | Low-risk common intent can hit template. | Matching normalized intent, role, versions, clean success stats. | Template plan executes through Harness without planner LLM call. | P1 |
| TC-D-005 | Runtime | Template still enforces policy. | Staff hits owner-only finance template. | Harness blocks tool call; no data leak. | P0 |
| TC-D-006 | Runtime | Degraded outcome demotes template. | Template execution ends `degraded`. | `degraded_count` increments and template no longer preferred. | P0 |
| TC-D-007 | Observability | Execution tier recorded. | Template hit and planner fallback runs. | Trace records `execution_tier=template` or `execution_tier=planner`. | P1 |

Expected initial failure before code:

```text
ModuleNotFoundError: No module named 'app.harness.plan_template_store'
```

Command:

```powershell
cd ai_python
python -m pytest tests/test_plan_template_store.py -q
```

---

### TC-E: Artifact Builder Tools and SSE

| ID | Level | Scenario | Input / setup | Expected result | Priority |
| :-- | :-- | :-- | :-- | :-- | :-- |
| TC-E-001 | Integration | List request emits data table artifact. | User asks "liệt kê sản phẩm sắp hết hàng". | Planner chooses `sql_query -> data_validator -> data_table_builder -> answer_composer`; SSE `data_table`. | P0 |
| TC-E-002 | Integration | Chart request emits chart artifact. | User asks trend/comparison. | Planner chooses `chart_builder`; SSE `chart`. | P0 |
| TC-E-003 | Integration | Non-chartable data replans to table/summary. | Chart builder rejects data shape. | Planner replans to `data_table_builder` or degraded summary with explicit label. | P0 |
| TC-E-004 | Integration | Input draft request emits HITL draft, no commit. | User asks create inventory receipt. | `input_table_draft_builder`/draft tool emits HITL payload; no Spring commit before confirm. | P0 |
| TC-E-005 | Regression | Existing SSE wrapper remains compatible. | Emit `chart`, `data_table`, `draft`, `inventory_draft`, `clarify`. | `_event_to_stream_chunk()` maps to existing top-level keys. | P1 |
| TC-E-006 | Runtime | Answer composer references artifacts without duplicating large table. | Observation has artifact ref and table result ref. | Final answer mentions artifact and short summary only. | P1 |

Expected initial failure before code:

```text
KeyError: unknown tool: data_table_builder
```

Command:

```powershell
cd ai_python
python -m pytest tests/test_v3_artifact_tools.py tests/test_chart_pipeline.py tests/test_query_table_sse.py tests/test_answer_composer.py -q
```

---

### TC-F: Clarification and In-flight Plan State

| ID | Level | Scenario | Input / setup | Expected result | Priority |
| :-- | :-- | :-- | :-- | :-- | :-- |
| TC-F-001 | Runtime | Clarify mid-plan persists state. | Planner issues clarify after first node. | Store contains original question, plan id/hash, completed node ids, resume mode. | P0 |
| TC-F-002 | Runtime | Clarify survives runtime recreation. | Store state, create new runtime, resume. | Runtime resumes or replans deterministically. | P0 |
| TC-F-003 | Runtime | Completed side-effect node is not replayed. | Completed `idempotent_write`/draft node before clarify. | Resume does not invoke it again. | P0 |
| TC-F-004 | Runtime | Expired result refs force replan without replaying side effects. | Result ref expired after clarify. | Planner receives missing-ref observation and replans safe path. | P0 |
| TC-F-005 | Regression | Existing data-query clarify resume still runs loop, not HITL. | `clarify_kind=harness_data_query`, no pending HITL. | Loop reruns and final answer is produced. | P1 |
| TC-F-006 | Security | Tenant mismatch cannot resume clarify state. | State stored for tenant `t1`, resume as `t2`. | Resume denied/expired; no tool execution. | P0 |

Expected initial failure before code:

```text
AssertionError: clarify state was not persisted
```

Command:

```powershell
cd ai_python
python -m pytest tests/test_v3_clarify_state.py tests/test_harness_clarify_flow.py tests/test_hitl_pending_store.py -q
```

---

### TC-G: K15 History and K12 Eval Gate

| ID | Level | Scenario | Input / setup | Expected result | Priority |
| :-- | :-- | :-- | :-- | :-- | :-- |
| TC-G-001 | Unit | K15 event appends after clean success. | Successful v3 data query. | Store has `outcome.status=success`, plan hash, tools, cost, asset versions. | P0 |
| TC-G-002 | Unit | Degraded outcome distinct from success. | Budget exhausted or dedup stopped. | Store has `outcome.status=degraded`; not counted as clean success. | P0 |
| TC-G-003 | Unit | HITL/clarify pending distinct statuses. | Draft pending and clarify pending. | Store uses `hitl_pending` and `clarify_pending`. | P0 |
| TC-G-004 | Privacy | K15 stores no raw tenant/user/question/SQL/PII. | Event built from user request with PII. | Raw tenant id, user id, phone, question, SQL absent; tenant hash present. | P0 |
| TC-G-005 | Eval | K12 required/must-not tools enforced. | Run subset eval_001 to eval_004 with fake planner/tools. | Required tools called, forbidden tools not called. | P0 |
| TC-G-006 | Eval | Route accuracy threshold blocks rollout. | Simulated score below configured threshold. | `agentic_v3_enabled` rollout gate fails. | P0 |
| TC-G-007 | Observability | Trace logs K asset versions. | Run v3 turn using K assets. | Trace has K12/K15 and relevant K versions. | P1 |

Expected initial failure before code:

```text
ModuleNotFoundError: No module named 'app.harness.history_store'
```

Command:

```powershell
cd ai_python
python -m pytest tests/test_k15_history_store.py tests/test_v3_eval_gate.py tests/test_observability.py -q
```

---

## 6. Acceptance Criteria Mapping

| AC | Primary tests |
| :-- | :-- |
| AC-1 | TC-C-002, TC-C-003 |
| AC-2 | TC-A-001, TC-A-002, TC-A-003 |
| AC-3 | TC-E-001, TC-E-002, TC-E-004 |
| AC-4 | TC-D-005, TC-G-005 |
| AC-5 | TC-C-001 through TC-C-005 |
| AC-6 | TC-E-004, existing `test_hitl_resume_flow.py` |
| AC-7 | TC-G-005 |
| AC-8 | TC-G-001 through TC-G-004 |
| AC-9 | Existing flag regression tests plus TC-D-004 fallback path |
| AC-10 | TC-E-005 |
| AC-11 | TC-A-005, TC-D-005 |
| AC-12 | TC-E-001 through TC-E-003 |
| AC-13 | TC-D-003 through TC-D-007 |
| AC-14 | TC-B-001 through TC-B-006 |
| AC-15 | TC-C-004, TC-E-003, TC-G-002 |
| AC-16 | Existing `test_hitl_resume_flow.py` plus TC-F-003 |
| AC-17 | TC-D-005 and policy tests for live claim fail-closed behavior |
| AC-18 | TC-F-001 through TC-F-006 |

---

## 7. Failure Modes

| Failure | Classification | Expected behavior | Test IDs |
| :-- | :-- | :-- | :-- |
| Planner asks unauthorized finance tool | AI validation/policy | Harness blocks before execution; K15 records policy block; no data leak. | TC-D-005, TC-G-004 |
| Tool result includes raw PII | Contract drift | Observation masks PII and stores safe sample only. | TC-B-001, TC-G-004 |
| Artifact builder receives expired `result_ref` | Tool integration | Harness returns missing-ref observation; Planner replans/degrades safely. | TC-F-004 |
| Plan template uses stale manifest | Runtime flow | Template invalidated and Planner pass runs. | TC-D-003 |
| Replan loop repeats same failed args | Runtime flow | Duplicate fingerprint short-circuits. | TC-C-003 |
| Non-idempotent write fails | Guardrail | No silent retry, no duplicate write. | TC-C-005, TC-F-003 |
| Clarify resume tenant mismatch | Guardrail | Resume denied/expired, no tool execution. | TC-F-006 |
| K12 route accuracy below threshold | Eval gate | v3 rollout blocked. | TC-G-006 |

---

## 8. Test Data / Mocks

| Data / mock | Purpose | Location / creation |
| :-- | :-- | :-- |
| Fake planner client | Return deterministic `PlannerDecision` and `PlanGraph` without real LLM. | New tests under `ai_python/tests/`; follow `_FakeClient` pattern from `test_harness_clarify_flow.py`. |
| Fake tool with large rows | Prove observation truncation and `result_ref`. | `test_observation_contract.py`. |
| Fake chart/table builders | Prove artifact tools consume `result_ref`. | `test_v3_artifact_tools.py`. |
| SQLite temp path | Test K15/template/clarify stores. | `tmp_path` fixture. |
| K12 subset | Eval route assertions for eval_001 to eval_004. | Load from `docs/ai-python/agentic-ai-supporting-assets/013_K12_golden_eval_set.md` or inline minimal fixtures. |
| K15 event sample | Privacy/outcome tests. | Use schema from `016_K15_intent_tool_success_history.md`. |
| Role claims | RBAC fail-closed tests. | `role="staff"`, `role="owner"`, `permissions=()`, missing role. |

---

## 9. Verification Commands

Focused new-test command:

```powershell
cd ai_python
python -m pytest tests/test_tool_manifest_v3.py tests/test_observation_contract.py tests/test_result_ref_store.py tests/test_plan_replan_ownership.py tests/test_plan_template_store.py tests/test_v3_artifact_tools.py tests/test_v3_clarify_state.py tests/test_k15_history_store.py tests/test_v3_eval_gate.py -q
```

Existing regression slices:

```powershell
cd ai_python
python -m pytest tests/test_plan_graph.py tests/test_plan_parallel.py tests/test_harness_orchestrator.py tests/test_harness_clarify_flow.py tests/test_hitl_pending_store.py tests/test_hitl_resume_flow.py tests/test_e2e_agentic_flow.py tests/test_observability.py -q
```

Full AI regression:

```powershell
cd ai_python
python -m pytest tests -q
```

Documentation sanity:

```powershell
git diff --check -- docs/upgrade/ai-python/srs/006_agentic-ai-v3-planner-brain-upgrade.md docs/upgrade/ai-python/tech_lead/004_agentic-ai-v3-planner-brain-upgrade.md docs/upgrade/ai-python/qa/004_agentic-ai-v3-planner-brain-upgrade.md
```

---

## 10. QA Readiness

**Status:** QA_READY_FOR_CODING

**Reason:** The QA matrix covers every SRS acceptance criterion and every Tech Spec slice with an expected failing test path before implementation. Remaining production tuning values are testable through settings and do not block Coding Agent from implementing the contracts.

**Instructions to Coding Agent:**

1. Start each slice with the listed failing tests.
2. Do not merge implementation that passes only helper-level tests; at least one runtime/integration test must cover each slice.
3. Keep tests deterministic with fake LLM/tool/store clients.
4. Treat any raw SQL, PII, bearer token, stack trace, or full result set in Planner prompt/final answer as a P0 failure.
5. Report route accuracy and K15 outcome counts before enabling v3 flags.
