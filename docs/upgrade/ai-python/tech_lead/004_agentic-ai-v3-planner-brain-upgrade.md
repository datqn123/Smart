# Tech Spec 004 (upgrade/ai-python): Agentic AI v3.0 Planner-Brain Upgrade

- **SRS ref**: `docs/upgrade/ai-python/srs/006_agentic-ai-v3-planner-brain-upgrade.md`
- **Stage**: TECH_SPEC_WRITER
- **Date**: 2026-06-07
- **Mode**: AUTO_DOCS
- **Scope**: AI Agentic runtime architecture, tool contracts, planner loop, eval/observability
- **CodeGraph**: `status --json`, `context("SRS-006 Agentic AI v3 planner brain upgrade tech spec QA spec tool manifest observation contract execution tier")`
- **Superpowers alignment**: writing-plans principles; exact slices, files, contracts, tests, and handoff boundaries.
- **Readiness**: READY_FOR_CODING

---

## 1. Goal

Upgrade the AI runtime from route-driven v1/v2 behavior to Agentic AI v3.0 where Planner/Reasoner owns reasoning and next-action selection, Harness owns execution/safety, and tools expose scoped capabilities with explicit manifests, observation contracts, artifact outputs, and eval gates.

This handoff is docs-only. The Coding Agent must implement test-first and must not broaden scope into unrelated graph or UI refactors.

---

## 2. Evidence Read

| Type | Path / symbol | Finding |
| :-- | :-- | :-- |
| SRS | `docs/upgrade/ai-python/srs/006_agentic-ai-v3-planner-brain-upgrade.md` | Defines v3 ownership, rich manifest, `result_ref`, plan templates, K12/K15 gates, AC-18 clarify durability. |
| Runtime | `ai_python/app/harness/plan_graph.py` | Existing `PlanGraph`, `PlanExecutor`, `execute_with_replan`; currently callback-driven replan can make Harness appear to own replan. |
| Runtime | `ai_python/app/harness/tool_registry.py` | `ToolManifest` only has `name`, `description`, `args_schema`, `has_hitl`; needs v3 contract expansion. |
| Runtime | `ai_python/app/harness/scratchpad.py` | Observation is plain text with max length; needs structured observation contract and safe planner surface. |
| Runtime | `ai_python/app/harness/policy.py` | Policy maps only `data_read`, `draft_create`, `chat`; lacks artifact builder and side-effect classes. |
| Runtime | `ai_python/app/harness/orchestrator.py` | Existing harness loop, PlanGraph mode, HITL resume, cache, trace; `_run_plan_mode` currently replans directly through callback. |
| API runtime | `ai_python/app/api/runtime.py` | Registry built in `_build_tool_registry`; HITL pending store already supports in-memory/SQLite family. |
| Settings | `ai_python/app/config/graph_settings.py` | Existing flags: harness loop, plan DAG, answer composer, capability guard, trace, cache. |
| Tests | `ai_python/tests/test_plan_graph.py` | Existing coverage for topo order, output expectations, callback replan cap. |
| Tests | `ai_python/tests/test_harness_clarify_flow.py` | Existing clarify SSE and resume tests. |
| K assets | `docs/ai-python/agentic-ai-supporting-assets/013_K12_golden_eval_set.md` | Golden eval cases define required/must-not tools, latency/cost, route assertions. |
| K assets | `docs/ai-python/agentic-ai-supporting-assets/016_K15_intent_tool_success_history.md` | Event contract for plan hash, tools, replan count, cost, outcome, failure detail. |

---

## 3. Scope Boundary

### In Scope

- Expand tool manifest and registry contracts for v3.
- Add structured planner decisions for `call_tool`, `plan_graph`, `clarify`, `final_answer`, and `degrade_final_answer`.
- Refactor PlanGraph replan ownership so Harness emits `replan_required` observations and Planner decides.
- Add `result_ref` storage/resolution so Planner never receives full result sets.
- Add plan template fast-path with version pinning and invalidation.
- Add artifact-builder tools for `answer`, `chart`, `data_table`, and `input_table_draft` paths where missing.
- Add durable clarify state using the pending-store family already used for HITL.
- Add K15-compatible history and K12 route/eval assertions.

