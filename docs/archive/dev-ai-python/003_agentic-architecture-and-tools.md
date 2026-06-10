# Agentic AI v3.0 — Architecture & Tools Reference

> **Service:** `ai_python` — ERP Chat Agent  
> **Tech:** FastAPI, LangGraph, OpenAI-compatible LLM, Harness Loop  
> **Audience:** Developers, integrators

---

## 1. System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI (main.py)                     │
│  POST /api/v1/ai/chat/stream    POST /api/v1/ai/chat/invoke │
│  POST /api/v1/ai/chat/transcribe  POST /api/v1/ai/chat/synthesize │
└────────────────────┬────────────────────────────────────┘
                     │ JWT auth
┌────────────────────▼────────────────────────────────────┐
│                 GraphRuntime (runtime.py)                 │
│   LangGraphRuntime ─── OR ─── LangHarnessRuntime          │
│   (legacy)                     (v3 harness loop)          │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│             HarnessOrchestrator (orchestrator.py)         │
│                                                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Intent   │  │ Planner  │  │Executor  │  │ Template │  │
│  │Subagent  │  │Subagent  │  │PlanGraph  │  │ Store    │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Policy   │  │ Budget   │  │ Cache    │  │ K15      │  │
│  │ Gate     │  │ Guard    │  │(semantic)│  │ History  │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              Tool Registry (tool_registry.py)              │
│                                                           │
│ sql_query  schema_explore  catalog_draft  inventory_draft │
│ data_validator  answer_composer  build_chart             │
│ data_table_builder  erp_guide                             │
└─────────────────────────────────────────────────────────┘
```

### 1.1 Two Runtime Modes

| Runtime | When | Description |
|---------|------|-------------|
| `LangGraphRuntime` | `harness_loop_enabled=false` | Legacy compiled LangGraph, full graph invoke per turn |
| `LangHarnessRuntime` | `harness_loop_enabled=true` | Strangler: routes matched intents to Harness loop, others to legacy |

Switch: `harness_loop_enabled` in `GraphSettings`.

### 1.2 Request Flow (SSE Stream)

1. User sends `POST /api/v1/ai/chat/stream` with JWT + ChatRequest
2. JWT validated → role/permissions extracted (server-authoritative)
3. `LangHarnessRuntime.stream()` decides route:
   - Legacy: runs compiled LangGraph, yields chunks
   - Harness: runs `HarnessOrchestrator.run()` which yields typed events
4. SSE events: `progress` | `delta` | `delta_full` | `chart` | `draft` | `inventory_draft` | `data_table` | `clarify` | `error` | `done`

---

## 2. Harness Loop (app/harness/)

The harness is the core v3 agentic loop. It replaces the legacy `planner -> sql -> compose` graph with an LLM-driven decision loop bounded by safety guards.

### 2.1 Turn Lifecycle

```
run() 
  ├─ dispatch()
  │   ├─ Intent analysis (optional)
  │   ├─ Tier decision: template hit? → fast-path
  │   │                    no template → PlannerSubagent plans
  │   ├─ PlanGraph execution (DAG)
  │   │   └─ For each node: resolve deps → check policy → run tool → observation
  │   ├─ Decision loop (reactive, no plan graph):
  │   │   └─ LLM decides: call_tool | clarify | final_answer
  │   └─ FinalAnswer / Clarify / HITL
  └─ finally: K15 history record (always 1 per turn)
