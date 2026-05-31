# SRS — AI Python — Task001 / LangGraph Gemma4 Task1 (LLM port)

**Status:** Approved (lean PM_RUN)  
**MCP_PHASE:** 0  
**PRD:** `docs/ai-python/prd/PRD_langgraph-gemma4-task1.md`  
**Task:** `docs/ai-python/tasks/Task001.md`

---

## 1. Tóm tắt & phạm vi

**In-scope (`ai_python/`):** Cấu hình LLM qua env; port **`LlmClient`**; implementation OpenAI-compatible bọc **`ChatOpenAI`**; **registry theo role**; wrapper stream chunk văn bản; structured output (intent, sql_review) + fallback JSON + retry parse; `.env.example` + README tên biến; unit test với mock client.

**Out-of-scope:** LangGraph compile đầy đủ (Task 2), FastAPI route production chat (Task 3), multimodal LM-05, chỉnh `backend/` / `frontend/`.

---

## 2. Stakeholder & luồng

| Actor | Vai trò |
| :-- | :-- |
| Dev / Agent | Cấu hình env, gọi `get_llm_client(role)` trong node sau này |
| Gateway FPT | OpenAI-compatible `chat.completions` |

**Luồng chính:** App load `LlmSettings` → validate nếu `LLM_REQUIRED=1` → build `LlmRegistry` → consumer gọi `client.invoke_text` / `stream_text` / `structured_predict`.

**Luồng lỗi:** Thiếu `LLM_API_KEY` khi `LLM_REQUIRED=1` → raise rõ ràng lúc build registry. Parse JSON fail → retry tối đa N → lỗi có kiểm soát.

---

## 3. Functional (numbered)

1. **FR-01:** Đọc biến môi trường `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`, `LLM_TEMPERATURE`, `LLM_MAX_TOKENS`, `LLM_TOP_P`, `LLM_TOP_K`, `LLM_STREAMING_DEFAULT`, `LLM_SEND_TOP_K`, `LLM_REQUIRED` (xem `.env.example`).
2. **FR-02:** `LlmSettings` Pydantic; không log secret; `top_k` chỉ gửi tới provider khi `LLM_SEND_TOP_K=true` và `LLM_TOP_K` set.
3. **FR-03:** Protocol `LlmClient` với ít nhất: đồng bộ invoke trả text; iterator stream trả chuỗi delta văn bản; API structured theo mục 5.
4. **FR-04:** `OpenAICompatibleChatClient` là implementation duy nhất tạo `ChatOpenAI` nội bộ.
5. **FR-05:** `get_llm_client(role: str)` — roles đăng ký tối thiểu `default`; role không map → dùng `default` (log `DEBUG` một lần mỗi process hoặc document hành vi — chọn **fallback `default`** cho v1).
6. **FR-06:** Wrapper stream: consumer nhận iterator/generator các `str` delta (có thể rỗng — bỏ qua khi join).
7. **FR-07:** Structured: thử `with_structured_output`; nếu lỗi hoặc không dùng được → prompt JSON + parse + Pydantic validate + retry tối đa 3 lần (cấu hình hằng số module).
8. **FR-08:** Schema Pydantic **Intent**: literal `general_chat` \| `system_data_query`. Schema **SqlReview**: `ok: bool`, `issues: list[str]`.
9. **FR-09:** Ghi file capability stub `docs/ai-python/task001/01-scope/GATEWAY_CAPABILITY.md` (template bảng: native structured / cần fallback — có thể để trống cho dev điền sau spike).

---

## 4. API / integration

- **Provider:** HTTP OpenAI-compatible; `base_url` không hard-code secret trong repo.
- **FastAPI:** Task 1 không bắt buộc route mới; có thể thêm lifespan validate `LLM_REQUIRED` (tuỳ chọn, ghi Task).

---

## 5. Data / state

**IntentOutput**

- `intent: Literal["general_chat", "system_data_query"]`

**SqlReviewOutput**

- `ok: bool`
- `issues: list[str]`

**LlmSettings** (fields khớp FR-01); dùng `SecretStr` cho `api_key`.

---

## 6. NFR

| ID | Yêu cầu |
| :-- | :-- |
| NFR-SEC-01 | Không commit `LLM_API_KEY`; không log giá trị key |
| NFR-OBS-01 | Không log full completion; có hook để gắn correlation sau Task 2 |
| NFR-TEST-01 | Unit tests chạy không mạng (mock `LlmClient`) |
| NFR-PERF-01 | Stream không buffer toàn bộ response vào một biến duy nhất trong wrapper (iterator) |

---

## 7. Acceptance

- Given `LLM_REQUIRED=0` và không set key, When import/build registry lazy, Then không crash app khởi động (trừ khi gọi client — raise rõ).
- Given `LLM_REQUIRED=1` và thiếu `LLM_API_KEY`, When `build_llm_registry`, Then raise `ValueError` hoặc tương đương có message tiếng Anh/Việt rõ ràng.
- Given mock `LlmClient`, When unit test stream, Then ghép delta == nội dung mong đợi.
- Given response JSON mẫu (fixture string), When `structured_predict` fallback path, Then parse thành `IntentOutput` / `SqlReviewOutput`.

---

## 8. Traceability

| FR | PRD |
| :-- | :-- |
| FR-01–02 | §4.2 TASK-LM-01 |
| FR-03–05 | §4.2 TASK-LM-02 (Option B) |
| FR-06 | §4.2 TASK-LM-03 |
| FR-07–08 | §4.2 TASK-LM-04 |
