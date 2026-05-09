# AUDIT — Task005 — final — 2026-05-09

- **Mode**: final  
- **Verdict**: **WARN**  
- **Workspace git** (evidence): `feature/ai-task005` @ `ac05124` (`test(ai-python): Task005 AC traceability and SRS §10 JSON fixtures`)

## Spot-check results

| Gate | Check | Status | Note |
| :--- | :--- | :---: | :--- |
| **G-AI-BA** | PRD + SRS; §1–11; `[CRITICAL]` OQ; Approved | **PASS** | `PRD_Task005_db_rag_agent_context.md`; `SRS_AI_Task005_db_rag_agent_context.md` has `## 1` … `## 11`; line ~231 states **không có** `[CRITICAL]`; §11 Approved. |
| **G-AI-PM** | `Task005.md`: ≥1 Unit, Feature, Eval; DoD↔AC; Branch label | **WARN** | Structure OK (3 Unit, 5 Feature, 2 Eval); `Branch: feature/ai-task005`; DoD links AC1–AC6. **Eval-T005-1 / Eval-T005-2 still `[ ]`** while `EVAL_REPORT` + `eval_run_*.jsonl` show completed run — PM execution truth lags TST. |
| **G-AI-TL** | ADR: 5 NFR (số), ≥2 alternatives, Accepted, mermaid | **PASS** | `ADR-003-db_rag_agent_context.md`: §NFR 1–5; **3** alternatives; Status **Accepted**; mermaid `flowchart TD`. |
| **G-AI-DEV** | pytest/ruff/mypy + app/test map | **PASS** (by CR record) | `CODE_REVIEW_Task005.md` records `ruff` / `mypy` / `pytest` Pass (57 tests). Grep `# AC: AC1`…`AC6` across `tests/**/test_task005_*.py`. |
| **G-AI-CR** | Report; verdict PASS; §3.1–3.5; iteration ≤3 | **PASS** | `docs/task005/05-code-review/CODE_REVIEW_Task005.md`: **PASS**; checklist all `[x]`; iteration **2**; prior Block/Major resolved per summary. |
| **G-AI-BRIDGE** | Bridge table; SSE + MCP paths vs SRS | **PASS** | `docs/api/bridge/BRIDGE_AI_Task005_db_rag_agent_context.md`: full columns; all Design SSE names as **n/a**; `sql.describe` / `sql.query_readonly` / `query_readonly_raw` rows; gate self-check **PASS**. |
| **G-AI-TST** | EVAL_REPORT, RED_TEAM_*, eval_run jsonl; pass-rate; HITL | **PASS** | `EVAL_REPORT_Task005.md` (100%, 38/38); `RED_TEAM_HITL_Task005.md`, `RED_TEAM_MCP_Task005.md`; `eval_run_20260509T053858Z.jsonl` = **38** lines (≥30; not fake gate); HITL bypass **0** by construction per HITL doc. |
| **G-AI-DS** | Sync report; Block drift | **PASS** (0 Block) | `docs/sync_reports/SYNC_REPORT_Task005_2026-05-09.md`: **0** `[Block]`; **Major** DS-1–DS-3 documented with Owner forks (see Anomalies). |

## Cross-handoff matrix (Task005 — batch slice)

Task005 v1 is **CLI/batch only** (no runtime SSE). Matrix uses SRS/ADR capability rows, not Design Chat-only examples.

| Item | SRS | ADR | Code | Test | Eval | Bridge |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| MCP `sql.describe` | ✓ §4.1 | ✓ | ✓ `contracts` / `db_readonly_port` / `task005_describe` | ✓ | ✓ `batch_describe` | ✓ |
| MCP `sql.query_readonly` | ✓ §4.2 | ✓ | ✓ `contracts` / port / `task005_smoke` | ✓ | ✓ `batch_smoke` | ✓ |
| Non-capability `sql.query_readonly_raw` | ✓ §1 | ✓ | ✓ absent | ✓ | ✓ | ✓ |
| `CorpusJobContext` / job context | ✓ §3 | ✓ | ✓ `app/contracts/task005.py` | ✓ | ✓ pipeline caps | ✓ (via job/MCP rows) |
| SSE Design vocabulary (REFERENCE_ONLY) | ✓ §2, §10 | ✓ (no ChatState) | n/a slice | n/a | n/a | ✓ n/a rows |
| RAG namespaces `erp_schema` / `erp_template_health` | ✓ | ✓ | ✓ ingest/fs | ✓ | ✓ `batch_rag` | ✓ (substance in BRIDGE + SRS) |

