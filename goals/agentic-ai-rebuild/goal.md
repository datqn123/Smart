# Goal — Agentic AI Rebuild (ai_python)

Xây mới hoàn toàn `ai_python/app` thành một **Agentic AI**: LLM Qwen3.6-27B (qua FPT Cloud API) đóng vai **Session Manager / planner-evaluator** — phân tích raw require của user, lập plan, gọi các tool trong static registry theo cơ chế **structured JSON decision + dispatcher**, đánh giá kết quả và tự quyết `retry_tool` / `replan` / `request_clarification` / `finish`. Mỗi tool là một LangGraph subgraph "phiên nhỏ" `[load_skill → execute → self_validate]`, đọc skill `.md` mỗi lần chạy (kể cả retry). Harness lo auth + map `User_ID → Thread_ID`; output qua SSE. Build này stateless (conversation memory để vòng sau).

## Shared understanding
Xem [facts.md](facts.md) — 22 facts đã được duyệt, là nguồn sự thật cho mọi outcome cần test/verify.

## Execution plan
Xem [plan.md](plan.md) — khung 11 step + chiến lược verify + 6 risks. **Lưu ý:** plan thi công chi tiết sẽ được viết lại sau bằng superpowers (writing-plans); plan.md hiện là định hướng đã chốt.

## Done condition
- Pipeline end-to-end happy path chạy được: require → Session Manager → `sql_execute` → `data_validator` (pass) → `answer_composer` → SSE.
- 4 tool hoạt động đúng skill `.md` + self-validate output; skill được đọc lại mỗi lần retry.
- SQL guard chặn mọi câu không phải SELECT; read-only enforce ở tầng kết nối.
- HITL pause/resume (backend) hoạt động khi validator fail, emit đúng event frontend đang dùng.
- Harness auth + thread mapping hoạt động; SSE contract dựng lại sạch.
- Mọi fact `automatedVerification:true` có ≥1 test (pytest + FakeLLM + stub SQL) pass.
- Các risk R1 (SQL direct vs Spring) và R3 (trùng SRS-006) được reconcile trước khi code Step 5 / khởi động.
