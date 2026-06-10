# Harness & Legacy Logging Enhancement — Design Spec

**Date**: 2026-06-10  
**Status**: Draft  
**Scope**: Add comprehensive debug logging to harness system, tool implementations, and legacy LangGraph components.

---

## 1. Goals

- **Harness system**: Add `logger.info/warning` to all components that currently lack logging (6 files with zero logs, 3 files with sparse logs)
- **Tool implementations**: Add invoke start/end timing logs to all 9 harness-registered tools
- **Legacy LangGraph**: Add logs to components that are actively used but have no logging (main_graph, sql_subgraph, routes)
- **Pattern**: Direct `logger = logging.getLogger(__name__)` with `key=value` format. No new abstraction. Follow existing patterns.

## 2. Non-Goals

- Not creating a new logging wrapper/abstraction
- Not changing existing log calls (only adding new ones)
- Not adding log aggregation, metrics pipelines, or structured JSON logging
- Not instrumenting legacy graph node internals (already have `emit_agent_trace`)

## 3. Architecture

### Logging infrastructure (already exists, no changes)

```
All log records → CorrelationFilter (injects correlation_id from contextvars)
                → stderr StreamHandler on "app" logger (format: "LEVEL name: message")
```

- `CorrelationFilter` already attached to root handlers via `setup_correlation_logging()`
- `app` logger already set to INFO level via `setup_app_package_stderr_logging()`
- Correlation ID set from `X-Correlation-Id` header in `routes.py`

### Log format convention

```python
logger.info("event_name key1=%s key2=%s", val1, val2)
logger.warning("event_name key1=%s error=%s", val1, err)
```

- **event_name**: snake_case, describes the action (e.g. `harness_turn_start`, `plan_exec_node_end`)
- **Level INFO**: Normal lifecycle events (turn start/end, tool invoke, decision)
- **Level WARNING**: Recoverable errors, fallbacks, guardrail triggers
- **Level DEBUG**: Internal detail (cache lookup, version check) — existing DEBUG calls unchanged
- **Privacy**: No raw SQL, PII, tokens, secrets. Messages preview truncated at 120 chars.

---

## 4. Detailed Changes

### 4.1 Harness Core

#### 4.1.1 `app/harness/orchestrator.py`

| # | Location | Level | Event | Keys |
|---|----------|-------|-------|------|
| 1 | `run()` entry | INFO | `harness_turn_start` | `correlation_id`, `thread_id`, `message_preview` |
| 2 | `run()` exit | INFO | `harness_turn_end` | `status`, `steps`, `latency_ms`, `replans`, `hitl` |
| 3 | `_dispatch()` entry | INFO | `harness_dispatch` | `mode` (reactive/plan/template/HITL), `intent` |
| 4 | `_decide()` each step | INFO | `harness_step` | `step`, `max_steps`, `action`, `tool`, `confidence` |
| 5 | Tool start | INFO | `harness_tool_start` | `tool`, `step` |
| 6 | Tool end | INFO | `harness_tool_end` | `tool`, `ok`, `latency_ms`, `rows`, `has_sse` |
| 7 | Template lookup | INFO | `harness_template_lookup` | `intent`, `found`, `demoted`, `versions_ok` |
| 8 | Policy check pass | INFO | `harness_policy_check` | `tool`, `role`, `decision=allow` |
| 9 | Replan | INFO | `harness_replan` | `attempt`, `max`, `failing_nodes`, `nodes_count` |
| 10 | Replan stop | WARNING | `harness_replan_stop` | `reason`, `attempt` |
| 11 | SSE emit | INFO | `harness_sse_emit` | `event`, `payload_keys` |
| 12 | Memory save | INFO | `harness_memory_save` | `thread`, `turn`, `tools` |

> Existing warnings (LLM decision fail, tool fail, turn metrics) in this file are unchanged.

#### 4.1.2 `app/harness/plan_graph.py`

