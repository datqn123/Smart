# Agentic AI Architecture — ai-python

> Phân tích toàn bộ hệ thống agentic runtime: harness orchestration, plan DAG, tools, intent classification, policy, và v3 planner-brain upgrade

---

## Tổng quan kiến trúc

Hệ thống sử dụng **Strangler Pattern**: `LangHarnessRuntime.stream()` quyết định routing dựa trên intent:

```
User → API Runtime
         │
         ├─ HarnessOrchestrator (khi harness_loop_enabled=True)
         │     ├─ IntentSubagent → phân tích intent
         │     ├─ Reactive Loop (call_tool/clarify/final_answer)
         │     ├─ Plan DAG (PlannerSubagent → PlanExecutor)
         │     └─ ToolRegistry → 10 tools
         │
         └─ LangGraphRuntime (legacy fallback)
               ├─ domain_guard → context_compact → agent_planner
               └─ classify_intent → chat/sql/chart/catalog/inventory
```

| Layer | Thành phần | Vai trò |
|-------|-----------|---------|
| **API** | `routes.py` → `runtime.py` | Nhận request, chọn runtime path, SSE streaming |
| **Harness** | `orchestrator.py` | Vòng lặp agentic chính: decide → execute → observe → loop |
| **Intent** | `intent.py` | IntentSubagent: classify, entity resolution, clarify detection |
| **Plan** | `plan_graph.py` | PlannerSubagent + PlanExecutor: DAG generation & execution |
| **Tools** | `tool_registry.py` | 10 tools: sql_query, schema_explore, catalog_draft, inventory_draft, data_validator, answer_composer, build_chart, data_table_builder, erp_guide |
| **Policy** | `policy.py` | 5-layer check: capability → RBAC → role → tenant → SQL guard |
| **LLM** | `app/llm/` | 16+ roles (harness_planner, planner, intent, sql_gen, chat, ...) |
| **Legacy** | `main_graph.py` | 15-node StateGraph: domain_guard, context_compact, planner, intent, chart pipeline, SQL subgraph, draft subgraphs |

---

## 5 Execution Modes

### 1. Reactive Loop (Default)
- `harness_loop_enabled=True`
- LLM decides next action step-by-step: `call_tool`, `clarify`, `final_answer`
- Tool executes → observation stored → loop repeats (max 6 steps)
- Budget enforcement: tokens, cost, wallclock (30s)
- Duplicate tool call detection

### 2. Plan DAG (P2)
- `agentic_plan_dag_enabled=False` (off by default)
- IntentSubagent classifies → PlannerSubagent generates PlanGraph DAG
- PlanExecutor executes parallel nodes, data-flow via `${node_id.field}` refs
- On failure: replan via PlannerSubagent

### 3. Clarify
- Hai đường dẫn: IntentSubagent detect ambiguity, hoặc reactive loop decide clarify
- Gửi ClarifyEvent với questions + suggested rewrite
- User respond → loop resume

### 4. HITL (Safety)
- Cho catalog_draft & inventory_draft (`has_hitl=True`, `non_idempotent_write`)
- Tool produce draft + HitlSpec → frontend confirm UI
- User confirm → `_resume_hitl()` commit qua Spring
- State persisted trong PendingHitlStore (in-memory/SQLite)

### 5. Legacy LangGraph (Fallback)
- `harness_loop_enabled=False`
- Pure StateGraph: 15 nodes, conditional edges
- domain_guard → context_compact → agent_planner → classify_intent
- Subgraphs: sql, catalog_draft, inventory_draft

---

## 10 Tools trong Registry

| Tool | Capability | Side Effect | HITL | Mô tả |
|------|-----------|-------------|------|-------|
| `sql_query` | data_read | read_only | ✗ | Đọc ERP data, self-correcting SQL pipeline |
| `schema_explore` | data_read | read_only | ✗ | Khám phá DB schema, tables, columns |
| `catalog_draft` | draft_create | non_idempotent_write | ✓ | Tạo catalog/product/category draft |
| `inventory_draft` | draft_create | non_idempotent_write | ✓ | Tạo inventory receipt/dispatch draft |
| `data_validator` | data_validate | read_only | ✗ | Validate business constraints |
| `answer_composer` | answer_compose | read_only | ✗ | Soạn answer tiếng Việt từ observations |
| `build_chart` | chart_build | read_only | ✗ | Build Recharts payload (line/bar/pie) |
| `data_table_builder` | data_table_build | read_only | ✗ | Build frontend data-table SSE artifact |
| `erp_guide` | erp_guide | read_only | ✗ | ERP domain guidance |

---

## Agentic Feature Flags

