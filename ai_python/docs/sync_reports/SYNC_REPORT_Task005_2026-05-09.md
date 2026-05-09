# Sync Report — Task005 — 2026-05-09

- **Author**: AI_DOC_SYNC  
- **Scope**: `Task005` (`db_rag_agent_context`)  
- **Code ref**: `feature/ai-task005` @ `ac051243ad35b49b4e28f11ff2b8d52e485c8e1d` (HEAD at scan time)  
- **Sources compared**: `Design_Agent/CHAT_AGENT_DESIGN.md` ↔ `ai_python/docs/prd/PRD_Task005_db_rag_agent_context.md` ↔ `ai_python/docs/srs/SRS_AI_Task005_db_rag_agent_context.md` ↔ `ai_python/docs/adr/ADR-003-db_rag_agent_context.md` ↔ `ai_python/app/**` ↔ `ai_python/docs/api/bridge/BRIDGE_AI_Task005_db_rag_agent_context.md`

---

## Inventories

### Design Doc (`Design_Agent/CHAT_AGENT_DESIGN.md`)

- **Events (§4)**: `token`, `tool_call`, `tool_result`, `ui`, `awaiting_approval`, `approval_resolved`, `committed`, `error`, `done` — Chat/SSE contract for interactive agent.  
- **Tools / MCP (§5, §5.1)**: Includes `db-readonly.sql.query_readonly(template_id, params)`, `db-readonly.sql.describe(object_name)`; mutation/HITL via Write path; read template-first.  
- **Intents (§3)**: Chat routing (`write`, `excel_import`, `chart`, …) — **not instantiated** in Task005 batch slice (per SRS).

### PRD (`PRD_Task005_db_rag_agent_context.md`)

- **v1**: Option B — `sql.describe` batch + smoke `sql.query_readonly` + versioned corpus + RAG ingest; **no** Chat HTTP/SSE/UI.  
- **Artifacts (FR §4.2.1)**: allowlist catalog, columns/types/nullable, **glossary / domain terms**, registry `template_id` → intent/params; smoke status files.  
- **Entrypoint (§4.6 T005-5)**: suggests `python -m ... generate_erp_rag_corpus` (illustrative).  
- **Task breakdown §4.6**: Markdown checkboxes **all `[ ]` unchecked** at doc v1.3.

### SRS aggregate (`SRS_AI_Task005_db_rag_agent_context.md`, Approved 2026-05-09)

- **SSE §2 / §10**: All Design event names listed as **REFERENCE_ONLY** / not emitted in Task005 v1.  
- **MCP §4**: `sql.describe`, `sql.query_readonly`; caps (`columns` ≤ 512, `summary` ≤ 2k, smoke `row_count` ≤ 50); **no** `sql.query_readonly_raw`.  
- **Job context §3**: `CorpusJobContext` fields align ADR-003.  
- **AC / NFR**: AC1–AC6, batch &lt; 10 min, observability `correlation_id`, namespaces `erp_schema`, `erp_template_health` (OQ-01 default).

### ADR-003

- Batch DAG: CLI → describe → smoke → FS artifacts → local RAG ingest → exit + logs.  
- **CorpusJobContext** table; **no** `ChatState`; **no** raw SQL path; namespaces **`erp_schema`**, **`erp_template_health`**.

### Code (`feature/ai-task005`, `ai_python/app`)

- **MCP port**: `app/mcp/db_readonly_port.py` — `describe`, `query_readonly`.  
- **Contracts**: `app/contracts/task005.py` — `McpToolError`, `SqlDescribe*`, `SqlQueryReadonly*`, `CorpusJobContext`, caps `MAX_*` aligned SRS.  
- **Pipeline**: `app/agents/task005_corpus_job.py` — describe → catalog JSON → smoke → health JSON → `ingest_corpus`.  
- **CLI**: `app/cli/task005_corpus_job.py` (`task005-corpus-job`), `app/cli/task005_daily.py` (`python -m app.cli.task005_daily`).  
- **RAG stub**: `app/rag/task005_ingest.py` — chunks from catalog + health only; namespaces `erp_schema` / `erp_template_health` (`task005_corpus_fs.py`).  
- **Registry**: `app/registry/task005_templates.py` — `smoke_safe`, `template_id`, `intent`, `params`.  
- **Tests**: `tests/unit/test_task005_*.py`, `tests/integration/test_task005_*.py`, `tests/eval/test_task005_eval_prompts.py`.  
- **Invariant scan**: No `query_readonly_raw`, no glossary generator module under `app/` (string search).

### Bridge (`BRIDGE_AI_Task005_db_rag_agent_context.md`)

- Rows for SSE events → **n/a**; `sql.describe` / `sql.query_readonly` → code paths cited; verdict **MATCH** ai_python ↔ SRS/MCP doc.

---

## Drift matrix

