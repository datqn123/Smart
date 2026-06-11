# Plan — Agentic AI Rebuild (ai_python)

## Solution approach

Xây mới `ai_python/app` (code cũ đã xóa) thành một **Agentic AI** với LLM Qwen3.6-27B (qua FPT Cloud OpenAI-compatible API) đóng vai **Session Manager / planner-evaluator**. SM nhận raw require, lập plan, gọi tool theo cơ chế **structured JSON decision + dispatcher**, đánh giá kết quả, tự quyết `retry_tool` / `replan` / `request_clarification` / `finish`. Mỗi tool là một LangGraph subgraph "phiên nhỏ" `[load_skill → execute → self_validate]`, đọc skill `.md` mỗi lần chạy (kể cả retry). Harness lo auth + map `User_ID → Thread_ID`. Output qua SSE. Build này **stateless** (memory để vòng sau).

**Lưu ý workflow:** Plan này chỉ là **bản phác thảo định hướng** (kèm `facts.md`) để chốt thiết kế. Phần triển khai chi tiết sẽ được **viết lại sau bằng superpowers (writing-plans)** — các Ordered steps dưới đây là khung tham chiếu, không phải plan thi công cuối cùng.

### Cấu trúc module dự kiến
```
ai_python/app/
  config/      settings (pydantic-settings), llm_client (openai→Qwen), backend_client (httpx)
  harness/     auth (PyJWT), session (User_ID→Thread_ID), turn_context, sse_emitter
  registry/    static registry: {tool_name → subgraph} + mô tả nhét vào context SM
  tools/
    session_manager/  __init__.py + skill.md
    sql_execute/      __init__.py + skill.md
    data_validator/   __init__.py + skill.md
    answer_composer/  __init__.py + skill.md
  graph/       orchestrator (large-session loop), dispatcher, subgraph builder, hitl pause/resume
  api/         FastAPI app, /chat endpoint, SSE streaming
  memory/      (DEFERRED — chỉ placeholder, không tích hợp vòng này)
```

## Ordered steps

### Step 1 — Scaffold + config module
- Tạo cây thư mục; `config/settings.py` (pydantic-settings đọc `.env`), `config/llm_client.py` (openai SDK trỏ `LLM_BASE_URL`, model `LLM_MODEL`), `config/backend_client.py` (httpx tới Spring).
- **Files:** `app/config/*`
- **Verify:** `pytest` unit test settings load đúng từ `.env`; llm_client khởi tạo với base_url/model đúng (mock HTTP, không gọi thật).

### Step 2 — Harness: auth + session
- `harness/auth.py` verify JWT (PyJWT, `JWT_HS256_SECRET`), hỗ trợ `AUTH_DEV_BYPASS`. `harness/session.py` map `User_ID → Thread_ID`. `harness/turn_context.py` gói context truyền vào pipeline.
- **Files:** `app/harness/*`
- **Verify:** test JWT sai/hết hạn → reject (không vào pipeline) [fact-auth]; JWT hợp lệ → thread_id resolved [fact-thread].

### Step 3 — Registry + skill loader
- `registry/registry.py`: dict static `{tool_name → subgraph builder}` + bảng mô tả tool. Helper `load_skill(tool_name)` đọc `tools/<name>/skill.md`.
- **Files:** `app/registry/*`
- **Verify:** registry liệt kê đúng 4 tool [fact-registry-static]; `load_skill` đọc đúng nội dung `.md` vào state.

### Step 4 — Tool subgraph skeleton (chung)
- Builder dựng subgraph `[load_skill → execute → self_validate]` cho mọi tool; `load_skill` luôn là node đầu; `self_validate` kiểm tra output của chính tool trước khi trả [comment fact-tool-subgraph].
- **Files:** `app/graph/subgraph.py`
- **Verify:** test subgraph chạy đúng thứ tự node; load_skill chạy đầu; re-invoke (retry) → load_skill đọc lại `.md` [fact-retry-reload]; self_validate chặn output sai.

### Step 5 — Tool `sql_execute`
- `execute`: sinh SQL từ raw_require (LLM + skill.md), chạy read-only. **SQL guard** (sqlparse): chỉ cho `SELECT`, chặn INSERT/UPDATE/DELETE/DROP/ALTER → trả lỗi an toàn; áp `SQL_EXECUTOR_ROW_LIMIT`. Read-only enforce ở tầng kết nối (xem Risk R1).
- **Files:** `app/tools/sql_execute/__init__.py` + `skill.md`
- **Verify:** test non-SELECT bị chặn không thực thi [fact-sql-guard]; SELECT chạy trên stub trả data [fact-sql-execute]; guard unit tests (sqlparse).

### Step 6 — Tool `data_validator`
- `execute`: đọc raw_require + data cuối, phán phù hợp/không (LLM + skill.md), trả verdict + lý do.
- **Files:** `app/tools/data_validator/__init__.py` + `skill.md`
- **Verify:** case data khớp → pass; lệch → fail [fact-validator-check]; đảm bảo validator là cổng bắt buộc trước composer [fact-validator-before].