### Out of Scope

- Replacing Spring as the source of truth for RBAC, writes, transactions, or persistence.
- Direct AI database writes without explicit HITL confirmation.
- Rebuilding frontend visual design.
- Adding non-ERP general knowledge behavior.
- Editing unrelated LangGraph v1 nodes except to wrap them as v3 tools or keep rollback compatibility.

### Ownership

| Layer | Owns | Must not own |
| :-- | :-- | :-- |
| Planner/Reasoner | Goal interpretation, tool choice, PlanGraph generation, replan/clarify/degrade/finalize decision. | Policy enforcement, tenant/RBAC validation, raw data storage, hidden retries inside tools. |
| Harness | Tool execution envelope, policy/RBAC, tenant scope, budget, HITL/clarify state, audit, validation, sanitization, `result_ref` resolution. | Broad reasoning, choosing next plan, exposing raw SQL/data/stack traces to Planner or user. |
| Tools | One bounded capability with explicit input/output schemas and artifact/result contracts. | Cross-tool planning, changing user goal, selecting fallback strategy beyond local deterministic retry. |
| API runtime | Auth context propagation, stream/event mapping, feature flags, pending store wiring. | Backend business authorization decisions beyond passing live claims into Harness. |
| Spring backend | Business rules, RBAC source of truth, writes, transactions. | Agent reasoning or planner prompt construction. |

---

## 4. Architecture Decision

### Decision

Implement v3 as a **PlanGraph-first agentic runtime with reactive fallback and a template fast-path**:

1. Execution tier tries a validated plan template only for low-risk, high-confidence, common intents.
2. Otherwise Planner produces either a one-step reactive action or a PlanGraph.
3. Harness validates and executes every tool call.
4. Harness emits structured observations and `replan_required` signals.
5. Planner decides whether to replan, clarify, degrade, or finalize.

### Decisions Resolving SRS Open Questions

| SRS item | Decision for coding |
| :-- | :-- |
| OQ-1 implementation-first mode | Build PlanGraph-first because `PlanGraph`, `PlanExecutor`, and tests already exist. Keep reactive loop for ambiguity/high-risk turns and fallback. |
| OQ-4 K15 persistence | Add a SQLite-backed `IntentHistoryStore` under `ai_python/app/harness/history_store.py`; use in-memory implementation in unit tests and SQLite for integration tests/local runtime. |
| OQ-5 K6 vs live claim | Live backend/JWT claim wins. K6 is planner advisory only. Missing live claim fails closed for protected tools. |
| OQ-6 template store | Add SQLite-backed `PlanTemplateStore` under `ai_python/app/harness/plan_template_store.py`; store `manifest_version`, K asset versions, `policy_version`, plan hash, normalized intent key, and outcome stats. |
| OQ-7 observation sample size | Default `sample_limit=20`; QA may tune. Full data never enters Planner and is accessible only by `result_ref`. |

### ADR Required?

- **Required**: Yes
- **ADR path**: `docs/upgrade/ai-python/tech_lead/004_agentic-ai-v3-planner-brain-upgrade.md` is the architecture handoff for this upgrade. A separate ADR is not required unless coding changes persistence beyond SQLite/local stores or changes cross-service RBAC ownership.

---

## 5. Horizontal Analysis

