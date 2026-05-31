# CODE_REVIEW — Task002

**Verdict:** PASS  
**Iteration:** 1  
**SRS:** `ai_python/docs/srs/SRS_AI_Task002_langgraph-gemma4-task2.md`  
**ADR:** `ai_python/docs/adr/ADR-002-langgraph-gemma4-task2-graph.md`  
**Task:** `ai_python/TASKS/Task002.md`

## Tóm tắt

- **`app/graph/`:** `AgentState` + reducer messages; main graph `classify_intent → chat | sql_branch → summarize`; subgraph SQL đủ chuỗi node + retry cap 3 + `fail_max_attempts`; registry metadata `INTENT_HANDLERS_V1`; không import FastAPI.
- **SqlExecutor Option C:** `stub` mặc định; `python_ro` / `http_spring` raise `NotImplementedError` có message handoff (đúng PRD cho đến Task 3).
- **Checkpoint Option C:** `MemorySaver` hoặc `SqliteSaver` qua `sqlite3.connect` (tránh xung node name `intent` ↔ state).
- **LG-13/LG-14:** `iter_graph_stream` + `correlation_scope`; `safe_log_sql` khi `MASK_SQL`.
- **Tests:** `tests/test_graph.py` — routing, retry, max attempts, validate DDL, checkpoint `:memory:`, stream; **16** pytest pass (không mạng).

## Findings

- **Nit:** `langgraph` deprecation warning (checkpoint serde `allowed_objects`) — chờ upstream; không chặn.
- **Nit:** `http_spring` / `python_ro` chưa implement — đã ghi NotImplemented + SRS.

## Khớp SRS / ADR

- FR routing, subgraph, retry, executor port, checkpoint, stream/log: đạt trong phạm vi graph-only (không TASK-AG chi tiết).
- ADR-002 NFR 5 mục: phản ánh timeout/doc, retry cap, validate trước execute, env doc, token qua `LlmClient`.

## Hành động cho DEV (BLOCK)

- Không có (PASS).