```

### 2.2 Key Components

#### `HarnessOrchestrator` (orchestrator.py)
- `run()` — top-level turn orchestrator, always records 1 K15 event
- `_dispatch()` — routes to plan mode, reactive mode, or HITL resume
- `_resume_hitl()` — handles catalog/inventory draft confirmation
- `_run_plan_mode()` — DAG plan execution with template support
- `_decide()` — LLM next-action decision (reactive loop)

#### `IntentSubagent` (intent.py)
- Analyzes user question → `IntentObject` (goal, type, entities, confidence)
- `decide()` → `run` | `clarify` | `auto_assume`
- Fallback heuristic when LLM unavailable

#### `PlannerSubagent` (plan_graph.py)
- Receives intent + tool manifest → produces `PlanGraph` (DAG of `PlanNode`s)
- Each node: `{id, tool, needs[], input_spec, output_expect}`
- Dependency references: `${node_id.field}` for data flow between nodes

#### `PlanExecutor` (plan_graph.py)
- Async DAG executor: respects dependency ordering
- Dependency gating (P1-1): failed dependency → skip dependent nodes
- `execute_with_replan()` — re-plan on failure (limited attempts)
- `run_planner_owned_plan()` — v3: planner owns replan decision (not harness)

#### `AgentHarness` (runtime.py)
- Execution boundary: before/after hooks, audit logging, deny-list
- `run_tool()` / `arun_tool()` — wraps tool calls with audit trail
- Blocks dangerous tools (delete, drop, truncate, exec_shell)

#### `HarnessPolicy` (policy.py)
- Capability check per tool (`data_read`, `draft_create`, etc.)
- RBAC: live JWT permission check against `rbac_required`
- SQL safety: blocks write keywords, multi-statement
- Tenant isolation: cross-tenant access denied

#### `TurnBudget` (budget.py)
- Four boundaries: `max_steps`, `token_budget`, `cost_budget_usd`, `wallclock_timeout_s`
- Raises `BudgetExceeded` → turn degrades gracefully

#### `InMemorySemanticCache` (cache.py)
- Tenant-scoped cache for deterministic tools (`sql_query`, `schema_explore`)
- SHA-256 keyed on `(tool_name, args, tenant_id)`

#### `ModelRouter` (model_router.py)
- Tiered routing: `intent` → haiku, `planner` → sonnet, `sql` → sonnet
- Escalation to opus after `opt_escalate_replan_count` replans

#### `WorkingMemory` (memory.py)
- Trims conversation to last N pairs before LLM reasoning
- `EpisodicMemory` + `InMemorySemanticStore` for recall

---

## 3. All Tools (app/graph/tools/)

Every tool is registered in `ToolRegistry` with a `ToolManifest` that defines its contract for the planner.

### 3.1 ToolManifest Fields

| Field | Purpose | Planner-visible |
|-------|---------|----------------|
| `name` | Unique identifier | Yes |
| `description` | What the tool does | Yes |
| `args_schema` | JSON schema string for arguments | Yes |
| `capability` | e.g. `data_read`, `draft_create` | Yes |
| `when_to_use` | Guidance for planner | Yes |
| `when_not_to_use` | Guidance for planner | Yes |
| `output_artifact_types` | What artifacts this produces | Yes |
| `produces` / `consumes` | Data flow types | Yes |
| `examples` | Example queries | Yes |
| `output_schema` | Full JSON schema | No (governance) |
| `rbac_required` | Required permission flags | No |
| `risk_level` | `low` / `medium` / `high` | No |
| `side_effect_class` | `read_only` / `idempotent_write` / `non_idempotent_write` | No |
| `cache_policy` | `none` / `tenant_scoped` / `global_static` | No |
| `has_hitl` | Requires human-in-the-loop confirmation | No |
| `result_ref_policy` | `inline` / `result_ref` | No |
| `budget_class` | `cheap` / `standard` / `expensive` | No |

### 3.2 Tool Reference

#### `sql_query` — `SqlQueryTool`

Read ERP data using the SQL subgraph with self-correction.

- **Args:** `{"query": "string"}` (natural-language data question)
- **Capability:** `data_read`
- **Side-effect:** `read_only`
- **Risk:** `low`
- **Produces:** `rows`
- **Data flow:** result_ref → downstream tools resolve
- **Self-correcting:** up to N SQL regen + M empty-result retries
- **SSE:** `data_table` event when rows present

**Implementation:** `SelfCorrectingSqlRunner` orchestrates:
1. `generate` — LLM produces SQL from user question
2. `review` — LLM validates SQL shape, schema, safety
3. `execute` — Spring SQL endpoint or stub
4. Loop on failure (limited), loop on empty result (limited)

#### `schema_explore` — `SchemaExploreTool`

Explore database schema without returning actual data.

- **Args:** `{"topic": "string"}`
- **Capability:** `data_read`
- **Side-effect:** `read_only`
- **Risk:** `low`
- **Produces:** `schema`
- **Output:** Schema plan (tables, columns, join hints) or schema artifact

#### `catalog_draft` — `CatalogDraftTool`

Create catalog/product/category draft with HITL (human-in-the-loop) confirmation.

- **Args:** `{"request": "string"}`
- **Capability:** `draft_create`
- **Side-effect:** `non_idempotent_write`
- **Risk:** `high`
- **RBAC:** `draft_create` permission required
- **HITL:** Yes — stops after draft for user confirmation
- **Produces:** `input_table_draft`
- **SSE:** `draft` event with draft payload
- **Confirm flow:** Re-invoke with `clarification_response` → calls Spring commit

#### `inventory_draft` — `InventoryDraftTool`

Create inventory receipt/dispatch document with HITL.

- **Args:** `{"request": "string"}`
- **Capability:** `draft_create`
- **Side-effect:** `non_idempotent_write`
- **Risk:** `high`
- **RBAC:** `draft_create` permission
- **HITL:** Yes
- **SSE:** `inventory_draft` event
- **Confirm flow:** Same pattern as catalog_draft

#### `answer_composer` — `AnswerComposerTool`

Compose Vietnamese final answer from tool observations.

- **Args:** `{"observations": "list", "assumptions": "list[str]"}`
- **Capability:** `answer_compose`
- **Side-effect:** `read_only`
- **Risk:** `low`
- **Produces:** `answer`
- **Consumes:** `observations`, `rows`
- **Output:** Markdown answer with row summaries, follow-up suggestions

#### `build_chart` — `BuildChartTool`

Build a frontend chart payload from tabular rows.

- **Args:** `{"rows": "list", "result_ref": "string"}`
- **Capability:** `chart_build`
- **Side-effect:** `read_only`
- **Risk:** `low`
- **Produces:** `chart`
- **Consumes:** `rows`
- **Data flow:** Accepts either inline rows or result_ref handle
- **Output:** `{chartType, xKey, yKey, title, ...}`

#### `data_table_builder` — `DataTableBuilderTool`

Build a frontend data-table artifact from rows or result_ref.

- **Args:** `{"rows": "list", "result_ref": "string", "title": "string"}`
- **Capability:** `data_table_build`
- **Side-effect:** `read_only`
- **Risk:** `low`
- **Produces:** `data_table`
- **Output:** `{title, rows, row_count}` → SSE `data_table` event

#### `data_validator` — `DataValidatorTool`

Validate rows against required data and basic business constraints.

- **Args:** `{"rows": "list", "required_data": "list[str]"}`
- **Capability:** `data_validate`
- **Side-effect:** `read_only`
- **Risk:** `low`
- **Output:** `{ok, issues[], severity}`

#### `erp_guide` — `ErpGuideTool`

Return concise ERP domain guidance (terminology, context).

- **Args:** `{"topic": "string"}`
- **Capability:** `erp_guide`
- **Side-effect:** `read_only`
- **Risk:** `low`
- **Produces:** `guidance`
- **Output:** Static domain text based on topic keyword (inventory, finance, etc.)

---

## 4. Observation Contract (observation.py)

Every tool result returned to the Planner is wrapped in a bounded, sanitized `ObservationEnvelope`:

| Field | Description |
|-------|-------------|
| `tool_name` | Which tool ran |
| `ok` | Success/failure |
| `error_kind` | `policy_blocked`, `timeout`, `tool_error` |
| `message` | Sanitized text (SQL/stack leaks stripped) |
| `schema_fields` | Column names + types (from first row) |
| `row_count` | Count of rows |
| `aggregate_stats` | Summary statistics |
| `sample_rows` | Masked sample (up to 20 rows) |
| `masked` / `truncated` | Safety flags |
| `result_ref` | Opaque handle to full data in `ResultRefStore` |
| `replan_required` | Signal to planner |
| `failure_fingerprint` | SHA-256 dedup hash (no raw error leaked) |

### 4.1 Data Flow with result_ref

```
Tool runs → full data → InMemoryResultRefStore (Harness-held)
                         ↕ opaque result_ref handle
