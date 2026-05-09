# EVAL_REPORT — Task005 (`db_rag_agent_context`)

| Field | Value |
| :--- | :--- |
| **Branch** | `feature/ai-task005` |
| **SRS** | `ai_python/docs/srs/SRS_AI_Task005_db_rag_agent_context.md` §6 |
| **ADR** | `ai_python/docs/adr/ADR-003-db_rag_agent_context.md` |
| **Eval prompts** | `ai_python/tests/eval/prompts.jsonl` (**38** rows — SRS B1–B6 matrix + cross-cutting + red-team seeds) |
| **Harness** | `python tests/eval/run_eval.py` → `tests/eval/task005_eval_checks.py` |
| **Raw run** | `eval_run_20260509T053858Z.jsonl` |

## Summary

| Metric | Result |
| :--- | :--- |
| **Pass-rate** | **100%** (38/38) |
| **Gate G-AI-TST threshold** | ≥ 80% (≥ 24/30) — **PASS** |

Task005 is **batch-only** (no Chat Agent SSE). Eval exercises **mock MCP `db-readonly`**, **artifact writes**, and **local RAG ingest** — not a live LLM or production MCP transport.

## Capability × outcome (from prompt `capability`)

| Capability | Prompts | Pass |
| :--- | :---: | :---: |
| `batch_describe` | 6 | 6/6 |
| `batch_pipeline` | 4 | 4/4 |
| `batch_smoke` | 8 | 8/8 |
| `batch_rag` | 4 | 4/4 |
| `batch_resilience` | 2 | 2/2 |
| `batch_observability` | 2 | 2/2 |
| `batch_contract` | 2 | 2/2 |
| `red_team_hitl` | 5 | 5/5 |
| `red_team_mcp` | 5 | 5/5 |

## NFR vs ADR (measurement notes)

| NFR | ADR target | Eval note |
| :--- | :--- | :--- |
| Batch e2e &lt; 600 s | ADR §NFR 1 | Not stress-benchmarked in this run; single-run durations &lt; 1 s with fake MCP (see `duration_seconds` in `RunOutcome`). |
| MCP call p95 ≤ 3 s | ADR §NFR 1 | **Not** measured (10× repeat per prompt not executed). Recommend cron-friendly soak on real MCP. |
| $/turn ≤ $0.005 | ADR §NFR 2 | **Core path $0** — no MKP/embeddings invoked in eval checks. |
| HITL bypass 0% | ADR §NFR 3 | No mutation/HITL surface in slice — see `RED_TEAM_HITL_Task005.md`. |

## Block / Major findings

**None.** No HITL bypass, no unexpected mutation path, no eval harness crash.

## Failures

None in latest run.
