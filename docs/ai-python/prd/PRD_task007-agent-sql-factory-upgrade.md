# PRD — Task 007: SQL Agent SQL-Factory-Lite Upgrade (`ai_python`)

**Task ID:** 007  
**Track:** `ai_python` only (FastAPI, LangGraph, LLM callers).  
**Related plans:** Owner plan *Nâng cấp AGENT_SQL* (`nâng_cấp_agent_sql_973e9b61.plan.md`); Spring DDL for table descriptions is **out of scope** here (see [`docs/plan/feature/spring_ai_table_description_registry.plan.md`](../../../../docs/plan/feature/spring_ai_table_description_registry.plan.md)).

**PRD status:** APPROVED — Owner selected **Option B** on 2026-05-11.

---

## 4.1. Project Overview

**Core goal:** Evolve the SQL branch toward a **SQL-Factory–lite** pattern: **subset table selection**, **exploration vs exploitation** prompts (paper Figure 4 / 5 style), **local hybrid similarity** over a small per-turn/thread pool, and **business descriptions merged into `SchemaArtifact`** so the LLM **never** receives DB credentials or opens database connections. All features must remain **optional behind `GraphSettings`/env flags with safe fallbacks**, preserving Task006 contracts: main graph `intent → chat_normal | sql_branch → summarize`, subgraph order `gen_sql → sql_review → validate_sql → execute_sql → validate_result`, and unchanged `SqlExecutor` (`http_spring` / stub) execution semantics.

**Target users:** Operators and developers running the AI chat service; end users asking **system data queries** in Vietnamese/English through the existing chat UI (no direct exposure to internal flags).

---

## 4.2. Specifications

### Functional requirements (FR)

- **FR1 — Schema richness in prompts:** `gen_sql` (and any predecessor step) must render schema text that includes **PK, FK relationships**, and **`TableMeta.description` when present**; if descriptions are absent, generation must proceed without error (optional field).
- **FR2 — Table subset selection:** Before or within SQL generation, compute `selected_tables` (bounded list, e.g. ≤ 8 tables by default, configurable) from `SchemaArtifact` + user question (+ optional intent snippet). Support **fallback to full schema or “all tables”** when artifact is small or selection is disabled/fails.
- **FR3 — Exploration / exploitation modes:** First attempt uses an **exploration**-style prompt (persona, conditional complexity, FK-aware schema block). On controlled retries (validation/execute/result failure **or** high local redundancy per FR4), switch to **exploitation** prompt with a **seed SQL** (last syntactically valid or last failed, length-capped) plus strict allowlist derived from selected schema; respect existing `can_regen_sql` / max-attempt limits.
- **FR4 — Local hybrid similarity (ToolR-lite):** Maintain a **local pool** (per turn/thread in state/checkpoint) of recent generated SQL strings (cap e.g. ≤ 32 entries, configurable). Compute **SimTok** (normalized token overlap) and **SimAST** (via `sqlparse` structure fingerprint). Optionally **SimEmb** behind a flag (default off). If max combined similarity exceeds threshold, inject feedback for retry and/or force exploit path per policy. Attachment point: after `gen_sql` or before `sql_review` (preference: after `gen_sql` to avoid redundant review cost on obvious duplicates).
- **FR5 — Management policy (no separate management LLM):** Deterministic state machine: attempt 1 → explore + table selection; failures / high similarity → exploit with seed; never exceed existing retry budget.
- **FR6 — Description sourcing boundary:** Merging descriptions into `SchemaArtifact` / YAML may use **Spring HTTP** (preferred when available) **and/or** optional read-only PG access **only in application service code** in `ai_python`—never in LLM tools or prompts containing connection strings. Refresh should be **bounded** (startup/job/cache by `schema_version`), not per-request full DB scan unless explicitly configured.
- **FR7 — GraphSettings / registry:** New toggles for hybrid similarity, redundancy threshold, exploit prompt enablement, optional LLM table-pick path, optional SimEmb weights (α/β/γ). New LLM role for structured table selection if Option B/C includes it—map missing role to safe default (`default`) per Task006 patterns.
- **FR8 — Compatibility & regression:** Unchanged routing: `general_chat` must **not** invoke SQL pipeline behavior. With PG/descriptions/sync disabled or failing, **`system_data_query` behavior MUST approximate current Task006** (YAML `FileSchemaLoader`, early-return patterns like `schema_load_failed`). Subgraph topology: either **single `gen_sql` node with internal branching** OR **inserted linear `select_tables → gen_sql`**—never reorder or drop `sql_review`, `validate_sql`, `execute_sql`, `validate_result`.
- **FR9 — State extensions:** Extend `AgentState` with optional keys (`selected_tables`, `sql_gen_mode`, `sql_attempt_history` or equivalent) using **`TypedDict total=False`** and safe defaults for old checkpoints.

### Non-functional requirements (NFR)