### Step 7 — Tool `answer_composer`
- `execute`: soạn câu trả lời từ data các step + raw_require; văn lịch sự, đủ thông tin, **gợi ý bước tiếp theo** [comment fact-composer]. Chỉ chạy sau validator pass.
- **Files:** `app/tools/answer_composer/__init__.py` + `skill.md`
- **Verify:** test composer không chạy khi validator chưa pass [fact-composer]; output chứa phần gợi ý next-step (assert cấu trúc/marker).

### Step 8 — Session Manager + orchestrator loop
- `tools/session_manager/skill.md` + `graph/orchestrator.py`: vòng lặp phiên lớn. SM xuất structured JSON `{action, tool_name, forward_data, reasoning}` với action ∈ {call_tool, retry_tool, replan, request_clarification, finish}. Dispatcher map tool_name → subgraph, payload luôn `{raw_require, upstream_data}`. SM phân loại lỗi tool vs lỗi plan. Budget `HARNESS_MAX_STEPS` + retry cap mỗi tool.
- **Files:** `app/graph/orchestrator.py`, `app/graph/dispatcher.py`, `app/tools/session_manager/*`
- **Verify:** JSON decision validate bằng pydantic [fact-sm-decision]; dispatcher route đúng + luôn kèm raw_require [fact-dispatcher]; SM reload skill khi re-analyze [fact-sm-reanalyze]; lỗi tool→retry, lỗi plan→replan [fact-sm-errorclass]; chạm max_steps → dừng an toàn [fact-budget].

### Step 9 — HITL pause/resume (chỉ phía backend)
- Validator fail → SM `request_clarification` → emit SSE clarify/confirm event → **persist pending state** (pause) → resume khi nhận `clarification_response` [comment fact-validator-hitl].
- **Frontend đã có sẵn UI confirm** — backend chỉ cần emit event đúng contract mà frontend đang dùng (không dựng UI mới). Việc còn thiếu là hạ tầng pause/persist + resume ở backend.
- **Files:** `app/graph/hitl.py`, tích hợp `app/api/*`
- **Verify:** test pause emit đúng shape event frontend mong đợi + lưu pending; resume tiếp tục đúng chỗ [fact-validator-hitl].

### Step 10 — API + SSE
- `api/app.py` FastAPI; endpoint `/chat` nhận require từ Spring; stream SSE. Thiết kế emit SSE **không** để node-key flatten làm mất payload key (bài học cũ: bọc nhất quán theo key cố định).
- **Files:** `app/api/*`
- **Verify:** end-to-end happy path stream SSE [fact-sse]; HITL clarify event đúng shape; config nối Qwen + backend [fact-config-llm, fact-config-backend].

### Step 11 — End-to-end happy path test
- Integration: require → SM → sql_execute → data_validator(pass) → answer_composer → SSE.
- **Verify:** `pytest` integration với **FakeLLM client** + **stub SQL executor** (theo precedent project); assert thứ tự tool + SSE cuối.

## Verification strategy
- `pytest` + `pytest-asyncio`; FakeLLM client (deterministic) thay Qwen; stub SQL executor thay DB; mọi external (LLM/DB/Spring) bắt buộc có fallback mock. Mỗi fact `automatedVerification:true` map tới ≥1 test ở step tương ứng.

## Risks & open questions
- **R1 — SQL path (BLOCKING quyết định):** interview chọn "DB trực tiếp read-only" nhưng `.env` để `SQL_EXECUTOR_MODE=http_spring` + `SPRING_SQL_URL=.../query-readonly-raw` (Spring đã có endpoint readonly như một guard sẵn). Cần chốt: nối thẳng `DATABASE_URL_RO` (tự guard bằng sqlparse) **hay** đi qua endpoint readonly-raw của Spring. Ảnh hưởng Step 5.
- **R2 — Plan thi công viết sau:** plan chi tiết để code sẽ được soạn riêng bằng superpowers (writing-plans); goal package này chỉ cung cấp facts + định hướng.
- **R3 — Trùng SRS-006:** `.env` có `AGENTIC_V3_ENABLED=1` (Planner-Brain, SRS-006). Thiết kế "mới hoàn toàn" này có thể thay/đè SRS-006 — cần reconcile tên SRS, flag, và tránh hai hệ song song.
- **R4 — HITL pause/resume:** hạ tầng pause chưa tồn tại (Step 9) — rủi ro build lớn nhất; cần checkpointer/persist pending state (có `langgraph-checkpoint-sqlite` sẵn).
- **R5 — Structured output trên Qwen:** SM phụ thuộc JSON decision ổn định. Nếu Qwen kém ổn định, có sẵn `LLM_STRUCTURED_MODEL=gemma-4-26B` để fallback cho riêng SM decision (lệch khỏi "Qwen cho mọi tool" — cần bạn duyệt).
- **R6 — SSE contract:** dựng lại sạch, tránh lặp lại bug flatten làm mất payload key.
