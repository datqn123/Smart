# SRS — AI Python — Task002 / LangGraph foundation + SQL subgraph

**Status:** Approved (lean PM_RUN)  
**MCP_PHASE:** 0  
**PRD:** `docs/ai-python/prd/PRD_langgraph-gemma4-task2.md`  
**Task:** `docs/ai-python/tasks/Task002.md`

---

## 1. Tóm tắt & phạm vi

**In-scope (`ai_python/`):** LangGraph **`StateGraph`** + **`AgentState`** (`messages` + `add_messages`); main flow `START → intent → route_by_intent`; nhánh `general_chat` (stub/callable LLM qua `LlmClient`); nhánh `system_data_query` → **subgraph** `sql_query` với chuỗi `gen_sql → sql_review → validate_sql → execute_sql → validate_result`, retry về `gen_sql` tối đa **3** lần (`MAX_SQL_ATTEMPTS`), `validation_feedback` chuẩn hoá; node `fail_max_attempts`; **registry** intent → runnable; **port `SqlExecutor`** (Option C: `stub` | `python_ro` | `http_spring`); **checkpointer** Option C (Memory mặc định, Sqlite khi `CHECKPOINT_SQLITE_PATH`); hook `astream` / `astream_events`; **log/mask** SQL theo `MASK_SQL`. Graph **không** import FastAPI.

**Out-of-scope:** Thiết kế prompt/Agent node chi tiết (TASK-AG PRD khác); `backend/` / `frontend/`; endpoint FastAPI production (Task 3); bộ test E2E đầy đủ (Task 4).

---

## 2. Stakeholder & luồng

| Actor | Vai trò |
| :-- | :-- |
| Task 3 (FastAPI) | Gọi `graph.invoke` / `astream` với `configurable` (`thread_id`, `correlation_id`, `tenant_id`, …) |
| Task 1 `LlmClient` | Node `intent`, `chat_normal`, `gen_sql`, `sql_review` gọi qua port (có thể mock) |

**Luồng chính — chat:** user message → `intent` → `general_chat` → `final_answer`.  
**Luồng chính — SQL:** `intent` → subgraph → `summarize_answer` → `final_answer`.  
**Luồng lỗi:** hết 3 lần gen → `fail_max_attempts` + `error_payload` có cấu trúc.

---

## 3. Functional (numbered)

1. **FR-01:** Khai báo `langgraph` (và `langgraph-checkpoint-sqlite` nếu dùng Sqlite) pin trong `requirements.txt`.
2. **FR-02:** `AgentState` gồm tối thiểu: `messages` (reducer `add_messages`); `intent`; `schema_version`; `generated_sql`; `sql_attempt_count`; `validation_feedback`; `query_result`; `final_answer`; `correlation_id` / `tenant_id` (state hoặc `config["configurable"]` — thống nhất một nơi trong code + comment).
3. **FR-03:** Main graph: `START → intent →` `route_by_intent` tới `chat_normal` hoặc subgraph SQL rồi `summarize_answer` → `END`.
4. **FR-04:** `INTENT_HANDLERS` (hoặc tương đương) map `general_chat` / `system_data_query`; intent không hợp lệ → `general_chat` (mặc định an toàn).
5. **FR-05:** Subgraph: thứ tự node đúng PRD; mọi fail trước retry ghi thêm `validation_feedback`; `sql_attempt_count` **tăng mỗi lần bắt đầu `gen_sql`** (trước LLM).
6. **FR-06:** `can_regen_sql(state) -> bool` khi `sql_attempt_count < MAX_SQL_ATTEMPTS` (3).
7. **FR-07:** `validate_sql` deterministic: `SELECT` only, deny DDL/DML, allowlist bảng (env `SQL_ALLOWED_TABLES` tuỳ chọn), bắt buộc `LIMIT` hoặc inject an toàn.
8. **FR-08:** `SqlExecutor` theo `SQL_EXECUTOR_MODE`; **stub** cho CI; `python_ro` / `http_spring` stub raise rõ hoặc TODO có docstring nếu chưa có URL.
9. **FR-09:** `build_checkpointer()`: Memory nếu không có path; `SqliteSaver.from_conn_string` khi `CHECKPOINT_SQLITE_PATH` set.
10. **FR-10:** `stream_events_with_correlation` hoặc tương đương — yield events từ `graph.astream_events` / `astream`; gắn `correlation_id` vào log context khi có.
11. **FR-11:** `safe_log_sql(sql)` / policy — khi `MASK_SQL=1` không log SQL đầy đủ.

---

## 4. API / integration

- **Spring:** không gọi trực tiếp trong Task 2; `http_spring` executor là placeholder / env URL sau.
- **Graph API:** `compile_agent_graph(deps) -> CompiledGraph`; `invoke` / `astream` / `astream_events` với `thread_id` trong `configurable`.

---

## 5. Data / state

- **Intent:** literal `general_chat` \| `system_data_query` (khớp Task 1 schema).
- **SqlReviewOutput / IntentOutput:** tái sử dụng `app.llm.schemas`.
- **error_payload (fail_max):** tối thiểu keys `error`, `attempts` (hoặc tương đương).

---

## 6. NFR

| ID | Yêu cầu |
| :-- | :-- |
| NFR-SEC-01 | Mọi `execute_sql` chỉ sau `validate_sql` pass trên cạnh graph |
| NFR-SEC-02 | `MASK_SQL=1` → không log full SQL |
| NFR-OBS-01 | Correlation id log xuyên node khi cấp trong configurable |
| NFR-TEST-01 | Pytest không mạng; mock `LlmClient` + `SqlExecutor` stub |

---

## 7. Acceptance

- Given mock LLM trả `system_data_query`, When invoke graph, Then đi qua subgraph (ít nhất các node tên đã đăng ký trong event hoặc state có `generated_sql`/`query_result` stub).
- Given validate_sql fail liên tiếp, When retry, Then đúng **3** lần vào `gen_sql`, không có lần thứ 4.
- Given `CHECKPOINT_SQLITE_PATH` trỏ file tạm, When hai invoke cùng `thread_id`, Then `messages` tích lũy (smoke).

---

## 8. Traceability

| FR | PRD |
| :-- | :-- |
| FR-01…06 | TASK-LG-01…11 |
| FR-07 | TASK-LG-08 + validate deterministic |
| FR-08 | § Options SQL C |
| FR-09 | § Options Checkpoint C |
| FR-10…11 | TASK-LG-13…14 |
