# ADR-001 — Task003 ERP read-only chat: RAG-first + selective MCP db-readonly

- **Status**: Accepted
- **Date**: 2026-05-09
- **Task**: Task003
- **SRS**: [`../srs/SRS_AI_Task003_erp_db_read_rag.md`](../srs/SRS_AI_Task003_erp_db_read_rag.md)

## Context

Task003 extends `ai_python` so Admin users obtain **read-only** answers about Smart ERP concepts, schema/catalog grounding, and **verifiable aggregates** via a **RAG-first** orchestration slice. Scope is **`ai_python/` only** (`backend/` and `frontend/` unchanged). Primary capabilities are **`query`** and **`clarify`**; **`write`**, **`excel_import`** commit paths, and any **`interrupt()` / HITL** mutation flow are **out of scope** — responses must refuse or clarify without emitting `awaiting_approval`, `approval_resolved`, or `committed` on success paths.

The Python service **must not** assemble or submit ad-hoc SQL. Read access to ERP fact data flows only through MCP **`db-readonly`** using **`template_id` + typed `params`** per server allowlist (`DB_READONLY_TOOLS` contract). Semantic retrieval flows through MCP **`vector-rag`** (`VECTOR_RAG_TOOLS` conventions: `top_k ≤ 10`, `max_chunk_chars ≤ 1200`, chunk metadata discipline).

Baseline runtime today (`app/main.py`, `mkp_client.py`) is a thin FastAPI SSE demo against FPT MKP; Task003 introduces LangGraph-shaped orchestration, MCP clients, and Design-aligned SSE vocab (`token`, `tool_call`, `tool_result`, `ui`, `error`, `done`).

Upstream alignment: **`MCP_PHASE` label vs PRD Option A** — Design §5.1.D MVP lists Phase 0 servers without explicitly naming **`db-readonly`**; **this slice instantiates PRD‑first**: enable **`vector-rag` + `db-readonly`** in `ai_python` deploy profiles; **`spring-erp`** / **`files-storage`** remain available for later phases and are **not required** on the minimal happy path for Task003 read/RAG/snapshot numbers.

---

## Decision (Topology + State + Model + MCP + NFR + Guardrails)

### Topology (mermaid)

```mermaid
flowchart TB
  START([Begin turn]) --> INGEST[Normalize input + correlation_id audit context]
  INGEST --> GUARD{Policy guard: write / DML / secret probe?}

  GUARD -->|yes| REFUSE_STREAM[Emit token refusal + optional error code]
  GUARD -->|no| INTENT[Classify slice intent: query | clarify branch]

  INTENT --> RAG_MAND[MCP vector-rag: mandatory retrieval path]

  RAG_MAND --> RAG_TOOLS{Select rag.search_* subset}
  RAG_TOOLS -->|default| RDS[rag.search_docs + rag.search_schema]
  RAG_TOOLS -->|optional config| CAT[rag.search_catalog]

  RDS --> ROUTE{Needs ground-truth numeric / aggregate verification?}
  CAT --> ROUTE

  ROUTE -->| clarify / ambiguous | CLAR[token clarify stream]
  ROUTE -->| RAG-only sufficient | SYNTH[token + optional ui from RAG grounding]
  ROUTE -->|needs DB snapshot| DBCHK{Already used sql.query_readonly this turn?}

  DBCHK -->|yes| SYNTH_CLAMP[token explains cap; no second DB hop]
  DBCHK -->|no| DBNODE[MCP db-readonly: sql.query_readonly once]

  DBNODE --> DBO{Optional describe enrichment}
  DBO -->|rate-limited internal| DSC[sql.describe]
  DBO -->|skip| SYNTH2[Synthesize grounded answer]

  DSC --> SYNTH2

  SYNTH2 --> OUT_MERGE[Stream tool_call/tool_result audit + token + optional ui TableSpec]

  SYNTH --> OUT_MERGE
  SYNTH_CLAMP --> OUT_MERGE
  CLAR --> OUT_MERGE
  REFUSE_STREAM --> DONE_NODE[Emit done + usage telemetry]

  OUT_MERGE --> DONE_NODE

  DONE_NODE --> ENDNODE([Turn complete])
```

**Notes (architecture):**

- **No `interrupt()`** nodes in this graph variant; supervision for mutations is deliberately absent per SRS §5.
- **Mandatory RAG**: every non-refusal turn traverses **`vector-rag`** before eligibility for **`sql.query_readonly`**.
- **Hard cap**: at most **one** `sql.query_readonly` invocation per turn when numeric verification is required (NFR-06 / SRS strategy).
- **`sql.describe`** is **optional, rate-limited** introspection to enrich router or error recovery — not a per-turn default.

### State schema (pydantic)

Extension of base **ChatState** (Design §3.1). Field names and semantics follow SRS §3; types below are **contract-level** (implement as Pydantic models under `app/contracts/`).