| Pattern / risk | Similar scopes checked | Finding | Required action |
| :-- | :-- | :-- | :-- |
| Replan ownership | `PlanExecutor.execute_with_replan`, `_run_plan_mode`, SRS AR-1/AR-2 | Current callback shape lets Harness execute a replan loop directly. | Introduce explicit `ReplanRequired` observation/result state and route next decision through Planner. |
| Manifest drift | `ToolManifest`, `_build_tool_registry`, existing tool manifests | Current manifest is too small for tool selection and PlanGraph data flow. | Add v3 manifest fields plus prompt-surface/governance split. |
| Result leakage | `NodeResult.tool_result`, `TurnScratchpad.add_observation`, `_compose_plan_answer` | Full rows can flow through `tool_result` and into answer composer. | Add Harness-held `ResultRefStore`; Planner sees observation plus opaque handle only. |
| Fast-path regression | `agentic_plan_dag_enabled`, cache, K15 history | A template fast-path can become v1 routing if hand-authored or stale. | Only promote Planner-generated eval-passing plans; pin versions; invalidate on manifest/K/policy changes. |
| HITL/clarify durability | `PendingHitlStore`, clarify SSE tests | HITL has a durable store family; clarify still relies mostly on request continuation context. | Add pending clarify state using same store family; no replay of completed side-effect nodes. |
| RBAC source | `HarnessPolicy`, `CapabilityMatrix`, K6 asset | Policy lacks live permission tuple and artifact tool coverage. | Add `permissions` to `TurnContext`; fail closed for protected capabilities. |
| SSE compatibility | `_event_to_stream_chunk`, existing chart/data table events | Frontend expects existing event names. | Keep event names and payload wrappers: `chart`, `data_table`, `draft`, `inventory_draft`, `clarify`, `delta`, `done`. |

---

## 6. Implementation Slices

| Slice | User-visible result | Primary files |
| :-- | :-- | :-- |
| A | Tools are discoverable by Planner with clear capabilities, data-flow contracts, risk, RBAC, side-effect class, examples. | `tool_registry.py`, tool classes, `api/runtime.py`, tests |
| B | Planner receives safe observations and opaque `result_ref`; chart/table tools render from full data without leaking it to Planner. | `result_store.py`, `observation.py`, `plan_graph.py`, `scratchpad.py`, tools |
| C | Replan is Planner-owned; Harness only signals `replan_required` and enforces limits. | `plan_graph.py`, `orchestrator.py`, tests |
| D | Fast-path plan templates improve common intents without recreating v1 fixed routes. | `plan_template_store.py`, `history_store.py`, `orchestrator.py`, settings |
| E | Artifact selection is tool-driven for answer/chart/data table/input draft. | `api/runtime.py`, `graph/tools/*`, `orchestrator.py`, SSE mapping |
| F | Clarify state survives turns/restarts and never replays completed side-effect nodes. | `clarify_store.py` or shared pending store, `api/runtime.py`, `orchestrator.py` |
| G | K12/K15 eval and observability gate rollout. | `evals` or tests, `observability.py`, `history_store.py`, docs/assets |

---

## 7. Contracts

### 7.1 Planner Decision Contract

Add or replace `DecisionSchema` with v3 fields while keeping backward compatibility for existing reactive loop tests.

```python
class PlannerAction(str, Enum):
    CALL_TOOL = "call_tool"
    PLAN_GRAPH = "plan_graph"
    CLARIFY = "clarify"
    FINAL_ANSWER = "final_answer"
    DEGRADE_FINAL_ANSWER = "degrade_final_answer"

class PlannerDecision(BaseModel):
    action: PlannerAction
    tool_call: ToolCall | None = None
    plan_graph: PlanGraph | None = None
    final_answer: str | None = None
    clarify: ClarifyRequest | None = None
    degraded_reason: str | None = None
    trace_reasoning: str = ""
```

Rules:

- `trace_reasoning` is trace-only and must not be sent to the user.
- `degrade_final_answer` must use a Vietnamese incomplete-answer label and list missing/unverified data.
- Planner may request only tools present in the registry.

### 7.2 Rich Tool Manifest Contract

Replace `ToolManifest` with a structured dataclass or Pydantic model:

