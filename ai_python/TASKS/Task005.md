# Task005 — db_rag_agent_context

- SRS: [`SRS_AI_Task005_db_rag_agent_context.md`](../docs/srs/SRS_AI_Task005_db_rag_agent_context.md)
- PRD: [`PRD_Task005_db_rag_agent_context.md`](../docs/prd/PRD_Task005_db_rag_agent_context.md)
- Branch: `feature/ai-task005`
- Owner: AI_TECH_LEAD → AI_DEV (`G-AI-DEV`) → AI_CR (`G-AI-CR`) → AI_TESTER (`G-AI-TST`)
- DoD overall: SRS §7 **AC1–AC6** (batch corpus + RAG ingest; read-only MCP; no Chat HTTP/SSE/UI in v1)

## Dependency graph

```text
Unit-T005-1 → Unit-T005-2
Unit-T005-3
       ↘ ↙
   Feature-T005-1 → Feature-T005-2 → Feature-T005-3 → Feature-T005-4 → Feature-T005-5
                                                                              ↓
                                                        Eval-T005-1, Eval-T005-2
```

## Unit

- [ ] Unit-T005-1 — Pydantic models: batch job context (SRS §3), `McpToolError`, audit-friendly metadata fields | DoD: SRS §7 **AC4**, **AC6** | Gate: `G-AI-DEV` | depends: -
- [ ] Unit-T005-2 — Validators / serializers: describe caps (`columns`, `summary`), smoke artifact **summary-only** (no persisted full rows), registry/catalog JSON shape | DoD: SRS §7 **AC1**, **AC2**, **AC4** | Gate: `G-AI-DEV` | depends: Unit-T005-1
- [ ] Unit-T005-3 — Pure helpers: atomic corpus writes, stable corpus paths + `corpus_version` / timestamp naming per module docs | DoD: SRS §7 **AC1** | Gate: `G-AI-DEV` | depends: -

## Feature

- [ ] Feature-T005-1 — CLI/job skeleton: config allowlist load, `correlation_id`, structured logging (objects/templates counts, MCP step errors) | DoD: SRS §7 **AC6** | Gate: `G-AI-CR` | depends: Unit-T005-1, Unit-T005-2, Unit-T005-3
- [ ] Feature-T005-2 — Batch `sql.describe` over allowlisted objects → schema/catalog artifacts (atomic write, version/timestamp, partial `describe_results` per SRS/OQ-02 default) | DoD: SRS §7 **AC1**, **AC6** | Gate: `G-AI-CR` | depends: Feature-T005-1
- [ ] Feature-T005-3 — Registry-driven smoke `sql.query_readonly(template_id, default params)` → `health.json` / template status (**row_count**, codes, no row dump) | DoD: SRS §7 **AC2**, **AC4** | Gate: `G-AI-CR` | depends: Feature-T005-2
- [ ] Feature-T005-4 — RAG ingest over fresh corpus: namespaces **`erp_schema`** + **`erp_template_health`** (reuse existing indexer/stub per OQ-03; integration proves ≥1 chunk readable) | DoD: SRS §7 **AC3** | Gate: `G-AI-CR` | depends: Feature-T005-3
- [ ] Feature-T005-5 — Policy closure: no DB writes from `ai_python`, no credentials/PII in logs/artifacts, graceful MCP-down handling, exit ≠ 0 + summary; NFR batch timing documented/measured (`run_started_at` → `run_finished_at`, target SRS §7 **AC5** / §8) | DoD: SRS §7 **AC4**, **AC5**, **AC6** | Gate: `G-AI-CR` | depends: Feature-T005-4

## Eval

- [ ] Eval-T005-1 — JSONL seed: SRS §6 scenarios **B1–B3** (describe idempotency/versioning; partial describe timeout; dual-template smoke OK without row dumps) | DoD: SRS §6 **#B1**, **#B2**, **#B3** | Gate: `G-AI-TST` | depends: Feature-T005-5
- [ ] Eval-T005-2 — JSONL seed: SRS §6 scenarios **B4–B6** (smoke rejected; MCP unavailable graceful; RAG ingest reads ≥1 chunk from new corpus) | DoD: SRS §6 **#B4**, **#B5**, **#B6** | Gate: `G-AI-TST` | depends: Feature-T005-5

## Risks / Notes

- Slice is **CLI/batch only** — no runtime SSE/Chat Agent (SRS §2); REFERENCE_ONLY JSON in SRS §10.1 is vocabulary only.
- Partial describe failures: default **continue** + exit ≠ 0 if any fail (SRS §9 OQ-02); align CLI exit policy with ADR if present.
- Corpus path/namespaces default `ai_python/data/rag_corpus/` + `erp_schema` / `erp_template_health` unless ADR overrides (SRS §9 OQ-01).