| Field | Type (contract) | Default | Purpose |
| :--- | :--- | :--- | :--- |
| `intent` | `Literal["query","clarify"] \| None` (slice path); `write` / `excel_*` **not** executed here | `None` until classified | Drives router; write-like utterances stay in refuse/clarify handling without handoff. |
| `rag_context_ids` | `list[str]` | `[]` | Chunk/source ids for traceability and eval; not required in user-visible text. |
| `rag_namespaces_hit` | `list[Literal["docs","schema","catalog"]]` | `[]` | Observability: which namespaces were queried. |
| `db_readonly_attempted` | `bool` | `False` | True after any `sql.query_readonly` or `sql.describe` in the turn (per SRS wording). |
| `db_template_last` | `{ "template_id": str, "param_keys": list[str] } \| None` | `None` | Audit-friendly template footprint; never persist raw row payloads in state. |
| `readonly_gate_reason` | `str \| None` | `None` | Explains **RAG-only vs RAG+DB** routing for replay and dashboards. |

**Explicit non-goals:** no `proposal_id`, no approval flags, no bulk Excel state deltas in Task003.

### Model & provider

| Role | Provider | Env / naming | Notes |
| :--- | :--- | :--- | :--- |
| Router intent, RAG-vs-DB gate, clarification, refusal copy, answer synthesis | **FPT MKP** (OpenAI-compatible Chat Completions) | **`FPT_MKP_API_KEY`** (required secret), **`FPT_MKP_BASE_URL`** default `https://mkp-api.fptcloud.com`, **`FPT_MKP_MODEL`** default `gemma-4-31B-it` | Same stack as existing `mkp_client`; extend to structured internal calls (non-stream and stream) behind async wrappers. Streaming user-facing deltas remains required for SSE. |
| MCP tool execution | N/A — remote MCP servers | Separate MCP credential env bundle (discovery per `TASKS/Task003.md` T1 naming; not interchangeable with MKP JWT) | MCP I/O audited with **`correlation_id`** continuity per turn. |

**Version lock:** default model string **`gemma-4-31B-it`** (must match MKP tenant availability). **`FPT_MKP_MODEL`** override is the authoritative pin per environment.

**Fallback policy:**

1. If MKP Chat Completions error is **retryable** (timeouts / 5xx burst): bounded async retry with jitter (counts against latency SLO budgets).
2. If MKP rejects request or quota exhausted: downstream **`error` SSE event** with stable internal code and user-safe `token` synopsis; **`done`** still emitted once per §2 contract discipline.
3. **No silent model hop** to a different vendor in MVP without Owner ADR revise — missing keys remain **deployment fail-fast** at process start for production profiles.

*(API keys are standard deploy prerequisites — document in ops runbooks; absence on a developer laptop does not invalidate this ADR.)*

### MCP servers (phase + per-server)

| Phase (label) | Server | Lifecycle for Task003 | Primary tools |
| :--- | :--- | :--- | :--- |
| **0 (instantiate)** | **`vector-rag`** | Required on every substantive turn path | **`rag.search_docs`**, **`rag.search_schema`**; **`rag.search_catalog`** behind config (default OFF; ON for fuzzy SKU / product wording per SRS §9 default). |
| **0 (instantiate)** | **`db-readonly`** | Conditional: **≤ 1 × `sql.query_readonly`** / turn when router demands verified numbers | **`sql.query_readonly`**, optional **`sql.describe`** (frequency-capped internally). |
| **0 / later** | **`spring-erp`**, **`files-storage`** | Not on critical path for Task003 MVP read slice; wire only if a later task extends Spring direct reads or file handoff | As per Design when enabled. |

**Template registry (OQ‑01 default):** `ai_python` holds a **config/registry** of allowed **`template_id` → JSON-schema-like param specs**; MCP server enforces **allowlist duplication** — agent must never send freeform SQL text.

### NFR (5 mục)