| # | Location | Level | Event | Keys |
|---|----------|-------|-------|------|
| 1 | `PlannerSubagent.plan()` | INFO | `planner_generated` | `nodes`, `confidence` |
| 2 | `execute()` layer start | INFO | `plan_exec_layer_start` | `layer`, `nodes` |
| 3 | Node start | INFO | `plan_exec_node_start` | `node`, `tool` |
| 4 | Node end | INFO | `plan_exec_node_end` | `node`, `ok`, `meets_expect`, `latency_ms` |
| 5 | Dep blocked | WARNING | `plan_dep_blocked` | `node`, `blocked_by` |
| 6 | Cycle detected | WARNING | `plan_cycle_detected` | `remaining_nodes` |
| 7 | Ref unresolved | WARNING | `plan_ref_unresolved` | `ref`, `node` |
| 8 | Observation built | INFO | `plan_observation_built` | `tool`, `rows`, `truncated`, `masked` |
| 9 | v3 plan start | INFO | `v3_plan_start` | `session_id`, `nodes` |
| 10 | v3 replan | INFO | `v3_plan_replan` | `attempt`, `max`, `observations` |
| 11 | v3 fingerprint duplicate | WARNING | `v3_plan_fingerprint_duplicate` | `fingerprints` |
| 12 | v3 nonidempotent blocked | WARNING | `v3_plan_nonidempotent_blocked` | `node` |

### 4.2 Harness Stores

#### 4.2.1 `app/harness/plan_template_store.py`

| # | Location | Level | Event | Keys |
|---|----------|-------|-------|------|
| 1 | Store init | INFO | `template_store_init` | `backend` (memory/sqlite) |
| 2 | Template promoted | INFO | `template_promoted` | `intent`, `plan_hash`, `role`, `after_successes` |
| 3 | Promotion blocked (K12) | INFO | `template_promotion_blocked` | `accuracy`, `threshold` |
| 4 | Lookup result | INFO | `template_lookup` | `intent`, `found`, `demoted`, `versions_ok`, `stored_versions` |
| 5 | Streak update | INFO | `template_candidate_streak` | `intent`, `plan_hash`, `success_count`, `needed` |
| 6 | Streak broken | WARNING | `template_streak_broken` | `intent`, `status`, `counts` |
| 7 | Template demoted | WARNING | `template_demoted` | `intent`, `status`, `counts` |

#### 4.2.2 `app/harness/history_store.py`

| # | Location | Level | Event | Keys |
|---|----------|-------|-------|------|
| 1 | Event append | INFO | `k15_event_append` | `intent_hash`, `status`, `tools`, `replan`, `hitl` |
| 2 | Summary retrieval | INFO | `k15_summary` | `intent`, `total`, `success`, `degraded`, `failure`, `hitl`, `clarify` |

#### 4.2.3 `app/harness/memory_store.py`

| # | Location | Level | Event | Keys |
|---|----------|-------|-------|------|
| 1 | Turn append | INFO | `conv_memory_append` | `thread`, `turn`, `intent`, `tools` |
| 2 | Compaction | INFO | `conv_memory_compact` | `thread`, `deleted`, `kept` |
| 3 | Context retrieve | INFO | `conv_memory_retrieve` | `thread`, `turns`, `has_summary` |
| 4 | Thread delete | INFO | `conv_memory_delete` | `thread`, `turns_removed` |

#### 4.2.4 `app/harness/eval_gate.py`

| # | Location | Level | Event | Keys |
|---|----------|-------|-------|------|
| 1 | Case result | INFO | `eval_case` | `case`, `passed`, `missing`, `forbidden` |
| 2 | Accuracy | INFO | `eval_accuracy` | `accuracy`, `total`, `passed` |
| 3 | Rollout decision | INFO | `eval_rollout` | `allowed`, `accuracy`, `threshold` |

### 4.3 Harness Infrastructure

#### 4.3.1 `app/harness/observation.py`

