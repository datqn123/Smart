# SRS — AI Python — Task007 / Agent SQL Factory (SQL-Factory–Lite Upgrade)

**Status:** Approved for PM  
**Date:** 2026-05-11  
**MCP_PHASE:** 0  
**PRD:** `d:\do_an_tot_nghiep\project\ai_python\docs\prd\PRD_task007-agent-sql-factory-upgrade.md`  
**Task ID:** `Task007`  
**Slug:** `agent-sql-factory-upgrade`

**Locked decision:** Owner selected **Option B** — heuristic-first table selection with optional structured LLM table pick (when flags/schema thresholds allow), optional linear `select_tables` subgraph node before `gen_sql`, local hybrid similarity and explore/exploit prompts behind flags, **HTTP-first** merge of table descriptions into `SchemaArtifact`; **no** direct PostgreSQL metadata reader in `ai_python` for this task unless later escalated to Option C.

---

## 1. Summary & Scope

**Goal:** Evolve the SQL branch toward a **SQL-Factory–lite** pattern: bounded table subset selection, exploration vs exploitation prompt paths, local hybrid redundancy detection over a capped per-turn/thread pool, and enrichment of schema text with **PK, FK**, and **`TableMeta.description`** when available—without exposing DB credentials or opening DB connections inside LLM tools or prompts. All new behavior remains **optional** behind `GraphSettings` / env with **Task006-compatible** fallbacks.

**In scope (`ai_python/` only):**

- Extensions to prompts and `gen_sql` (or linear `select_tables → gen_sql` when enabled) implementing FR1–FR5, FR7–FR9.
- `sql_similarity` (SimTok + SimAST; optional SimEmb behind flag), pool management in state, policy wiring after `gen_sql` (preferred attachment) per FR4.
- Configuration surface: new `GraphSettings` toggles, `.env.example`, LLM registry role(s) for optional structured table selection with safe fallback to default role (Task006 pattern).
- Description merge path: YAML base artifact + bounded refresh via **preferred Spring HTTP** bulk fetch concept (design contract only in this SRS); degrade gracefully when source missing or failing.
- Pytest extensions for similarity, policy transitions, prompt allowlists, regression paths (general_chat vs `system_data_query`, flags off ≈ Task006).

**Out of scope:**

- Java/Spring implementations (including DDL migrations for a description registry in Spring). Python may **call** documented HTTP endpoints conceptually once they exist elsewhere.
- Frontend, executor HTTP contract changes, and Postgres schema edits in backend repos.
- In-process **`psycopg2` / `asyncpg`** metadata reader for Task007 (reserved for optional future Option C).

**Handoff (cross-scope):**

- Spring/other services own authoritative table-description storage, API shape, authentication, and rate limits for any HTTP bulk-description endpoint referenced by FR6. Task007 SRS treats that integration as **conceptual**: path/method/payload names are placeholders until aligned in a bridge doc; **no Spring code** in this deliverable track.

---

## 2. Stakeholders & Flows

### 2.1 Stakeholders

| Actor | Role |
| :-- | :-- |
| Product / Owner | Locks Option B; accepts flag-gated rollout and Task006 parity when features are off. |
| AI runtime maintainers | Implement graph, state, prompts, similarity, settings, and tests under `ai_python/`. |
| Spring / platform owners | Optionally expose HTTP APIs for merging descriptions into Python’s artifact builder (contract TBD externally). |
| Operators | Configure toggles, caps, thresholds, URLs, and timeouts; monitor logs at diagnostic level. |
| End users | Ask data questions via existing chat UX; must not see internal modes or credentials. |

### 2.2 Main flow — `system_data_query` with Option B features enabled

```text
User message -> intent routing -> sql_branch entry
  -> [optional select_tables node OR internal selection inside gen_sql] -> selected_tables + mode
  -> gen_sql uses exploration prompt (attempt 1) with subset schema (PK/FK/descriptions when present)
  -> [similarity hook: compare new SQL vs local pool -> maybe redundancy feedback / exploit path trigger]
  -> sql_review -> validate_sql -> execute_sql (unchanged SqlExecutor semantics: http_spring/stub)
  -> validate_result -> summarize
```