```python
from collections.abc import Sequence

@dataclass(frozen=True)
class ToolManifest:
    name: str
    description: str
    capability: str
    args_schema: dict[str, Any] | str
    output_schema: dict[str, Any] | str
    output_artifact_types: Sequence[str] = ()
    has_hitl: bool = False
    preconditions: Sequence[str] = ()
    when_to_use: str = ""
    when_not_to_use: str = ""
    risk_level: Literal["low", "medium", "high"] = "low"
    rbac_required: Sequence[str] = ()
    budget_class: Literal["cheap", "standard", "expensive"] = "standard"
    cache_policy: Literal["none", "tenant_scoped", "global_static"] = "none"
    eval_cases: Sequence[str] = ()
    examples: Sequence[str] = ()
    side_effect_class: Literal["read_only", "idempotent_write", "non_idempotent_write"] = "read_only"
    produces: Sequence[str] = ()
    consumes: Sequence[str] = ()
    result_ref_policy: Literal["inline", "result_ref"] = "inline"
    observation_schema: str = "ObservationEnvelope"
```

`tools_manifest_text()` must include only planner-visible fields:

- `name`
- `description`
- `capability`
- compact `args_schema`
- `output_artifact_types`
- `when_to_use`
- `when_not_to_use`
- condensed `examples`
- `produces`
- `consumes`

Governance-only fields stay out of prompt by default:

- `eval_cases`
- full `output_schema`
- `cache_policy`
- internal `preconditions`
- `rbac_required`
- `side_effect_class`
- version fields

### 7.3 Observation Envelope

Add `ai_python/app/harness/observation.py`:

```python
class ObservationEnvelope(BaseModel):
    tool_name: str
    ok: bool
    error_kind: str | None = None
    message: str = ""
    schema: list[dict[str, str]] = Field(default_factory=list)
    row_count: int | None = None
    aggregate_stats: dict[str, Any] = Field(default_factory=dict)
    sample_rows: list[dict[str, Any]] = Field(default_factory=list)
    masked: bool = False
    truncated: bool = False
    result_ref: str | None = None
    artifact_refs: list[str] = Field(default_factory=list)
    replan_required: bool = False
    failure_fingerprint: str | None = None
```

Rules:

- Planner receives `ObservationEnvelope.model_dump()` or compact JSON, never raw rows beyond `sample_rows`.
- `sample_rows` limit is 20.
- PII and raw SQL are masked.
- `result_ref` is opaque and tenant/correlation scoped.
- Artifact builders resolve `result_ref` through Harness, not through Planner prompt.

### 7.4 Result Ref Store

Add `ai_python/app/harness/result_store.py`:

```python
@dataclass(frozen=True)
class StoredResult:
    result_ref: str
    tool_name: str
    tenant_id: str | None
    correlation_id: str
    data: dict[str, Any]
    created_at: float

class ResultRefStore(Protocol):
    def put(self, *, tool_name: str, data: dict[str, Any], ctx: TurnContext) -> str:
        raise NotImplementedError

    def get(self, result_ref: str, *, ctx: TurnContext) -> StoredResult | None:
        raise NotImplementedError

    def delete(self, result_ref: str) -> None:
        raise NotImplementedError
```

Implementation:

- `InMemoryResultRefStore` for unit tests.
- Optional SQLite implementation only if needed by clarify/HITL resume; otherwise result refs can be turn-scoped.
- Tenant mismatch returns `None` and records a policy block.

### 7.5 Plan Template Store

Add `ai_python/app/harness/plan_template_store.py`:

```python
class PlanTemplateRecord(BaseModel):
    normalized_intent_key: str
    plan_graph_hash: str
    plan_graph: PlanGraph
    manifest_version: str
    policy_version: str
    asset_versions: dict[str, str]
    role_scope: str
    success_count: int = 0
    degraded_count: int = 0
    failure_count: int = 0
```

Promotion rules:

- Promote only Planner-generated plans that pass K12 assertions and have clean `success` outcomes.
- Demote on any contract version mismatch, degraded outcome, policy block, or repeated failure.
- Never hand-author templates as routes.

### 7.6 K15 History Store

Add `ai_python/app/harness/history_store.py`:

```python
class IntentHistoryEvent(BaseModel):
    event_id: str
    created_at: str
    schema_version: str = "1.0"
    context: dict[str, Any]
    intent: dict[str, Any]
    plan: dict[str, Any]
    outcome: dict[str, Any]
    asset_versions: dict[str, str]
    failure_detail: dict[str, Any] | None = None
```