| # | Location | Level | Event | Keys |
|---|----------|-------|-------|------|
| 1 | Envelope built | INFO | `observation_built` | `tool`, `ok`, `rows`, `truncated`, `masked`, `ref` |
| 2 | Error envelope | WARNING | `observation_error` | `tool`, `kind`, `fingerprint` |

#### 4.3.2 `app/harness/tool_registry.py`

| # | Location | Level | Event | Keys |
|---|----------|-------|-------|------|
| 1 | Tool registered | INFO | `tool_registered` | `name`, `hitl`, `capability`, `side_effect` |
| 2 | Version computed | INFO | `tool_manifest_version` | `hash`, `tool_count` |

#### 4.3.3 `app/harness/budget.py`

| # | Location | Level | Event | Keys |
|---|----------|-------|-------|------|
| 1 | Budget exceeded | WARNING | `budget_exceeded` | `kind`, `used`, `limit`, `step` |

#### 4.3.4 `app/harness/cache.py`

| # | Location | Level | Event | Keys |
|---|----------|-------|-------|------|
| 1 | Cache access | INFO | `harness_cache` | `hit`, `tool`, `key` |

#### 4.3.5 `app/harness/runtime.py`

| # | Location | Level | Event | Keys |
|---|----------|-------|-------|------|
| 1 | Tool call timing | INFO | `harness_tool_call` | `tool`, `latency_ms`, `ok` |

### 4.4 Tool Implementations (`app/graph/tools/`)

Each tool gets 2 log points: one at `invoke()` start, one at `invoke()` end.

| Tool file | Start keys | End keys |
|-----------|-----------|----------|
| `sql_query.py` | `tool=sql_query`, `query_preview` | `tool=sql_query`, `ok`, `latency_ms`, `rows`, `sql_hash`, `has_sse` |
| `schema_explore.py` | `tool=schema_explore`, `topic` | `tool=schema_explore`, `ok`, `latency_ms`, `tables` |
| `catalog_draft.py` | `tool=catalog_draft`, `request_preview` | `tool=catalog_draft`, `ok`, `latency_ms`, `has_hitl`, `has_sse` |
| `inventory_draft.py` | `tool=inventory_draft`, `request_preview` | `tool=inventory_draft`, `ok`, `latency_ms`, `has_hitl`, `has_sse` |
| `answer_composer.py` | `tool=answer_composer`, `observations_count` | `tool=answer_composer`, `ok`, `latency_ms`, `answer_chars` |
| `build_chart.py` | `tool=build_chart`, `rows` | `tool=build_chart`, `ok`, `latency_ms`, `chart_type` |
| `data_table_builder.py` | `tool=data_table_builder`, `rows`, `title` | `tool=data_table_builder`, `ok`, `latency_ms`, `row_count` |
| `data_validator.py` | `tool=data_validator`, `rows`, `required` | `tool=data_validator`, `ok`, `issues` |
| `erp_guide.py` | `tool=erp_guide`, `topic` | `tool=erp_guide`, `ok`, `latency_ms`, `guidance_chars` |

All events prefixed with `tool_invoke_start` / `tool_invoke_end`.

### 4.5 Legacy System

#### 4.5.1 `app/graph/main_graph.py`

| # | Location | Level | Event | Keys |
|---|----------|-------|-------|------|
| 1 | Graph compiled | INFO | `graph_compile` | `nodes`, `checkpointer` |
| 2 | Each route function | INFO | `graph_route` | `from`, `to`, `reason` |

#### 4.5.2 `app/graph/sql_subgraph.py`

| # | Location | Level | Event | Keys |
|---|----------|-------|-------|------|
| 1 | SQL attempt counter | INFO | `sql_attempt` | `attempt`, `max` |
| 2 | Each route function | INFO | `sql_route` | `from`, `to`, `reason` |
| 3 | Empty result verdict | INFO | `sql_empty_verdict` | `verdict`, `reason` |

#### 4.5.3 `app/api/routes.py`