On controlled retries (validation/execute/result failure **or** high redundancy per FR4), policy switches to **exploitation**: seed SQL (last syntactically valid or last failed, capped), strict allowlist from selected schema—within existing **`can_regen_sql` / max-attempt** budget (FR5).

### 2.3 Alternative / error flows

- **`general_chat`:** No SQL subgraph behavior; unchanged from FR8.
- **All new flags off or schema small / selection disabled / selection failure:** Fall back to full-schema or Task006-equivalent paths (early returns such as `schema_load_failed`, YAML `FileSchemaLoader` behavior).
- **Descriptions HTTP unavailable:** Artifact and prompts omit descriptions; generation continues without error (FR1, FR6).
- **Optional LLM table-pick gated off or skipped by heuristic confidence:** Single LLM generation call on SQL path when policy allows (NFR1).

---

## 3. Functional Requirements (numbered, testable)

| ID | Requirement | PRD Trace |
| :-- | :-- | :-- |
| **FR-SRS-001** | Schema blocks used in SQL generation must include PK and FK relationships and `TableMeta.description` when populated; when descriptions are absent, `gen_sql` (and predecessors) MUST NOT fail solely for that reason. | FR1 |
| **FR-SRS-002** | Before or within generation, compute `selected_tables` as a bounded list (default maximum **8**, configurable via `GraphSettings`); MUST support heuristic-first selection per Option B. | FR2 |
| **FR-SRS-003** | When optional structured LLM table selection is enabled and schema-size/heuristic-confidence rules permit, MAY invoke structured LLM (registered role per FR7); MUST NOT exceed NFR1 sequential-call budget unless Owner-approved mode is documented. | FR2, FR7, NFR1 |
| **FR-SRS-004** | If selection fails, is disabled, or artifact is small, MUST fall back to full schema behavior consistent with Task006 (no orphaned tables referenced in prompts). | FR2, FR8 |
| **FR-SRS-005** | Attempt **1** MUST use exploration-style prompting; on allowed retries subject to failures or redundancy signal (FR4), MUST switch to exploitation-style prompt including capped seed SQL and allowlist constrained to **`selected_tables`**. | FR3 |
| **FR-SRS-006** | Maintain a per-turn/thread local pool of recent generated SQL strings with enforced cap (**default ≤ 32**, configurable); MUST compute hybrid similarity using **SimTok** (normalized token overlap) + **SimAST** (`sqlparse` fingerprint); optional **SimEmb** only behind flag with weights configurable (FR7). | FR4 |
| **FR-SRS-007** | After `gen_sql` (preferred attachment), MUST evaluate redundancy vs threshold (`GraphSettings`); if redundant, MUST influence retry/exploit feedback per deterministic policy FR5 **without** a separate management LLM. | FR4, FR5 |
| **FR-SRS-008** | Management policy MUST be a deterministic state machine respecting existing retry flags (`can_regen_sql`, max attempts); MUST NOT exceed retry budget introduced in Task006 semantics. | FR5 |
| **FR-SRS-009** | Merging **`table_name → description`** into `SchemaArtifact` MAY use bounded Spring HTTP fetch and/or YAML-only paths; MUST NOT embed connection strings in LLM-visible content; refresh MUST be bounded by **`schema_version`** / cache TTL or job—not unbounded per-request full scan unless explicitly configured (FR6). | FR6 |
| **FR-SRS-010** | Add/register `GraphSettings` for: hybrid similarity enable, redundancy threshold, exploit prompt enablement, optional LLM table-pick enable, optional SimEmb α/β/γ (or equivalent), optional `select_tables` node vs monolithic `gen_sql` switch; MUST map missing LLM roles to **`default`** (Task006 pattern). | FR7 |
| **FR-SRS-011** | With all new toggles defaulted **off**, median incremental latency on `system_data_query` MUST meet NFR1 “negligible” CPU path; observable behavior MUST approximate Task006 (stub mode baseline). | FR8, NFR1 |
| **FR-SRS-012** | Subgraph node order MUST remain **`gen_sql → sql_review → validate_sql → execute_sql → validate_result`**; optional **`select_tables` ONLY** as linear insertion before `gen_sql`; MUST NOT drop or reorder review/validate/execute stages. | FR8 |
| **FR-SRS-013** | Extend **`AgentState`** with optional **`total=False`** keys: `selected_tables`, `sql_gen_mode`, `sql_attempt_history` (or equivalent structure holding attempts, pool entries, redundancy flags **as needed**); old checkpoints MUST merge without `KeyError` when absent. | FR9 |

