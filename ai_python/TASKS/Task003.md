# Task003 — erp_db_read_rag
- SRS: [`SRS_AI_Task003_erp_db_read_rag.md`](../docs/srs/SRS_AI_Task003_erp_db_read_rag.md)
- PRD: [`PRD_Task003_erp_db_read_rag.md`](../docs/prd/PRD_Task003_erp_db_read_rag.md)
- Branch: feature/ai-task003
- Owner chain: AI_TECH_LEAD (ADR/registry) → AI_DEVELOPER → AI_CODE_REVIEWER → AI_TESTER (`G-AI-TST`)
- DoD overall: SRS §7 AC-1 … AC-5; eval matrix SRS §6 + NFR-03 `[default‑OK]` scale-out

## Dependency graph (AI_PM §4)

```text
Unit-T003-1 → Unit-T003-2 → Unit-T003-3
                      ↓
            Feature-T003-1 → Feature-T003-2 → Feature-T003-3
                                                      ↓
                                               Eval-T003-1
```

- Eval depends on Feature; Feature depends Unit; Units chain on shared Python contracts (state → MCP models → SSE).

## Unit
- [x] Unit-T003-1 — `ChatState` Task003 deltas (intent, `rag_*`, `db_*`, gate reason) pydantic validators | DoD: AC-2 (router/state fields ready) | Gate: `G-AI-DEV` | depends: -
- [x] Unit-T003-2 — MCP `vector-rag` + `db-readonly` request/response + `McpToolError` parity SRS §4 | DoD: AC-2, AC-4 | Gate: `G-AI-DEV` | depends: Unit-T003-1
- [x] Unit-T003-3 — SSE envelope/`token`/`tool_*`/`error`/`done` payload guards + refusal/error code mapping helpers SRS §10 | DoD: AC-1, AC-4 | Gate: `G-AI-DEV` | depends: Unit-T003-2

## Feature
- [x] Feature-T003-1 — LangGraph path: mandatory `rag.search_*` first; stream `tool_call`/`tool_result`, `token`, `done`; audit `correlation_id` across turn | DoD: AC-1 | Gate: `G-AI-CR` | depends: Unit-T003-3
- [x] Feature-T003-2 — Router: RAG-only vs RAG+DB; ≤1× `sql.query_readonly`/turn; template_id allowlist + typed params; answer grounded in tool rows/summary | DoD: AC-2 | Gate: `G-AI-CR` | depends: Feature-T003-1
- [x] Feature-T003-3 — Refuse DML/write/secret in `token`; no `awaiting_approval`/`committed`; map MCP reject (`DB_QUERY_REJECTED`, etc.) to SSE `error` or explanatory `token` + `done`; RAG ingest/stale telemetry hooks SRS §7 AC-5 / NFR-05 `[default‑OK]` | DoD: AC-3, AC-4, AC-5 | Gate: `G-AI-CR` | depends: Feature-T003-2

## Eval
- [x] Eval-T003-1 — JSONL seed prompts for AI_TESTER: SRS §6 rows **#E1–#E5** + note to expand ≥30 / NFR-03 | DoD: SRS §6 prompt #E1–#E5 + §6 “≥30 prompt” sentence | Gate: `G-AI-TST` | depends: Feature-T003-3

## Risks / Notes
- `MCP_PHASE=0` vs PRD Option A: align TL ADR / bridge before integration test against real MCP.
- Template allowlist ownership (OQ‑01): default registry in `ai_python` with MCP double-enforce.
- Optional `rag.search_catalog` / `ui(TableSpec)` per SRS §9 defaults — keep behind config to avoid scope creep.