| # | Location | Level | Event | Keys |
|---|----------|-------|-------|------|
| 1 | Stream start | INFO | `sse_stream_start` | `correlation_id`, `thread_id` |
| 2 | Stream end | INFO | `sse_stream_end` | `chunks`, `duration_ms`, `had_error` |
| 3 | First delta | INFO | `sse_first_delta` | `ttfb_ms` |

---

## 5. Files Summary

| File | Current logs | New logs | Logger already exists? |
|------|-------------|----------|----------------------|
| `app/harness/orchestrator.py` | ~8 | ~10 | Yes |
| `app/harness/plan_graph.py` | 0 | ~12 | No — add `logging.getLogger(__name__)` |
| `app/harness/plan_template_store.py` | 0 | ~7 | No — add `logging.getLogger(__name__)` |
| `app/harness/history_store.py` | 0 | ~2 | No — add `logging.getLogger(__name__)` |
| `app/harness/memory_store.py` | 0 | ~4 | No — add `logging.getLogger(__name__)` |
| `app/harness/eval_gate.py` | 0 | ~3 | No — add `logging.getLogger(__name__)` |
| `app/harness/observation.py` | 0 | ~2 | No — add `logging.getLogger(__name__)` |
| `app/harness/tool_registry.py` | 0 | ~2 | No — add `logging.getLogger(__name__)` |
| `app/harness/budget.py` | 0 | ~1 | No — add `logging.getLogger(__name__)` |
| `app/harness/cache.py` | 0 | ~1 | No — add `logging.getLogger(__name__)` |
| `app/harness/runtime.py` | ~2 | ~1 | Yes |
| `app/graph/tools/sql_query.py` | ~3 | ~2 | Yes |
| `app/graph/tools/schema_explore.py` | 0 | ~2 | No — add |
| `app/graph/tools/catalog_draft.py` | 0 | ~2 | No — add |
| `app/graph/tools/inventory_draft.py` | 0 | ~2 | No — add |
| `app/graph/tools/answer_composer.py` | 0 | ~2 | No — add |
| `app/graph/tools/build_chart.py` | 0 | ~2 | No — add |
| `app/graph/tools/data_table_builder.py` | 0 | ~2 | No — add |
| `app/graph/tools/data_validator.py` | 0 | ~2 | No — add |
| `app/graph/tools/erp_guide.py` | 0 | ~2 | No — add |
| `app/graph/main_graph.py` | 0 | ~5 | No — add `logging.getLogger(__name__)` |
| `app/graph/sql_subgraph.py` | 0 | ~8 | No — add `logging.getLogger(__name__)` |
| `app/api/routes.py` | ~2 | ~3 | Yes |

**Total**: ~110 new log points across 23 files (10 files add `logging.getLogger(__name__)` for the first time).

---

## 6. Testing Strategy

- Existing test suite (587 tests) must continue to pass
- No new test framework or dependency required
- Log output is visible in pytest via caplog — existing tests that assert against caplog may need updating if they match specific log messages
- Manual verification: run `uvicorn main:app` and send a test request, confirm structured logs appear on stderr

---

## 7. Risk & Mitigation

| Risk | Mitigation |
|------|-----------|
| Log volume too high in production | All new logs at INFO level; can be suppressed by setting `LOG_LEVEL=WARNING` in production |
| Performance impact from string formatting | Python logging uses lazy % formatting — no cost when level is suppressed |
| Breaking existing tests that match log output | Only ADDING log calls, never removing or changing existing ones. Grep tests for `caplog` assertions before changes |
| Privacy leak from message preview | All user message previews truncated to 120 chars; no SQL/entities logged raw |

---

## 8. Rollout

1. Add `logging.getLogger(__name__)` import to 10 files that lack it
2. Add log calls to each file in order: stores → infra → core → tools → legacy
3. Run full test suite after each file group
4. Final manual smoke test with live LLM + Spring SQL