---

## 4. Integration (conceptual HTTP — Spring descriptions)

Task007 implements **consumer-side** enrichment in Python only; **no** Spring code or OpenAPI edits in this repo.

| Aspect | Specification |
| :-- | :-- |
| Purpose | Bounded bulk fetch or batch map of **`table`** → **`description`** (and possibly `schema_version` echo) compatible with YAML-backed `SchemaArtifact` merge (FR-SRS-009). |
| Transport | HTTPS client from application service layer; timeouts and non-secret headers per NFR4. |
| Failure | Timeout, non-2xx, or malformed body ⇒ log at safe level ⇒ continue **without** descriptions (FR6, NFR3). |
| Credentials | Bearer or mTLS specifics **TBD** with platform owners; MUST NOT leak into prompts or INFO logs (NFR4). |

Concrete path/method/payload naming is **`TBD`** until recorded in project API bridge/handoff artifact outside this SRS.

---

## 5. Data / State

### 5.1 `AgentState` (extensions — illustrative)

Existing keys preserve Task006 behavior (`messages`, `intent`, `schema_version`, `generated_sql`, `sql_attempt_count`, `validation_feedback`, `query_result`, etc.).

| Key | Type intent | Notes |
| :-- | :-- | :-- |
| `selected_tables` | `list[str]` or structured ids | Bounded; drives schema subset and exploitation allowlist. |
| `sql_gen_mode` | `Literal["explore","exploit"]` or equivalent | Diagnostic + policy branching. |
| `sql_attempt_history` | Sequence / TypedDict aggregate | Holds capped SQL pool snippets, redundancy scores, structured feedback—not raw secrets. |

All new keys **`total=False`**; defaults compatible with checkpoints missing them (FR9).

### 5.2 `GraphSettings` / env flags (minimum surface)

Representative toggles (exact names MAY follow codebase naming but MUST cover PRD FR7/NFR):

- Table selection: enable, max tables (≤8 default), heuristic vs optional LLM path, optional **`select_tables` node** wiring.
- Similarity: enable hybrid, pool max (≤32 default), redundancy threshold, optional SimEmb + α/β/γ.
- Exploitation prompts: enable, seed/str feedback max length budgets (≤8–16 KB class per NFR2).
- Descriptions merge: HTTP base URL/feature flag for Spring fetch vs YAML-only mode.
- Operational: diagnostic logging granularity for modes and selected tables (NFR5).

---

## 6. Non-functional requirements