| Flag | Default | Mô tả |
|------|---------|-------|
| `harness_loop_enabled` | ❌ False | Strangler route ON/OFF |
| `agentic_intent_object_enabled` | ❌ False | IntentSubagent analysis |
| `agentic_plan_dag_enabled` | ❌ False | PlanGraph DAG execution |
| `agentic_answer_composer_enabled` | ❌ False | AnswerComposer tool |
| `agentic_data_validator_enabled` | ❌ False | Data Validator tool |
| `agentic_capability_guard_enabled` | ❌ False | RBAC guard extensions |
| `agentic_model_routing_enabled` | ❌ False | Tiered model routing |
| `agentic_semantic_cache_enabled` | ❌ False | Semantic tool cache |
| `agentic_trace_enabled` | ✅ True | Trace recording |
| `agentic_async_enabled` | ❌ False | Native async harness |
| `agentic_v3_enabled` | ❌ False | Master v3 (cascade: loop + plan_dag + intent + ...) |

V3 cascade khi bật: tự động bật harness_loop, plan_dag, intent_object, answer_composer, data_validator, capability_guard, async, plan_template.

---

## Subagents & LLM

### IntentSubagent (`harness/intent.py`)
- Structured LLM output → IntentAnalysisResult
- Entity resolution qua SequenceMatcher + synonym map + catalog
- Heuristic fallback khi LLM unavailable
- Confidence thresholds: run=0.9, hitl=0.75, entity_score=0.6

### PlannerSubagent (`harness/plan_graph.py`)
- Generate PlanGraph DAG từ intent
- Replan: generate revised plan sau failure
- LLM `astructured_predict` với schema mẫu

### LLM Roles (16+)
| Role | Mục đích | Tier mặc định |
|------|---------|---------------|
| `harness_planner` | Next-action decision | sonnet |
| `planner` | Plan graph generation | sonnet |
| `intent` | Intent classification | haiku |
| `sql_gen` | SQL generation | sonnet |
| `sql_review` | SQL review | sonnet |
| `chat` | General conversation | primary |
| `domain_guard` | ERP scope check | haiku |
| `catalog_draft` | Catalog draft gen | sonnet |
| `inventory_draft` | Inventory draft gen | sonnet |

---

## Policy (5-Layer Check)

1. **Capability mapping**: tool → data_read / draft_create / artifact_build / chat
2. **RBAC permission**: JWT permissions vs tool's `rbac_required`
3. **CapabilityMatrix**: owner=all, staff=data_read+chat only
4. **Tenant isolation**: `args.tenant_id` == `ctx.tenant_id`
5. **SQL guardrails**: keyword deny (DELETE, UPDATE, INSERT, DROP, ...) + multi-stmt block

**Sensitive column masking**: non-owner role strips cost_price, margin, debt_balance, finance_ledger.

---

## V3 Planner-Brain Upgrade (Upcoming)

| Slice | Component | Mô tả |
|-------|-----------|-------|
| A | Rich Manifest | capability, produces/consumes, side_effect_class, result_ref_policy |
| B | Observation Envelope | Masked samples, opaque result_ref, tenant-scoped |
| C | Planner-Owned Replan | Harness emit replan_required, Planner decide |
| D | Plan Templates | Fast-path, version-pinned, auto-promote/demote |
| E | Artifact Tools | chart_builder, data_table_builder consume result_ref |
| F | Clarify Durable | Survive restarts, no replay of side-effect nodes |
| G | K12/K15 Eval | Route accuracy threshold, outcome weighting |

Tất cả feature flags v3 hiện đang `False`. Cần implement + bật dần theo eval gate.

---

## Data Flow: User → Final Response

```
User → API Runtime → HarnessOrchestrator.stream()
  ├─ HITL resume check → _resume_hitl() nếu pending
  ├─ Budget init (steps=6, tokens=0, cost=$0.05, wallclock=30s)
  ├─ [P1] IntentSubagent.analyze()
  │    ├─ clarify → ClarifyEvent → STOP
  │    └─ run → continue
  ├─ [P2] Plan DAG mode (nếu enabled + data_query/chart_report)
  │    └─ _run_plan_mode() → PlannerSubagent → PlanGraph → PlanExecutor
  ├─ Reactive loop (nếu không plan mode):
  │    for step in max_steps:
  │      a. LLM decide (call_tool/clarify/final_answer)
  │      b. Policy check
  │      c. Tool invoke (subgraph call nếu SQL/draft)
  │      d. Observation stored
  │      e. Budget checkpoint
  └─ FinalAnswerEvent → SSE → User
```

---

## Key Observations

1. **Strangler pattern** — Harness đang dần thay thế legacy LangGraph, nhưng hầu hết flags đang `False`
2. **Intent routing** — 2 hệ thống song song (legacy LangGraph node + Harness IntentSubagent)
3. **Safety-first** — HITL cho draft, policy 5-layer, column masking, tenant isolation
4. **Chưa bật** — tất cả agentic P-series flags đang off, cần implement + eval trước khi rollout
5. **V3 scope** — lớn: 7 slices, nhiều file mới (observation.py, result_store.py, history_store.py, plan_template_store.py, clarify_store.py)