Use SQLite for local/integration runtime. Hash tenant id before storing. Do not store raw question, raw SQL, user id, phone, email, or bearer token.

### 7.7 Policy Contract

Extend `TurnContext`:

```python
from collections.abc import Sequence

permissions: Sequence[str] = ()
```

Policy inputs:

- `role`
- `permissions`
- `tenant_id`
- `tool_name`
- `side_effect_class`
- `rbac_required`

Rules:

- Missing live role/permissions fails closed for `draft_create`, protected finance data, and write-like tools.
- K6 may only add planner hints; it must never override live claims.
- Artifact builders are read-only unless they create HITL draft payloads.

---

## 8. Files For Coding Agent

### Read First

- `docs/upgrade/ai-python/srs/006_agentic-ai-v3-planner-brain-upgrade.md`
- `ai_python/app/harness/plan_graph.py`
- `ai_python/app/harness/tool_registry.py`
- `ai_python/app/harness/orchestrator.py`
- `ai_python/app/harness/policy.py`
- `ai_python/app/harness/scratchpad.py`
- `ai_python/app/harness/hitl_store.py`
- `ai_python/app/api/runtime.py`
- `ai_python/app/config/graph_settings.py`
- `docs/ai-python/agentic-ai-supporting-assets/013_K12_golden_eval_set.md`
- `docs/ai-python/agentic-ai-supporting-assets/016_K15_intent_tool_success_history.md`

### Expected To Edit

- `ai_python/app/harness/tool_registry.py`
- `ai_python/app/harness/plan_graph.py`
- `ai_python/app/harness/orchestrator.py`
- `ai_python/app/harness/scratchpad.py`
- `ai_python/app/harness/policy.py`
- `ai_python/app/harness/observability.py`
- `ai_python/app/api/runtime.py`
- `ai_python/app/config/graph_settings.py`
- Existing tools under `ai_python/app/graph/tools/`
- Existing tests under `ai_python/tests/`

### Expected To Add

- `ai_python/app/harness/observation.py`
- `ai_python/app/harness/result_store.py`
- `ai_python/app/harness/history_store.py`
- `ai_python/app/harness/plan_template_store.py`
- `ai_python/app/harness/clarify_store.py` only if existing `hitl_store.py` cannot store clarify records cleanly.
- `ai_python/tests/test_tool_manifest_v3.py`
- `ai_python/tests/test_observation_contract.py`
- `ai_python/tests/test_result_ref_store.py`
- `ai_python/tests/test_plan_replan_ownership.py`
- `ai_python/tests/test_plan_template_store.py`
- `ai_python/tests/test_k15_history_store.py`
- `ai_python/tests/test_v3_eval_gate.py`

### Do Not Edit

- Do not edit Spring backend unless a specific API contract is proven missing.
- Do not edit frontend visual components in this v3 runtime task.
- Do not hand-author fixed routes as plan templates.
- Do not create `CLAUDE.md`.

---

## 9. Slice Handoff

### Slice A: Rich Manifest and Registry

Write failing tests first:

```powershell
cd ai_python
python -m pytest tests/test_tool_manifest_v3.py -q
```

Expected initial failure:

- `ToolManifest` lacks v3 fields.
- `tools_manifest_text()` does not separate planner-visible and governance fields.

Implementation:

- Expand `ToolManifest`.
- Add `manifest_version` on `ToolRegistry`, derived from stable hash of registered manifest fields.
- Update all tool classes to declare `capability`, `produces`, `consumes`, `side_effect_class`, and `result_ref_policy`.
- Add policy mapping for `answer_composer`, `build_chart`/`chart_builder`, `data_table_builder`, `data_validator`, and draft tools.

Verification:

```powershell
cd ai_python
python -m pytest tests/test_tool_manifest_v3.py tests/test_harness_scratchpad_registry.py tests/test_harness_policy.py -q
```

### Slice B: Observation Envelope and Result Ref

Write failing tests:

```powershell
cd ai_python
python -m pytest tests/test_observation_contract.py tests/test_result_ref_store.py -q
```

