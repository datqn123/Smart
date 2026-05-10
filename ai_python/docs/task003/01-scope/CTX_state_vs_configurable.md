# State vs `config["configurable"]` (FR-CTX-01)

Track: `ai_python`. Liên quan Task 2 **LG-03.4** — metadata luồng (correlation, tenant, …) có thể đặt trên **state** hoặc **LangGraph config**, nhưng trong codebase hiện tại graph đọc chủ yếu từ **state**.

## Bảng tham chiếu (triển khai hiện tại)

| Field / metadata | Nguồn đọc trong graph | Ghi chú |
| :-- | :-- | :-- |
| `messages` | `AgentState` | Reducer `add_messages`. |
| `intent`, `schema_version`, `generated_sql`, `sql_attempt_count` | `AgentState` | Luồng intent → SQL subgraph. |
| `validation_feedback`, `query_result`, `final_answer` | `AgentState` | Feedback bucket + kết quả + đáp án cuối. |
| `sql_review_ok`, `sql_valid`, `result_ok`, `result_empty` | `AgentState` | Cờ routing subgraph. |
| `error_payload` | `AgentState` | `schema_load_failed`, `max_sql_attempts`, … |
| `correlation_id` | `AgentState` *(field có trong TypedDict)* | Logging qua `correlation_scope` / `CorrelationFilter`; có thể set từ caller khi invoke. |
| `tenant_id` | `AgentState` | Truyền vào `SqlExecutor.execute(..., tenant_id=...)`. |
| `thread_id` / checkpoint | **`config["configurable"]["thread_id"]`** | Khi `compile_agent_graph(..., use_checkpointer=True)` — không đọc từ state trong nodes hiện tại. |

## Quy ước mở rộng

- Nếu sau này tenant hoặc correlation chỉ có trong **runtime config**, adapter invoke nên **copy** vào `AgentState` trước `graph.invoke` để nodes không đổi.
- Tránh đọc trực tiếp `config` trong node trừ khi refactor rõ ràng — SRS khuyến nghị một nơi thống nhất (LG-03.4).