Planner sees only: schema + count + sample (bounded)
                         ↕ result_ref
Downstream tools (chart, table builder) resolve handle → full rows
```

**Security:**
- Sensitive columns masked (`password`, `email`, `salary`, `cccd`, etc.)
- SQL and stack traces sanitized from error messages
- Tenant-scoped: cross-tenant result_ref resolution denied

---

## 5. Plan Templates (plan_template_store.py)

Auto-promotion of validated plans for fast-path execution (skip Planner LLM).

### Lifecycle

```
Planner generates plan → N clean successes → promoted as template
                                                     ↓
Next same intent → template hit → execute directly → K15 tracked
                                                     ↓
                Degraded/failure → demoted, not preferred next time
```

### Version Pinning (FR-11.8)

Template invalidated when ANY of these drifts:
- `manifest_version` (tool registry hash)
- `policy_version` (policy logic version)
- `asset_versions` (K12, K15 eval versions)
- `role_scope` (role + live permissions fingerprint)

### Storage

| Store | When | Persistence |
|-------|------|-------------|
| `InMemoryPlanTemplateStore` | Default | Process-only |
| `SqlitePlanTemplateStore` | `agentic_v3_template_store_path` set | Disk |

---

## 6. K15 History (history_store.py)

Privacy-safe outcome tracking. One record per turn.

### Fields

- `event_id` — UUID
- `context` — `{tenant_hash}` (SHA-256, no raw tenant)
- `intent` — `{intent_key_hash}` (no raw question)
- `plan` — `{plan_hash, tools[], replan_count, hitl_count}`
- `outcome` — `{status, latency_ms, cost_usd, budget_status}`
- `asset_versions`
- `failure_detail` — only on degraded/failure

### Outcome Statuses (FR-9.5)

| Status | Meaning |
|--------|---------|
| `success` | Clean completion |
| `degraded` | Partial data, budget hit, duplicate detection |
| `failure` | Unhandled error |
| `hitl_pending` | Stopped for human confirmation |
| `clarify_pending` | Stopped for clarification |

---

## 7. RBAC & Policy (policy.py + capability.py)

### Permission Resolution

```
JWT claims (validated) → derive_role_permissions()
  ├─ role: owner | admin | staff | ...
  └─ permissions: tuple of flag strings from "mp" claim