- **NFR1 — Latency:** Incremental median end-to-end latency for `system_data_query` with **defaults off** MUST be negligible (&lt; 50 ms CPU-only path vs Task006 baseline in stub mode). With **LLM table-pick + gen** enabled (if chosen), budget **≤ 2 sequential LLM calls** on the SQL path unless Owner approves explicit multi-call mode; optional second call should be skipped when heuristic selection is sufficient (schema size/heuristic confidence flags).
- **NFR2 — Resource caps:** Local SQL pool bounded (default ≤ 32 strings; configurable). Table selection subset default ≤ 8 tables. Seed SQL and feedback strings capped (e.g. ≤ 8–16 KB configurable) before prompt assembly to prevent token blowups.
- **NFR3 — Reliability:** No unhandled raises on missing description table / failed HTTP PG sync—degrade to “no descriptions.” Graph compile must succeed **without** PostgreSQL client libraries installed when direct PG sync is disabled.
- **NFR4 — Security:** Never log secrets (`DATABASE_*`, JWT). Metadata reader (if enabled) MUST use **read-only** semantics and timeouts (e.g. connect + query each ≤ 3 s default, pool size ≤ 5).
- **NFR5 — Observability:** Structured logging or existing trace hooks should record mode (`explore`/`exploit`), similarity decisions, and selected tables at **debug/diagnostic** level without leaking PII.
- **NFR6 — Testability:** Unit tests for similarity metrics, policy transitions (attempt 1→2), prompt allowlist (no tables outside `selected_tables`), and graph regression paths as specified in FR8.

---

## 4.3. Tech stack (`ai_python` only)

| Layer | Technology |
| :-- | :-- |
| API / runtime | FastAPI, Uvicorn |
| Orchestration | LangGraph; existing `main_graph`, `sql_subgraph` |
| Config | Pydantic settings (`GraphSettings`, app `settings`), `.env` / `.env.example` |
| LLM | OpenAI-compatible client, structured invoke, `app/llm/registry.py` roles |
| SQL parsing / similarity | `sqlparse` (required for SimAST); optional embedding API behind flag |
| HTTP integration | Existing Spring relay / executor HTTP mode (no contract change to execute path) |
| Optional metadata DB | `psycopg2-binary` and/or `asyncpg` **only if** Option C (or B variant) enables in-process read-only metadata sync |
| Tests | `pytest`, existing fake LLM / stub executor patterns |

**Out of scope (other repos):** Spring migrations for description registry, frontend changes, executor endpoint contract changes.

---

## 4.4. Task breakdown & dependency graph

Legend: `→` = depends on / should follow.

- [ ] **T1 — State & prompts foundation**  
  - **Description:** Extend `AgentState` (optional keys, checkpoint-safe). Add `sql_prompts` module: builders for exploration (Figure 4 style) and exploitation (Figure 5 style); include PK/FK and `TableMeta.description` in schema block when present.  
  - **Input/Output:** In: `SchemaArtifact`, user message, prior SQL/feedback. Out: prompt strings + state updates.  
  - **Acceptance Criteria:** Type checks pass; old checkpoints merge without KeyError; unit test for prompt sections when descriptions missing vs present.  
  - **Dependencies:** None (baseline for others).

- [ ] **T2 — Table selection**  
  - **Description:** Implement selection producing `selected_tables` per chosen option (heuristic-only vs optional structured LLM). Render **subset schema + one-hop join helpers** as required. Cap table count; fallback when disabled.  
  - **Input/Output:** In: artifact, question, flags. Out: `selected_tables` in state.  
  - **Acceptance Criteria:** With large fixture schema, prompt text excludes non-selected tables; fallback path matches full-schema behavior when flag off.  
  - **Dependencies:** → T1.

- [ ] **T3 — `sql_similarity.py` (SimTok + SimAST; optional SimEmb)**  
  - **Description:** Implement hybrid score, thresholds from `GraphSettings`, local pool append/read from state.  
  - **Input/Output:** In: candidate SQL, pool from state. Out: score, redundancy flag, feedback snippet.  
  - **Acceptance Criteria:** Golden pairs (identical vs structurally different) behave as expected; pool cap enforced.  
  - **Dependencies:** → T1.

- [ ] **T4 — Wire subgraph / `gen_sql` integration**  
  - **Description:** Integrate selection, modes, similarity hook, and retry policy into `sql_pipeline` / `sql_subgraph` **without** breaking node order. Optional separate `select_tables` node only if selected architecture option requires it.  
  - **Input/Output:** In: full `AgentState`. Out: updated SQL + validation feedback.  
  - **Acceptance Criteria:** `gen_sql → sql_review → validate_sql → execute_sql → validate_result` preserved; fake LLM tests cover explore→exploit transition.  
  - **Dependencies:** → T1, T2, T3.

- [ ] **T5 — GraphSettings / `.env.example` / LLM registry**  
  - **Description:** Add flags (hybrid sim, thresholds, exploit enable, LLM pick enable, optional embedding weights, PG metadata URL if applicable). Register new role if needed.  
  - **Input/Output:** Config surface only.  
  - **Acceptance Criteria:** Defaults keep behavior ≈ Task006 when all new features off; documented in `.env.example`.  
  - **Dependencies:** → T4 (can parallelize doc with T4 but merge after behavior stable).

