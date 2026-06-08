# Agentic AI v3.0 — ERP Chat Agent

Harness-orchestrated planner-brain architecture with execution tier fast-path templates, observation contracts, and K15 outcome tracking.

## Quick Start

### Prerequisites
- Python 3.12+
- `.env` file with LLM/Spring/JWT config (see `.env.example`)

### Run Locally

```bash
# 1. Activate venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate  # Windows

# 2. Start the app
uvicorn main:app --reload --port 8000

# 3. Test a request
curl -X POST http://localhost:8000/api/v1/ai/chat/stream \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>" \
  -H "X-Correlation-Id: test-1" \
  -d '{
    "message": "doanh thu tháng này",
    "metadata": {
      "user_id": "user1",
      "tenant_id": "tenant1",
      "thread_id": "thread-1"
    }
  }'
```

Expected: SSE stream with `event: delta` messages and final `event: done`.

## Architecture

### Agentic AI v3.0 (SRS-006)

- **Planner-Brain**: LLM-backed decision component (`harness_planner` role) that chooses tools, builds plans, and replans.
- **Harness Execution**: Safety boundary enforcing policy, RBAC, budget, HITL, validation.
- **Observation Contract**: Bounded, sanitized view of tool results (schema + counts + sample, never full data).
- **Result References**: Full data held by Harness behind opaque `result_ref` handles; only sample shown to Planner.
- **Plan Templates**: High-confidence plans auto-promoted after N clean successes; fast-path skips planner LLM on repeat intents.
- **K15 History**: Privacy-safe outcome tracking (hashed tenant/intent, never raw SQL) with distinct statuses: success, degraded, failure, hitl_pending, clarify_pending.

### Configuration

Master switch: `AGENTIC_V3_ENABLED` (default: `1`)

Setting | Default | Purpose
---|---|---
`AGENTIC_V3_ENABLED` | `1` | Master switch: cascades 8 dependent flags (harness loop, intent object, plan DAG, answer composer, validator, capability guard, async, templates).
`AGENTIC_V3_PLAN_TEMPLATE_ENABLED` | `1` | Runtime template promotion (Slice D/OQ-6).
`AGENTIC_V3_TEMPLATE_PROMOTE_AFTER` | `3` | Clean successes before a plan is promoted to fast-path template.
`AGENTIC_V3_MEASURED_ROUTE_ACCURACY` | `0.0` | K12 eval accuracy (measured by CI). Promotion blocked until >= threshold (FR-11.7).
`AGENTIC_V3_ROUTE_ACCURACY_THRESHOLD` | `0.8` | Required K12 accuracy before v3 rollout.

### Rollback to Legacy

Set `AGENTIC_V3_ENABLED=0` in `.env` → full fallback to legacy linear graph (no harness loop, no planner).

## Testing

```bash
# Full test suite (587 tests)
pytest tests -q

# Specific test file
pytest tests/test_v3_artifact_tools.py -q

# Watch mode
pytest tests -q --tb=short --looponfail
```

## Key Features (v3)

✅ **Dependency Gating (P1-1)**: Draft/write tools never run after failed lookup.  
✅ **Empty Results (P2-1)**: "No data found" list/table returns valid 0-row artifact, not degraded.  
✅ **Failure Labeling (P1-3)**: Internal plan errors recorded as degraded, not clean success.  
✅ **K12 Eval Gate (P1-2)**: Template promotion blocked until measured route accuracy ≥ threshold.  
✅ **RBAC Scope (P2-2)**: Template lookup isolated by role + live permission fingerprint, preventing cross-user poisoning.  
✅ **Clarify State (P1-4)**: Durable clarification records carry in-flight plan state; resume never replays side-effect nodes.  

## Environment Variables

### LLM (Required)
```
LLM_MODEL=gpt-4o-mini  # or Qwen, Claude, etc.
LLM_BASE_URL=http://...
LLM_API_KEY=sk-...
LLM_STRUCTURED_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.0
LLM_STREAMING_DEFAULT=true
```

### Spring SQL Backend (Required)
```
SPRING_SQL_URL=http://localhost:8089/api/v1/sql/execute
```