Expected initial failure:

- Observations are plain text.
- Full rows can be sent through `NodeResult.tool_result`.
- No `result_ref` store exists.

Implementation:

- Add `ObservationEnvelope`.
- Add `ResultRefStore`.
- Convert tool results with large data into `result_ref` plus bounded sample.
- Ensure artifact builders can resolve `result_ref` under tenant/correlation scope.

Verification:

```powershell
cd ai_python
python -m pytest tests/test_observation_contract.py tests/test_result_ref_store.py tests/test_plan_graph.py tests/test_e2e_agentic_flow.py -q
```

### Slice C: Planner-Owned Replan

Write failing tests:

```powershell
cd ai_python
python -m pytest tests/test_plan_replan_ownership.py -q
```

Expected initial failure:

- `PlanExecutor.execute_with_replan()` directly invokes a replan callback.
- Failure details may include raw errors.

Implementation:

- Keep `PlanExecutor.execute()` as deterministic executor.
- Replace or wrap `execute_with_replan()` so it emits `NodeResult`/`ObservationEnvelope` with `replan_required=True`.
- Move replan loop decision into `PlannerSubagent`/`HarnessOrchestrator`.
- Bound replan count and duplicate failure fingerprints.
- For `non_idempotent_write`, never retry silently.

Verification:

```powershell
cd ai_python
python -m pytest tests/test_plan_replan_ownership.py tests/test_plan_graph.py tests/test_harness_orchestrator.py -q
```

### Slice D: Execution Tier and Plan Templates

Write failing tests:

```powershell
cd ai_python
python -m pytest tests/test_plan_template_store.py -q
```

Expected initial failure:

- No template store.
- No version-pinned invalidation.
- No trace of execution tier.

Implementation:

- Add `PlanTemplateStore`.
- Add settings:
  - `agentic_v3_enabled`
  - `agentic_v3_plan_template_enabled`
  - `agentic_v3_template_store_path`
  - `agentic_v3_route_accuracy_threshold`
- Execution tier checks template only when normalized intent key, role scope, manifest version, policy version, and K asset versions match.
- Template hit still runs through Harness policy and validation.

Verification:

```powershell
cd ai_python
python -m pytest tests/test_plan_template_store.py tests/test_model_router.py tests/test_semantic_cache.py -q
```

### Slice E: Artifact Builder Tools

Write failing tests:

```powershell
cd ai_python
python -m pytest tests/test_v3_artifact_tools.py -q
```

Expected initial failure:

- `data_table_builder` and `input_table_draft_builder` are not distinct manifest capabilities.
- Chart/table builders may consume raw rows instead of `result_ref`.

Implementation:

- Register artifact tools under v3 names while keeping existing tool implementations where possible.
- `chart_builder` and `data_table_builder` consume `result_ref`.
- `answer_composer` consumes observations and artifact refs, not full tables.
- Input draft tools emit HITL payloads and never commit directly.
- `_event_to_stream_chunk()` keeps existing SSE contract.

Verification:

```powershell
cd ai_python
python -m pytest tests/test_v3_artifact_tools.py tests/test_chart_pipeline.py tests/test_query_table_sse.py tests/test_answer_composer.py tests/test_hitl_resume_flow.py -q
```

### Slice F: Clarify Durable State

Write failing tests:

```powershell
cd ai_python
python -m pytest tests/test_v3_clarify_state.py -q
```

Expected initial failure:

- Clarify continuation does not have durable pending state equivalent to HITL.
- Completed side-effecting nodes are not tracked for replay prevention.

Implementation:

- Store clarify pending state with original question, plan graph, completed node ids, side-effect node ids, and resume mode.
- Resume policy:
  - Read-only completed nodes may be reused through `result_ref` if valid.
  - Side-effecting completed nodes are not re-executed.
  - If result refs expired, Planner must replan without replaying side effects.

Verification:

```powershell
cd ai_python
python -m pytest tests/test_v3_clarify_state.py tests/test_harness_clarify_flow.py tests/test_hitl_pending_store.py -q
```