**Cross-count sanity:** no mismatch “5 events in SRS vs 3 in code” — batch scope keeps SSE as vocabulary only; MCP row count aligns (2 tools + explicit non-raw).

## Anomalies

- **[Major] OR-001 — PM Eval checkboxes vs completed TST artifacts** — Evidence: `ai_python/TASKS/Task005.md` L36–37 `Eval-T005-1` / `Eval-T005-2` remain **`[ ]`**; `docs/task005/04-tester/EVAL_REPORT_Task005.md` reports **100%** (38/38) and raw `eval_run_20260509T053858Z.jsonl` has **38** entries. **Impact:** G-AI-PM execution truth not updated after G-AI-TST green. **Owner:** Mark eval lines `[x]` or add explicit “closed by EVAL_REPORT dated …” per `WORKFLOW_RULE` handoff.
- **[Major] OR-002 — Doc sync Majors (PRD / SRS vs as-built)** — Evidence: `SYNC_REPORT_Task005_2026-05-09.md` **DS-1** (PRD §4.6 checklist unchecked vs shipped), **DS-2** (PRD entrypoint naming vs `app.cli.task005_*`), **DS-3** (glossary in PRD/SRS vs no `glossary` in `app/` ingest). **0 Block** per sync; resolutions are Owner choice (patch PRD/SRS vs code).  
- **[Minor] OR-003 — MCP audit fields on Python boundary** — Evidence: `CODE_REVIEW_Task005.md` **[Minor] CR-003** — `SqlDescribeIn` / `SqlQueryReadonlyIn` omit SRS §4 audit surface fields; logging has `correlation_id`. Tracked as Minor; acceptable for v1 stub transport.  
- **[Info] OR-004 — NFR measurement gap** — `EVAL_REPORT_Task005.md` notes batch p95 / MCP p95 **not** stress-measured (fake MCP, short runs). Aligns with ADR measurement notes; not a gate fake.

**Not observed:** `WIP`/`FIXME` in `ai_python/app/**/*.py` (grep); cross-repo edits in `backend/`/`frontend/` for this audit scope (orchestrator did not expand full-repo diff — **STOP** only if Task005 delivery required those paths; CR §3.5 states no `backend/`/`frontend/` scope).

## Recommendations (Owner action)

1. **Close OR-001:** Update `TASKS/Task005.md` Eval section to reflect `EVAL_REPORT` + chosen `eval_run_*.jsonl` canonical path.  
2. **Close OR-002:** Execute SYNC report forks — at minimum PRD checklist + as-built entrypoints (**DS-1**, **DS-2**); decide glossary (**DS-3**) implement vs defer with ADR/SRS amendment.  
3. **Optional follow-up:** CR-003 audit fields when wiring real MCP adapter.

## Gate G-AI-OR (self-check)

| Check | Result |
| :--- | :--- |
| `AUDIT_Task005_final.md` exists | **Yes** |
| Verdict ≠ FAIL | **Yes** (`WARN`) |
| Unresolved **Block** anomalies | **None** listed |
| **Warn** / **Major** have Owner path | **Yes** (above + SYNC_REPORT) |

---

**Executive verdict:** **WARN** — all referenced artifacts exist; branch **`feature/ai-task005`** matches `Task005.md`; **CODE_REVIEW PASS**, **BRIDGE PASS**, **TST PASS** (jsonl depth OK), **DS 0 Block**. Outstanding **Major** items are **PM eval checkbox drift** and **doc/sync Majors (PRD/SRS/glossary)** — no evidence of fake green gates or cross-handoff row-count explosion; resolve via Owner updates to `Task005.md` / PRD / SRS or scoped code per SYNC.