| # | NFR theme | Numeric / measurable target (Task003) |
| :--- | :--- | :--- |
| 1 | **Latency p95** (per capability) | **RAG-only path** (mandatory `vector-rag`, no `db-readonly`): **p95 end-to-end until first `token` delta ≤ 4.0 s**. **RAG + one `sql.query_readonly`**: **p95 until first `token` delta ≤ 10.0 s**. (Aligns PRD NFR-01; stricter global Design query/table ≤ 3 s applies to non-RAG-heavy modules — **this slice adopts PRD numbers**.) |
| 2 | **Cost per turn cap** | **Mean model + tool surcharge target ≤ USD 0.005 / turn** on staging aggregates over ≥ 200 turns/week (baseline from Design §6; actual MKP metering must be reconciled monthly — operational budget alert at **USD 0.006** rolling mean). |
| 3 | **HITL bypass** | **0%** tolerance: no `awaiting_approval` / `committed` emission and no mutation tool routes in Task003 graph; red-team fixtures must show **100% refusal** on write/DML prompts (feeds PRD NFR-04 slice interpretation). |
| 4 | **File & row caps + MIME whitelist** | **≤ 5 MB** per upload artifact if file tools appear in later glue; Excel / tabular exports (out of slice commit path) remain **≤ 10 000 rows** per workbook; MIME allowlist **`application/pdf`**, **`text/plain`**, **`text/markdown`**, **`application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`**, **`text/csv`** (reject all others at gateway before index or tool). Task003 **does not** implement import commit — caps still bound any future ingest hook sharing the service. |
| 5 | **Model / provider lock** | **Env vars:** **`FPT_MKP_API_KEY`**, **`FPT_MKP_BASE_URL`**, **`FPT_MKP_MODEL`** default **`gemma-4-31B-it`**; **fallback:** bounded retry only — **no alternate provider** without new ADR. **MCP credentials** independently namespaced per server with fail-fast startup in prod. |

### Coding guardrails

- **Lint / types:** **Ruff** line length **100**, rules **`E,F,I,UP,B,SIM`**; **Mypy** strict with **`--ignore-missing-imports`** allowed only for provisional MCP SDK surfaces until stubs land.
- **Async I/O mandate:** HTTP to MKP, MCP transports (HTTP/SSE/stdio per deployment), and FastAPI endpoints use **async** paths; forbid blocking SDK calls on the event loop (offload via `asyncio.to_thread` only where vendor SDK is sync-only, with timeout guards).
- **Layering:** `app/agents/` (graph nodes), `app/tools/` (thin tool facades), `app/mcp/` (server clients), `app/contracts/` (Pydantic I/O parity with SRS §4), `app/api/` (FastAPI routes, SSE formatter).
- **Logging safety:** **`correlation_id`** on every tool audit row; structured logs store **summaries** and **hashed/redacted args** — never full row dumps or secrets (PRD NFR-07: **≥ 30 days** staging retention target).
- **SQL hygiene:** CI / pre-commit grep policy: **no dynamic `SELECT`/`INSERT`/… string assembly** outside explicit test fixtures allowlist (`TASKS/Task003.md` DoD echoes this).

---

## Alternatives considered (≥ 2)

1. **DB-first (query `db-readonly` before or without RAG)** — Rejected: conflicts with PRD Option A and SRS mandatory RAG path; increases accidental numeric answers without doc grounding and weakens explainability for schema questions.
2. **Raw read-only SQL from the LLM (broad MCP SQL surface)** — Rejected: violates SRS SQL policy and expands attack surface; template+params model is the security/eval contract.
3. **Multi-model split (cheap router + large synthesizer)** — Deferred: adds operational complexity and second billing dimension; single MKP model with disciplined prompts meets MVP if cost alerts stay under cap.

---

## Consequences

### Positive

- Grounded answers with **mandatory RAG** reduce schema hallucination on conceptual queries.
- **Template-bound DB access** yields auditable, testable queries suitable for compliance narrative.
- **Clear absence of HITL nodes** simplifies streaming contract and security review for read slice.

### Negative / risks

- **Dual latency stack** (RAG then optional DB) challenges **10 s** p95 target under slow vector or ERP lock contention — needs aggressive timeouts and parallel RAG sub-queries only where MCP supports.
- **Template registry drift** vs evolving ERP schema requires Owner process to version templates alongside MCP allowlist.
- **Staleness** (NFR-05: knowledge not older than **24 h** vs last successful ingest) demands scheduled ingest discipline outside pure chat path — failure modes must emit **`stale_acknowledged`** telemetry.

---

## Test strategy summary

| Layer | Focus |
| :--- | :--- |
| **Unit** | Pydantic parity for SRS §4 MCP models and SSE payload guards; router unit tests: RAG-only vs RAG+DB vs refuse vs clarify; template allowlist validation. |
| **Integration (async)** | Mock MCP servers: success, `McpToolError` codes (`RAG_*`, `DB_*`), timeouts; assert **≤ 1** `sql.query_readonly` per synthetic turn and mandatory `vector-rag` ordering. |
| **E2E SSE** | Streaming order: `tool_call`/`tool_result` pairs with redacted args, `token` stream, final `done` with **usage** shape; never `awaiting_approval` / `committed` on golden read paths. |
| **Eval / red-team** | Handed to **AI_TESTER** (`G-AI-TST`): seed JSONL from SRS §6 **E1–E5**, expand to **≥ 30** prompts for PRD NFR-03 **≥ 80%** pass bar — not duplicated as CI functional tests. |

---

**G-AI-TL checklist:** sections **Context** + **Decision** (topology, state, model, MCP, **5 numeric NFR rows**, guardrails) + **Alternatives** (≥ 2) + **Consequences** + **Test strategy** — complete; **Status = Accepted**.