### JWT Authentication (Required unless AUTH_DEV_BYPASS=1)
```
JWT_HS256_SECRET=your-secret-key
JWT_ISSUER=your-issuer
JWT_AUDIENCE=your-audience
AUTH_DEV_BYPASS=0
```

### Agentic AI v3 (Optional)
```
AGENTIC_V3_ENABLED=1
AGENTIC_V3_PLAN_TEMPLATE_ENABLED=1
AGENTIC_V3_TEMPLATE_PROMOTE_AFTER=3
AGENTIC_V3_MEASURED_ROUTE_ACCURACY=0.0  # Update via CI after K12 eval
AGENTIC_V3_ROUTE_ACCURACY_THRESHOLD=0.8
```

## Operational Notes

### First Run with Live LLM + Spring

1. Ensure LLM endpoint is reachable and API key is valid.
2. Ensure Spring SQL endpoint is running and JWT secret matches.
3. Send a test query with a valid JWT token (or use `AUTH_DEV_BYPASS=1` for dev).
4. Monitor SSE output for `delta` events and final `done`.

### Enabling Fast-Path Templates

1. Run K12 route-accuracy eval (requires eval fixtures).
2. Write the measured accuracy to `AGENTIC_V3_MEASURED_ROUTE_ACCURACY` (e.g., `0.92`).
3. Restart the app.
4. Now plan templates will auto-promote after `AGENTIC_V3_TEMPLATE_PROMOTE_AFTER` clean successes.

### Monitoring

- **Traces**: All turns logged with `correlation_id`, tool counts, replan counts, latency, cost.
- **K15 History**: Query intent history with `summary(intent_key)` → success/degraded/failure/hitl_pending/clarify_pending counts.
- **Plan Templates**: Inspect promoted templates in memory/SQLite store (live accuracy, success/degraded/failure counts per template).

## Architecture Diagram

```
User Query
    ↓
[Harness Runtime] ← async/budget/timeout/cache
    ↓
[Intent Analysis] (LLM: intent_role)
    ↓
[Tier Decision] → Known template? → [Template Fast-Path] (skip planner LLM)
    ↓                                      ↓
    No template → [Planner LLM]      [Execute Plan]
       ↓               ↓                   ↓
    [Plan] → [PlanExecutor] ← Harness gates (policy/RBAC/budget)
       ↓               ↓
    [Tool Call] → [Observation] (bounded sample, result_ref handle)
       ↓               ↓
    [Planner Decision] (replan/clarify/degrade/stop)
       ↓
    [K15 Record] (outcome: success/degraded/failure/hitl_pending/clarify_pending)
       ↓
    [SSE Stream] → Frontend (delta/data_table/chart/draft/clarify/done)
```

## Files

| File | Purpose |
|---|---|
| `main.py` | ASGI app entry; FastAPI router setup. |
| `app/harness/plan_graph.py` | Plan DAG executor; dependency gating; replan loop. |
| `app/harness/observation.py` | Observation contract; sanitization; result_ref creation. |
| `app/harness/orchestrator.py` | Harness orchestrator; tier decision; K15 recording. |
| `app/harness/plan_template_store.py` | Plan template promotion logic; version pinning. |
| `app/harness/history_store.py` | K15 intent history; outcome tracking (privacy hashed). |
| `app/harness/eval_gate.py` | K12 route-accuracy evaluation; rollout gate. |
| `app/api/runtime.py` | API layer; clarify/HITL state; SSE streaming. |
| `app/graph/tools/*.py` | Tool implementations (sql_query, chart_builder, data_table_builder, etc.). |

## Changelog

### v3.0 (SRS-006)
- Planner-brain architecture with harness execution boundary.
- Observation contract with result_ref data-flow.
- Plan template auto-promotion (runtime FR-11.3/11.7).
- K15 privacy-hashed outcome history.
- K12 route-accuracy eval gate.
- Dependency gating (P1-1), empty-result flow (P2-1), failure labeling (P1-3), RBAC scope isolation (P2-2), clarify durable state (P1-4).

---

**Status**: Production-ready (587 tests, 2 skipped).  
**Default Mode**: Agentic v3 enabled. Use `AGENTIC_V3_ENABLED=0` to rollback to legacy.
