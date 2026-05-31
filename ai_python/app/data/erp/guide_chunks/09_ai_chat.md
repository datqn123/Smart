## 9. AI Chat — Smart Assistant

> Requires permission: `can_use_ai`

### Architecture

```
Browser (React) → Spring Boot (Java, port 8080) → Python FastAPI (port 9000) → PostgreSQL (via Spring JDBC)
     ↑                    ↑                      ↑
   SSE events          JWT Auth              LLM (Gemma/OpenAI-compatible)
   Chart cards         Relay
   Draft tables        SQL exec
```

### 9.1. General Chat

**Flow:** `START → domain_guard → context_compact → classify_intent → chat_normal → END`

`domain_guard` loads the ERP capability index (from `docs/guides/GUID_ERP.md`) and may return `clarify` (SSE + questions) or `reject` before any SQL/draft/chart branch runs.

```
Frontend: User types message → POST /api/v1/ai/chat/stream { message, conversationId } + Bearer token
  ↓
Spring: Extract user_id/tenant_id from JWT → Build ChatRequest → Forward to Python (same Bearer)
  ↓
Python Auth: Validate JWT → Cross-check claims with metadata
  ↓
Intent Node: LLM classifies intent → "general_chat"
  ↓
Chat Normal Node: Takes last 20 messages (truncated to 4000 chars) → calls LLM with system prompt
  ↓
SSE Streaming: event: delta (partial text), event: done (end)
  ↓
Frontend: appendDeltaSmart() (Vietnamese-aware spacing) → render chat bubble
```

### 9.2. Data Query (SQL Generation Pipeline)

**Flow:** `START → classify_intent → sql_branch(subgraph) → summarize_answer → END`

#### SQL Subgraph Diagram

```
schema_explore (optional) → gen_sql → sql_review → validate_sql → execute_sql → validate_result
                                                                        ↓ (failure)
                                                                   decide_sql_retry → back to gen_sql
                                                                        ↓ (success)
                                                                 summarize_answer
```

#### Step Details

| Step | Description |
|---|---|
| **schema_explore** | LLM identifies metric, dimensions, tables → calls Spring `/describe` for column metadata → builds SchemaArtifact |
| **gen_sql** | Increment sql_attempt_count → load schema → build prompt with schema + dialog tail + feedback → LLM generates SQL |
| **sql_review** | LLM reviews SQL → SqlReviewOutput(ok, issues[]) → filters benign issues → appends feedback |
| **validate_sql** | Deterministic: sqlparse parse → checks: 1 statement, SELECT only, no DDL/DML, table allowlist, column allowlist → auto-inject LIMIT |
| **execute_sql** | Calls Spring `/query-readonly-raw` → JDBC PreparedStatement.executeQuery() → returns {rows, columns, meta} |
| **validate_result** | Checks: has data, ≤50,000 rows → flags result_empty if 0 rows |

#### Retry Logic

| Type | Max Budget |
|---|---|
| Policy validation | 3 attempts |
| Execution | 3 attempts |
| Result validation | 2 attempts |
| Total SQL attempts | MAX_SQL_ATTEMPTS (configurable) |

#### Summarization

```
summarize_answer node:
  - Localize timestamps to Asia/Ho_Chi_Minh
  - Build prompt with dialog tail + SQL rows (6000 chars)
  - LLM summarizes in Vietnamese Markdown
```

### 9.3. Chart Generation

**Flow:** `START → classify_intent → agent_idea → sql_branch → chart_readiness → agent_chart → agent_review → END`

| Step | Description |
|---|---|
| **agent_idea** | LLM generates IdeaPlannerOutput: data_request (metric, time range, filters) + chart_idea (chart_type, axis semantics) |
| **sql_branch** | Runs SQL pipeline to fetch data (same as 9.2) |
| **chart_readiness** | Heuristic checks + optional LLM critic → determines data is suitable for charting |
| **agent_chart** | LLM generates ChartSpecDraftOutput(chart_type, x_key, y_key, title) — Recharts-compatible |
| **agent_review** | Reviews draft, aligns keys to real columns → chart_spec_final with ≤200 rows data |

**SSE:** `event: chart` → Frontend `AiChatChartCard.tsx` renders Bar/Line/Pie via Recharts

**Chart degrade:** When SQL retries exhausted but query_result has data → draw chart from last available data.

### 9.4. Catalog Draft (HITL — Human-In-The-Loop)

**Flow:** `START → classify_intent → catalog_draft_branch(subgraph) → END`

| Step | Description |
|---|---|
| **classify_catalog_entity** | LLM classifies: product|category|supplier|customer + row count (1-50) |
| **generate_catalog_draft** | LLM generates columns and rows → enrich → validate → fallback stub rows on error |
| **persist_catalog_draft** | Calls Spring `POST /api/v1/ai/catalog-drafts` → saves draft to DB |

**SSE:** `event: draft` → Frontend `AiChatDraftTableCard.tsx` renders editable table

**Frontend actions:**
- "Add Row" → adds new row
- "Save Draft" → PATCH draft
- "Confirm Write to DB" → POST /commit → Spring creates real entities (products, categories, etc.)
- "Cancel" → DELETE draft

**Commit result:** Each row shows `committedAt` (green bg) or `lastError` (red bg with error messages).

### 9.5. Intent Classification

| Intent | Route | Description |
|---|---|---|
| `general_chat` | chat_normal | General conversation (fallback) |
| `system_data_query` | sql_branch | Data query via SQL |
| `system_data_chart` | agent_idea → sql_branch → chart | Chart generation |
| `catalog_data_entry` | catalog_draft_branch | Catalog data entry HITL |

### 9.6. SSE Events

| Event | Trigger | Payload | Frontend Handler |
|---|---|---|---|
| `delta` | Each final_answer increment | Text string | onDelta → appendDeltaSmart() |
| `chart` | chart_spec_final first appears | JSON spec | onChart → AiChatChartCard |
| `draft` | catalog_draft_sse first appears | JSON draft | onDraft → AiChatDraftTableCard |
| `done` | Graph completes | Empty | onDone → stop typing indicator |
| `error` | Graph or HTTP error | Vietnamese text | onError → display error |

### 9.7. SQL Safety — 4 Layers

| Layer | Mechanism |
|---|---|
| **Executor-level** | enforce_read_only_sql(): blocks DDL/DML, multi-statement, transaction control |
| **Deterministic validation** | sqlparse AST: 1 statement, SELECT only, table/column allowlist, auto-LIMIT |
| **LLM review** | Structured review with SqlReviewOutput(ok, issues[]) |
| **Retry policy** | Per-kind budgets, duplicate SQL detection, chart degrade fallback |

### 9.8. Conversation Memory

- **Checkpointer:** MemorySaver (in-memory) or SqliteSaver (persistent file)
- **Thread ID:** `sessionStorage ai_chat_conversation_id` — UUID per browser tab
- **Dialog tail:** Last 12 messages (max 2000 chars) injected into prompt for gen_sql and summarize; prepends `conversation_summary` when set.
- **Compaction (`context_compact`):** When user turns > 10 (configurable), summarizes older turns to 8 Vietnamese lines, keeps last 2 user turns, prunes old messages from checkpoint.
- **Each new turn:** Resets query_result, generated_sql, final_answer, error_payload, intent. Keeps thread_id, user_id, tenant_id, `conversation_summary`.

---