| Pair | Block | Major | Minor | Info |
| :--- | :---: | :---: | :---: | :--- |
| Design ↔ SRS | 0 | 0 | 0 | SRS explicitly scopes Task005 off interactive SSE/HITL; vocabulary cross-ref consistent. |
| SRS ↔ PRD | 0 | 1 | 0 | PRD §4.6 backlog checkboxes vs SRS “Approved” + shipped code — PM doc lag (see Major DS-2). |
| PRD ↔ ADR | 0 | 0 | 0 | Option B, paths, namespaces aligned. |
| ADR ↔ Code | 0 | 0 | 0 | `CorpusJobContext`, DAG, namespaces, caps match. |
| SRS ↔ Code | 0 | 1 | 0 | SRS §1 / PRD FR1 cite **glossary** in corpus; no dedicated glossary artifact or ingest path in code (see Major DS-3). |
| Code ↔ Bridge | 0 | 0 | 1 | Bridge line anchors may drift on edit; substance still true. |
| Design ↔ Code | 0 | 0 | 0 | No Chat path, no DB writes, template-first MCP only — respects Design invariants for this slice. |

---

## Drift items

### [Block]

*(none — 0 Block drift.)*

### [Major] DS-1 — PRD §4.6 task checklist vs as-built

- **Evidence**: PRD `PRD_Task005_db_rag_agent_context.md` §4.6 lines ~99–128 all **`[ ]` unchecked**; `ai_python/TASKS/Task005.md` shows Feature-T005-1..5 **`[x]`** and code present on `feature/ai-task005`.  
- **Impact**: PM readers see “not started” in PRD while SRS/branch are delivery-complete for feature slice.  
- **Proposed patch (PRD)**: Either mark T005-1..T005-5 as `[x]` with date + link to `TASKS/Task005.md`, or replace checklist with “See `ai_python/TASKS/Task005.md` for live status” and single source of truth.

### [Major] DS-2 — PRD daily entrypoint module name vs shipped CLI

- **Evidence**: PRD §4.6 T005-5 / §4.3 mentions `generate_erp_rag_corpus`-style module; shipped: `python -m app.cli.task005_corpus_job` and `python -m app.cli.task005_daily` (`app/cli/task005_daily.py:6-7`, `app/TASK005_README.md`).  
- **Impact**: Runbook mismatch only (capability exists).  
- **Proposed patch (PRD)**: Add explicit “As-built entrypoints” bullet listing `app.cli.task005_corpus_job` / `app.cli.task005_daily`; keep illustrative name as alias in prose or deprecate old name.

### [Major] DS-3 — Glossary artifact (PRD FR1, SRS §1) vs code

- **Evidence**: PRD §4.2.1 (bullet 3) and SRS §1 (“glossary, registry …”) require **glossary / domain terms** in corpus; `grep` for `glossary` under `ai_python/app` → **no matches**; `task005_ingest.py` only chunks **catalog** + **health** (`_schema_chunks`, `_health_chunks`).  
- **Impact**: Doc scope slightly ahead of implementation; not an invariant breach (read-only, no wrong tool).  
- **Proposed patch (Owner choice)**  
  - **Code path**: Add `erp_glossary/glossary__<corpus_version>.md` (placeholder sections) + one ingest chunk namespace + README note.  
  - **Doc path**: Amend PRD/SRS to “glossary deferred to Task00X” with ADR pointer if Owner accepts corpus v1 without glossary files.

### [Minor] DS-4 — Internal feature IDs in code comments vs PRD IDs

- **Evidence**: e.g. `task005_describe.py:1` “Feature-T005-2”; PRD labels T005-2 describe, T005-2b smoke — numbering differs but mapping is obvious.  
- **Proposed patch**: Optional comment alignment in code or a one-line mapping table in `TASK005_README.md` (no functional change).

### [Minor] DS-5 — Bridge BR-001 (informational)

- **Evidence**: `BRIDGE_AI_Task005_db_rag_agent_context.md` §Drift — `app/main.py` chat SSE uses `delta` / string `[DONE]` vs Design §4 `token`/`done` JSON — **out of Task005 scope**; already tracked as Minor in bridge file.

---

## Recommendations

1. **G-AI-DS**: **PASS** on **Block** count (**0**). Resolve **Major** via Owner: prefer **PRD checklist + entrypoint sync (DS-1, DS-2)** soon; **glossary (DS-3)** either implement minimal placeholder file + ingest or explicitly defer in SRS/PRD with ADR addendum.  
2. Keep **`TASKS/Task005.md`** as execution truth for gates; mirror status into PRD or drop duplicate checklist to avoid double-stale.  
3. Re-run AI_DOC_SYNC after Eval-T005-1/2 close if eval artifacts change contract tables.

---

## Gate G-AI-DS (self-check)

| Check | Result |
| :--- | :--- |
| Report path | `ai_python/docs/sync_reports/SYNC_REPORT_Task005_2026-05-09.md` |
| `Block` drift count | **0** |
| `Major` | DS-1–DS-3 have proposed patch / Owner fork above |
