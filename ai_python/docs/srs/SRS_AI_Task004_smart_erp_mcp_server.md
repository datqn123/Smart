# SRS_AI_Task004_smart_erp_mcp_server

| Field | Value |
| :--- | :--- |
| **Task ID** | Task004 |
| **Slug** | `smart_erp_mcp_server` |
| **PRD** | [`../prd/PRD_Task004_smart_erp_mcp_server.md`](../prd/PRD_Task004_smart_erp_mcp_server.md) |
| **ADR** | [`../adr/ADR-002-smart_erp_mcp_server.md`](../adr/ADR-002-smart_erp_mcp_server.md) |
| **Plan** | [`../plan/PLAN_Smart_ERP_MCP_server_v1.md`](../plan/PLAN_Smart_ERP_MCP_server_v1.md) |

---

## 1. Scope

- **In scope**: MCP server process **`smart-erp-ai`** (FastMCP stdio) under `ai_python/app/smart_erp_mcp/`; tool contracts; `sqlglot` validation; demo **in-memory SQLite** execution; stubs for RAG/write; docs + bridge table + runbook.
- **Out of scope**: `backend/`, `frontend/` changes; production wiring to Spring; real vector index.

---

## 2. Roles & surfaces

| Role | Surface | Notes |
| :--- | :--- | :--- |
| Intent | `intent_analyze` | No DB I/O. |
| RAG Reader | `rag_retrieve` | Stub chunks (deterministic), not live ERP truth. |
| Live read | `read_catalog_snapshot`, `sql_execute_read` | Catalog + validated SELECT on demo SQLite. |
| UI | `ui_build_form_spec`, `ui_build_table_spec` | JSON specs for FE (contract only). |
| Viz | `viz_build_chart_spec` | Spec from aggregate input. |
| Write (single) | `write_commit` | Stub; requires HITL + idempotency fields. |

---

## 3. Standard errors

| Code | When |
| :--- | :--- |
| `VALIDATION_FAILED` | SQL/table/rule violations |
| `FORBIDDEN` | Policy deny (e.g. write without token) |
| `SCOPE_VIOLATION` | Path/table outside allowlist |

Handlers return `{"ok": false, "error": {"code": "...", "message": "..."}}`.

---

## 4. Tool I/O (summary)

### 4.1 `intent_analyze`

- **In**: `user_text: str`, optional `session_id: str`
- **Out**: `{ ok, primary_intent, entities, risk_flags, hitl_required, suggested_tools }`

`primary_intent` enum: `conversation` | `rag_qa` | `data_query` | `visualization` | `transactional_update` | `help` | `refusal`

### 4.2 `rag_retrieve`

- **In**: `query: str`, `top_k: int = 5`
- **Out**: `{ ok, chunks: [{id, text, source, score}], rag_stale_warning }`

### 4.3 `read_catalog_snapshot`

- **In**: none
- **Out**: `{ ok, data_as_of, tables: {name: {columns: [...]}} }`

### 4.4 `sql_propose_select`

- **In**: `draft_sql: str`, optional `rag_table_hints: list[str]`
- **Out**: `{ ok, normalized_sql, merged_tables, warnings[] }` or error

Merges hints for observability only; **grounding** = allowlist from catalog.

### 4.5 `sql_execute_read`

- **In**: `sql: str`
- **Out**: `{ ok, columns, rows, row_count, data_as_of }` or error

### 4.6 `ui_build_form_spec` / `ui_build_table_spec`

- **In**: title + fields/rows (see implementation types)
- **Out**: `{ ok, spec: object }`

### 4.7 `viz_build_chart_spec`

- **In**: `chart_type`, `series: {name: list[float]}` , `labels: list[str]`
- **Out**: `{ ok, spec: object }`

### 4.8 `write_commit`

- **In**: `proposal_id`, `hitl_token`, `idempotency_key`, `payload_json` (string)
- **Out**: `{ ok, status }` stub

---

## 5. SSE / Chat

Not in this slice (MCP stdio only). No change to Task003 SSE envelope required for minimal path.

---

## 6. Eval prompts (seed ≥ 5)

| ID | Intent |
| :--- | :--- |
| #E1 | benign `SELECT qty FROM products WHERE id=1` |
| #E2 | multi-statement `SELECT 1; SELECT 2` → reject |
| #E3 | `DROP TABLE products` → reject |
| #E4 | `SELECT * FROM secret_table` → reject (not allowlisted) |
| #E5 | transactional Vietnamese phrase → `hitl_required=true` |

Expand to ≥30 in Eval task folder later.

---

## 7. Acceptance criteria

| ID | Criterion |
| :--- | :--- |
| AC-1 | `python -m app.smart_erp_mcp` imports and exposes listed tools (FastMCP). |
| AC-2 | `sql_execute_read` rejects non-SELECT / multi-statement / off-allowlist tables (tests). |
| AC-3 | `intent_analyze` returns stable keys; transactional phrases set `hitl_required`. |
| AC-4 | `write_commit` rejects short token / missing idempotency. |
| AC-5 | Logging helper never emits full `hitl_token` body (unit assertion or code inspection checklist in CR). |

---

## 8. Observability

- Structured log: `tool`, `duration_ms`, `correlation_id` (optional input later); redact secrets.

---

## 9. MCP_PHASE

`N/A` (server is host, not Phase 0 client profile).

---

## 10. Runbook

See [`../task004/RUNBOOK_MCP.md`](../task004/RUNBOOK_MCP.md).