| ID | Requirement | PRD Trace |
| :-- | :-- | :-- |
| **NFR-SRS-101** | With defaults **off**, incremental median end-to-end latency for `system_data_query` (CPU stub path vs Task006) **\< 50 ms** as PRD stipulates “negligible.” | NFR1 |
| **NFR-SRS-102** | With optional LLM table-pick + generation enabled, sequential LLM calls on SQL path ≤ **2** unless Owner-approved multi-call mode is documented separately. Heuristic/fast path MUST skip optional second call when confidence/schema-size rules suffice. | NFR1 |
| **NFR-SRS-103** | Pool, table-count, seed, and feedback caps enforced at assembly time (defaults per PRD: pool ≤32, tables ≤8, string caps in 8–16 KB class configurable). | NFR2 |
| **NFR-SRS-104** | Missing description source, HTTP failure, or malformed metadata MUST NOT crash the graph; graph compile succeeds **without** optional PG drivers when PG path unused (always for Option B scope). | NFR3 |
| **NFR-SRS-105** | Never log secrets (`DATABASE_*`, JWT). Any future read-only metadata client MUST use RO semantics, connect/query timeouts (e.g. ≤3 s default), bounded pool (e.g. ≤5)—**design guidance** for Option C only. | NFR4 |
| **NFR-SRS-106** | Trace/logging at debug/diagnostic level records `explore`/`exploit`, similarity decisions, `selected_tables` without PII leakage. | NFR5 |
| **NFR-SRS-107** | Automated tests cover similarity metrics, policy transitions 1→2, allowlist constraints, and regression paths (FR8). | NFR6 |

---

## 7. Acceptance criteria

### 7.1 Checklist (release gate)

- [ ] With **all new flags disabled**, `general_chat` never enters SQL similarity/selection paths; `system_data_query` matches Task006 regression baselines (stub/http_spring as configured).
- [ ] With flags enabled on fixture data, prompt snapshots show **only** selected tables in subset mode; exploitation prompts never reference tables outside `selected_tables`.
- [ ] Redundancy: golden pairs (identical vs structurally different SQL) produce expected scores/flags; pool cap never exceeded.
- [ ] Old LangGraph checkpoints without new keys deserialize and run without `KeyError`.
- [ ] Description merge: present vs absent HTTP/YAML cases both render valid schema text; missing source is non-fatal.
- [ ] CI green: extended tests per NFR6 and Task007 PRD T7.

### 7.2 Given / When / Then (samples)

| # | Given | When | Then |
| :-- | :-- | :-- | :-- |
| A1 | Large schema fixture, selection **on** | User asks `system_data_query` | `selected_tables` length ≤ configured max; `gen_sql` prompt excludes non-selected tables unless fallback engaged. |
| A2 | Attempt 1 | `gen_sql` runs | Mode `explore` (or equivalent) applied; no seed SQL required. |
| A3 | Validation or execute failure with retries left | Next `gen_sql` | Mode `exploit`; seed SQL present and length-capped; allowlist tied to `selected_tables`. |
| A4 | New SQL highly similar to pool per hybrid score | Similarity hook runs | Redundancy feedback recorded and policy triggers exploit/retry per FR5 without extra management LLM. |
| A5 | Spring description HTTP **down** | Schema load / merge | Service continues; descriptions omitted; no exception surfaces to user. |

---

## 8. Traceability matrix (SRS ↔ PRD)

| PRD FR | Covered by SRS FR-ID(s) |
| :-- | :-- |
| FR1 | FR-SRS-001 |
| FR2 | FR-SRS-002, FR-SRS-003, FR-SRS-004 |
| FR3 | FR-SRS-005 |
| FR4 | FR-SRS-006, FR-SRS-007 |
| FR5 | FR-SRS-007, FR-SRS-008 |
| FR6 | FR-SRS-009, §4 Integration |
| FR7 | FR-SRS-003, FR-SRS-010, §5.2 |
| FR8 | FR-SRS-004, FR-SRS-011, FR-SRS-012 |
| FR9 | FR-SRS-013, §5.1 |

**NFR coverage:** NFR1 → NFR-SRS-101, NFR-SRS-102; NFR2 → NFR-SRS-103; NFR3 → NFR-SRS-104; NFR4 → NFR-SRS-105, §4; NFR5 → NFR-SRS-106; NFR6 → NFR-SRS-107, §7.

---

## Document control

- **Prepared by:** AI_BA (`ai_python`)  
- **PRD reference version:** Task007 PRD as of 2026-05-11 (Option B locked)  
- **STOP rules review:** PRD includes NFR and acceptance; scope remains `ai_python/` with explicit cross-repo handoff for Spring—**PASS** (no Handoff-only minimal SRS required).