Server-authoritative: overwrites client-supplied metadata (FR-5.4)
```

### Policy Check (per tool call)

1. **RBAC**: tool's `rbac_required` → must be in live permissions
2. **Capability**: `data_read` / `draft_create` → checked against role matrix
3. **SQL safety**: blocks multi-statement, write keywords
4. **Tenant isolation**: cross-tenant args denied
5. **Role-implied capabilities**: owner/admin get `draft_create` + `data_read`

### Sensitive Column Masking (capability.py)

- Non-owner roles: columns like `cost_price`, `margin`, `debt_balance` stripped from row output

---

## 8. Configuration (GraphSettings)

Master switch: `AGENTIC_V3_ENABLED` (default: `1`)

| Setting | Default | Purpose |
|---------|---------|---------|
| `harness_loop_enabled` | false | Route intents to harness loop |
| `harness_loop_intents` | see runtime.py | Which intent labels enter the loop |
| `harness_max_steps` | 6 | Max decision iterations per turn |
| `harness_token_budget` | 0 | Token budget (0=unlimited) |
| `harness_cost_budget_usd` | 0.0 | Cost budget |
| `harness_wallclock_timeout_s` | 30.0 | Wall-clock timeout |
| `agentic_intent_object_enabled` | false | Use LLM intent analysis |
| `agentic_plan_dag_enabled` | false | Use plan DAG mode |
| `agentic_v3_plan_template_enabled` | true | Template promotion |
| `agentic_v3_template_promote_after` | 3 | Clean successes before promotion |
| `agentic_answer_composer_enabled` | false | Enable artifact tools |
| `agentic_semantic_cache_enabled` | false | Enable result cache |
| `agentic_model_routing_enabled` | false | Enable tiered model routing |
| `plan_replan_max` | 2 | Max replans in plan mode |
| `sql_regen_max` | 3 | Max SQL regeneration attempts |
| `sql_empty_retry_max` | 2 | Max empty-result retries |

---

## 9. SSE Event Contract

The API returns `text/event-stream` with these event types:

| Event | Payload | When |
|-------|---------|------|
| `progress` | text | Processing step status |
| `delta` | text | Streaming answer delta |
| `delta_full` | text | Full answer text (non-streaming) |
| `chart` | JSON | Chart spec `{chartType, xKey, yKey, ...}` |
| `draft` | JSON | Catalog draft UI payload |
| `inventory_draft` | JSON | Inventory draft UI payload |
| `data_table` | JSON | Data table `{title, rows, row_count}` |
| `clarify` | JSON | Clarification questions `{questions[], ...}` |
| `error` | text | User-facing error message (Vietnamese) |
| `done` | — | Terminal event |

---

## 10. Module Map

```
app/
├── api/
│   ├── routes.py       # REST endpoints, SSE streaming
│   ├── schemas.py      # Pydantic contracts
│   ├── auth.py         # JWT validation
│   ├── errors.py       # Error envelopes
│   └── runtime.py      # GraphRuntime adapter + build
├── harness/
│   ├── orchestrator.py # Main agentic loop
│   ├── plan_graph.py   # Plan DAG executor, planner subagent
│   ├── intent.py       # Intent analysis + entity resolution
│   ├── policy.py       # Capability + RBAC policy
│   ├── runtime.py      # AgentHarness execution boundary
│   ├── tool_registry.py # Tool registration + manifest
│   ├── scratchpad.py   # Turn scratchpad + decision prompt
│   ├── observation.py  # Observation contract + sanitization
│   ├── result_store.py # result_ref store
│   ├── plan_template_store.py # Template promotion
│   ├── history_store.py # K15 outcome history
│   ├── hitl_store.py   # Pending HITL state
│   ├── budget.py       # Turn budget guards
│   ├── cache.py        # Semantic cache
│   ├── capability.py   # Capability matrix + masking
│   ├── model_router.py # Tiered LLM routing
│   ├── memory.py       # Working memory, episodic, semantic
│   ├── compact.py      # Context compaction
│   ├── observability.py # Metrics + trace recording
│   └── eval_gate.py    # K12 route accuracy gate
├── graph/
│   ├── state.py        # AgentState TypedDict
│   ├── deps.py         # GraphDeps injection
│   ├── tools/          # Harness tool adapters
│   │   ├── sql_query.py
│   │   ├── catalog_draft.py
│   │   ├── inventory_draft.py
│   │   ├── schema_explore.py
│   │   ├── answer_composer.py
│   │   ├── build_chart.py
│   │   ├── data_table_builder.py
│   │   ├── data_validator.py
│   │   ├── erp_guide.py
│   │   ├── _result_ref.py
│   │   └── _state.py
│   ├── *.py            # Graph nodes, subgraphs, schema, etc.
├── llm/
│   ├── protocol.py     # LlmClient port
│   ├── openai_compatible.py # ChatOpenAI wrapper
│   ├── registry.py     # Role → LlmClient registry
│   ├── structured.py   # JSON-only structured output
│   ├── schemas.py      # Structured output schemas
│   └── streaming.py    # Streaming helpers
├── stt/                # Speech-to-text (FPT Whisper)
├── tts/                # Text-to-speech (FPT VITs)
└── config/             # Settings (LLM, Graph, Auth)
```
