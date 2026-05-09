# Task004 — smart_erp_mcp_server
- SRS: [`SRS_AI_Task004_smart_erp_mcp_server.md`](../docs/srs/SRS_AI_Task004_smart_erp_mcp_server.md)
- PRD: [`PRD_Task004_smart_erp_mcp_server.md`](../docs/prd/PRD_Task004_smart_erp_mcp_server.md)
- ADR: [`ADR-002-smart_erp_mcp_server.md`](../docs/adr/ADR-002-smart_erp_mcp_server.md)
- Plan: [`PLAN_Smart_ERP_MCP_server_v1.md`](../docs/plan/PLAN_Smart_ERP_MCP_server_v1.md)
- Branch: `feature/ai-task004`

## Dependency graph

```text
Unit-T004-1 → Unit-T004-2 → Unit-T004-3
       ↓
Feature-T004-1 → Feature-T004-2
```

## Unit
- [x] Unit-T004-1 — `sqlglot` guard: single-statement SELECT, allowlist tables, deny DML/DDL | Gate: `G-AI-DEV`
- [x] Unit-T004-2 — `intent_analyze` heuristic JSON schema stable | Gate: `G-AI-DEV` | depends: -
- [x] Unit-T004-3 — `ui_*` / `viz_*` builders produce JSON-serializable specs | Gate: `G-AI-DEV` | depends: Unit-T004-1

## Feature
- [x] Feature-T004-1 — FastMCP `smart-erp-ai` stdio: tools wired to pure handlers + in-memory SQLite seed | Gate: `G-AI-DEV` | depends: Unit-T004-1–3
- [x] Feature-T004-2 — Observability helper + `write_commit` stub validation | Gate: `G-AI-DEV` | depends: Feature-T004-1

## Eval
- [x] Eval-T004-1 — Red-team prompts JSONL seed under `docs/task004/04-tester/` (SQLi multi-stmt, forbidden DDL) | Gate: `G-AI-TST` | depends: Feature-T004-2

## Risks
- ADR-001 Task003 forbids raw SQL in **chat graph**; Task004 MCP is **separate surface** — ADR-002 clarifies boundaries.
