# PRD — Task004 — Smart ERP MCP server (`smart-erp-ai`) v1

| Field | Value |
| :--- | :--- |
| **Task** | Task004 |
| **Slug** | `smart_erp_mcp_server` |
| **Plan** | [`../plan/PLAN_Smart_ERP_MCP_server_v1.md`](../plan/PLAN_Smart_ERP_MCP_server_v1.md) |
| **Scope** | `ai_python/` only |

## 1. Overview

Deliver an MCP server **`smart-erp-ai`** exposing tools for **intent routing**, **RAG-style retrieval (stub)**, **live catalog snapshot**, **constrained SELECT** (`sqlglot` validate + in-memory SQLite demo execute), **UI form/table specs**, **chart spec**, and a **single write entrypoint (stub)** with HITL/idempotency fields — aligned with `PLAN_Smart_ERP_MCP_server_v1.md` (hybrid RAG + live read; no free-text write).

## 2. Options (HITL — Owner)

- **A — Demo execution only (chosen for v1)**: `sql.execute_read` runs only on **in-memory SQLite** with seeded allowlisted tables after validation. No raw SQL forwarded to Task003 `db-readonly` templates in this slice.
- **B — Bridge to `db-readonly` templates**: Map validated intent to `template_id + params` only; no arbitrary SELECT strings.
- **C — HTTP Spring read/write**: Out of `ai_python/` scope for this task; handoff.

**Recommendation**: **A** for implementable slice under orchestrate rules; document bridge path in ADR-002.

## 3. Functional requirements

1. **Tools registered** (FastMCP): `intent_analyze`, `rag_retrieve`, `read_catalog_snapshot`, `sql_propose_select`, `sql_execute_read`, `ui_build_form_spec`, `ui_build_table_spec`, `viz_build_chart_spec`, `write_commit`.
2. **Intent output** matches stable JSON keys: `primary_intent`, `entities`, `risk_flags`, `hitl_required`, `suggested_tools`.
3. **SQL guard**: single statement; `SELECT` only; deny DDL/DML keywords; tables ⊆ allowlist from catalog.
4. **Write stub**: rejects missing/short `hitl_token` or empty `idempotency_key`; success returns `status: accepted_stub`.

## 4. NFR (quantified — detail in ADR-002)

- Tool handler p95 (local, no network) **< 50 ms** for `intent_analyze` on strings ≤ 2k chars.
- `sql_execute_read` row cap **≤ 500** rows returned; statement timeout **≤ 5 s** (SQLite default ok).
- `rag_retrieve` returns **≤ 10** chunks, each **≤ 1200** chars.
- Logging: never log full `hitl_token` or user secrets — redact in observability helper.

## 5. Out of scope

- Real vector DB / re-embedding pipeline changes.
- Spring/FE changes.
- Production DB connectivity from MCP process.

## 6. Acceptance

- `pytest` green; `ruff`/`mypy` clean; MCP stdio server module importable.
- SRS AC table satisfied.
