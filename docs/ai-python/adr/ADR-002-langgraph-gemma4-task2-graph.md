# ADR-002 — LangGraph main + SQL subgraph + SqlExecutor / checkpointer (Task 2)

**SRS:** `ai_python/docs/srs/SRS_AI_Task002_langgraph-gemma4-task2.md`  
**Task:** `ai_python/TASKS/Task002.md`  
**Date:** 2026-05-10

## 1. Bối cảnh & quyết định

Cần orchestration LangGraph trong `ai_python` với nhánh SQL có retry có giới hạn, đồng thời giữ **một cổng LLM** (`LlmClient`) và **tách thực thi SQL** khỏi logic graph để CI dùng stub và prod chọn Spring/DB sau. PRD FINAL chốt **SqlExecutor Option C** và **Checkpoint Option C**.

## 2. Phương án đã xem xét

- **A — Monolith node:** một file graph khổng lồ — nhanh ban đầu, khó test từng nhánh.  
- **B — Subgraph SQL riêng + main graph:** ranh giới rõ, khớp DESIGN; compile subgraph làm một node.  
- **C — Full LangGraph cloud features / Redis checkpoint:** vượt scope Task 2.

## 3. Quyết định

- **Main `StateGraph`** + **`sql_query` subgraph** biên dịch riêng, add làm node `sql_branch`.  
- **`SqlExecutor` protocol** + factory `stub` | `python_ro` | `http_spring` (RO/HTTP có thể minimal/stub đến Task 3).  
- **Checkpointer:** `MemorySaver` mặc định; `SqliteSaver.from_conn_string` khi `CHECKPOINT_SQLITE_PATH` có giá trị.  
- **Node LLM** chỉ gọi `LlmClient` đã inject qua `GraphDeps`, không import `ChatOpenAI` trong graph.

## 4. Hệ quả

- Thêm dependency `langgraph`, `langgraph-checkpoint-sqlite` (cho Sqlite).  
- FastAPI (Task 3) chỉ cần `graph.compile(checkpointer=…)` và truyền `thread_id`.  
- `http_spring` executor cần contract REST — handoff Task 3 + AI_BRIDGE nếu đổi payload.

## 5. NFR (5 mục)

1. **Hiệu năng:** Executor stub/O(1) trong test; đường thật document timeout ≤ 30s (HTTP/DB) tại implementation sau.  
2. **Reliability:** `MAX_SQL_ATTEMPTS = 3` một module; không retry vô hạn; `fail_max_attempts` có payload ổn định.  
3. **Bảo mật:** Không execute SQL chưa qua `validate_sql`; `MASK_SQL` ẩn SQL trong log.  
4. **Vận hành:** Env `SQL_EXECUTOR_MODE`, `CHECKPOINT_SQLITE_PATH`, `MASK_SQL` trong `.env.example`; không commit secret.  
5. **Chi phí token:** Node LLM gọi qua `LlmClient` có structured + retry parse (Task 1); graph không nhân đôi completion không cần thiết — intent một lần mỗi turn.