- [ ] **T6 — Description merge path**  
  - **Description:** Implement merge of `table_name → description` into `TableMeta` / artifact build path per chosen option (HTTP-only vs optional direct PG reader). Cache by `schema_version`.  
  - **Input/Output:** In: YAML base + external source. Out: enriched `SchemaArtifact`.  
  - **Acceptance Criteria:** Missing source does not crash; merged descriptions appear in prompt snapshots in tests.  
  - **Dependencies:** → T1; coordination with Spring contract is **design-only** in this PRD (no backend edits in this task).

- [ ] **T7 — Tests & regression suite**  
  - **Description:** Extend `test_task006_sql_dbmeta.py` / `test_agents.py` / graph tests: general_chat path, SQL path with stub, schema load failure, new flags on/off.  
  - **Input/Output:** Automated test results.  
  - **Acceptance Criteria:** CI green; coverage for FR3–FR5 and FR8.  
  - **Dependencies:** → T4, T5, T6.

---

## Architecture options (Owner HITL)

### Option A — Heuristic-only selection, monolithic `gen_sql`, HTTP/YAML descriptions only

**Summary:** Table subset via **keyword/heuristic** matching on artifact names and optional description text already in memory; **no** second LLM call for table picking. **Explore/exploit** implemented as **internal helpers** inside the existing `gen_sql` node (no new graph node). **Table descriptions** enter `SchemaArtifact` only via **prebuilt YAML** and/or **Spring HTTP bulk fetch**—**no** `psycopg2`/`asyncpg` in `ai_python`.

**Pros:** Lowest latency and LLM cost; smallest dependency footprint; simplest ops (no DB reader credentials in Python); easiest to reason about in tests.  
**Cons:** Weaker table choice on ambiguous natural language when schema is large; all selection logic must be maintained as heuristics.  
**Risks:** Under-selection or over-selection of tables without LLM nuance; HTTP dependency for fresh descriptions if YAML is stale.  
**Cost-to-change:** Low now; migrating to LLM pick later requires refactor of selection boundary.  
**When to choose:** Tight budget, small-to-medium schemas, or policy forbids extra Python DB dependencies.

### Option B — Hybrid selection + optional `select_tables` node + HTTP-first descriptions (recommended)

**Summary:** **Heuristic-first**; optional **structured LLM** (`sql_table_pick` or equivalent) when schema size or low heuristic confidence and flag enabled. **Single `gen_sql` node** OR **optional linear `select_tables` node** before `gen_sql`, controlled by `GraphSettings` for clarity and testability. **Similarity + exploit** behind soft-launch flags. Descriptions: **prefer Spring HTTP** merge into artifact; optional async job in Python that **only** calls HTTP—still no direct PG in Python unless Owner later selects C.

**Pros:** Balances quality and cost; aligns with Owner plan’s “heuristic và/hoặc structured LLM”; preserves Task006 compatibility via flags; clear seam for tests when `select_tables` is a node.  
**Cons:** More branches and settings to document; two-call path must be carefully gated.  
**Risks:** Misconfigured flags could enable double LLM unexpectedly—mitigate with schema-size thresholds in code.  
**Cost-to-change:** Medium; most future enhancements (SimEmb, PG reader) plug in without renaming public API.  
**When to choose:** Default for **chat online** ERP use cases with evolving schema and willingness to tune flags.

### Option C — LLM-forward selection, dedicated `select_tables` node, optional direct PostgreSQL reader in `ai_python`

**Summary:** **Default or frequent use** of structured LLM for table picking on non-trivial schemas. **Always** expose **`select_tables` as its own subgraph node** before `gen_sql`. Add **optional** read-only metadata sync using **`DATABASE_URL_METADATA_RO`** with `psycopg2` or `asyncpg` inside a dedicated service module for merging descriptions (still **never** exposed to LLM).

**Pros:** Highest expected SQL relevance on large schemas; faster description refresh cycles without waiting on new Spring endpoints if PG URL is acceptable; subgraph structure explicit in traces.  
**Cons:** Highest latency/cost baseline; duplicated credential surface in Python ops; strongest security/compliance scrutiny for DB URLs.  
**Risks:** Connection leaks or slow queries impacting startup—needs strict timeouts/pool limits (NFR4).  
**Cost-to-change:** Higher initial implementation and ops checklist.  
**When to choose:** Large multi-table warehouse-style schemas **and** Org accepts Python-holding read-only PG credentials alongside Spring.

**Recommendation:** **Option B** best matches the Owner plan’s emphasis on optional features, fallback to Task006 behavior, Soft launch via `GraphSettings`, and **HTTP-first** description integration—with room to escalate to **C** later without rewriting similarity or exploit logic.

---

## Owner decision (HITL — closed)

**Selected option:** **B** — Hybrid selection + optional `select_tables` node + HTTP-first descriptions; heuristic-first with optional structured LLM table pick when flags/schema thresholds allow; no direct PostgreSQL reader in `ai_python` for this task unless escalated later to Option C.

**Locked scope for implementation:** Follow Option B summary in §4.4 options table; all SQL-Factory-lite features remain behind `GraphSettings` / env with Task006-compatible fallbacks.