### Slice G: K12/K15 Eval and Rollout Gate

Write failing tests:

```powershell
cd ai_python
python -m pytest tests/test_k15_history_store.py tests/test_v3_eval_gate.py -q
```

Expected initial failure:

- No K15 event append after every v3 turn.
- No numeric K12 route accuracy gate.

Implementation:

- Append K15-compatible event after every v3 turn: success, failure, degraded, or HITL/clarify pending.
- Distinguish clean `success`, `degraded`, `hitl_pending`, `clarify_pending`, and `failure`.
- Add route accuracy calculation over K12 expected `required_tools` / `must_not_tools`.
- Block `agentic_v3_enabled` rollout when route accuracy falls below configured threshold.

Verification:

```powershell
cd ai_python
python -m pytest tests/test_k15_history_store.py tests/test_v3_eval_gate.py tests/test_observability.py -q
```

---

## 10. Failure Modes

| Failure | Classification | Expected behavior |
| :-- | :-- | :-- |
| Planner chooses unsafe tool | Harness policy | Block before tool call; emit sanitized observation/error; no data leak. |
| Planner repeats same failed args | Runtime flow | Duplicate fingerprint short-circuits; Planner may degrade or clarify within bounded replan count. |
| Tool returns full rows | Contract drift | Harness stores rows behind `result_ref`; Planner sees bounded sample only. |
| Artifact builder cannot render | Tool integration | Harness emits `replan_required`; Planner chooses data table/summary/degrade. |
| Template version mismatch | Contract drift | Template invalidated; full Planner pass required. |
| Missing role/permission claim | RBAC | Fail closed for protected tools and draft/write flows. |
| Clarify resume after restart | State durability | Pending clarify state restored; side-effect nodes not replayed. |
| K15 degraded plan repeats | Feedback poisoning | Degraded/hitl/clarify outcomes weighted below clean success; template demoted. |

---

## 11. Test Plan Summary

| Level | Tests | Expected coverage |
| :-- | :-- | :-- |
| Unit | `test_tool_manifest_v3.py`, `test_observation_contract.py`, `test_result_ref_store.py` | Manifest fields, prompt-surface filtering, sample/masking, tenant-scoped refs. |
| Runtime | `test_plan_replan_ownership.py`, `test_plan_template_store.py`, `test_v3_clarify_state.py` | Planner-owned replan, template invalidation, clarify durable state. |
| Integration | `test_v3_artifact_tools.py`, `test_e2e_agentic_flow.py`, `test_harness_orchestrator.py` | Tool selection, artifact SSE, answer composition, RBAC. |
| Eval | `test_v3_eval_gate.py`, K12 fixtures | Required/must-not tools, route accuracy threshold, rollout blocking. |
| Observability | `test_k15_history_store.py`, `test_observability.py` | K15 event append, status weighting, asset versions, no raw PII/SQL. |

Full focused command:

```powershell
cd ai_python
python -m pytest tests/test_tool_manifest_v3.py tests/test_observation_contract.py tests/test_result_ref_store.py tests/test_plan_replan_ownership.py tests/test_plan_template_store.py tests/test_v3_artifact_tools.py tests/test_v3_clarify_state.py tests/test_k15_history_store.py tests/test_v3_eval_gate.py -q
```

Regression command:

```powershell
cd ai_python
python -m pytest tests -q
```

---

## 12. Coding Readiness

**Status:** READY_FOR_CODING

**Reason:** SRS ownership conflicts have been resolved in the latest SRS revision, CodeGraph identified the runtime blast radius, and this handoff resolves SRS coding blockers with concrete store, policy, and implementation-first decisions.

**Instructions to Coding Agent:**

1. Implement slices A through G in order.
2. For each slice, write the failing tests named above before production changes.
3. Keep feature flags off by default until K12/K15 gates pass.
4. Preserve v1/v2 rollback flags.
5. Do not let `SelfCorrectingSqlRunner` or any tool own broad replan logic.
6. Do not expose raw SQL, stack traces, bearer tokens, raw PII, or full result sets to Planner or final answers.
