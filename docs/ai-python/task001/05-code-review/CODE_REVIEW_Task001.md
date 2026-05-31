# CODE_REVIEW — Task001

**Verdict:** PASS  
**Iteration:** 1  
**SRS:** `ai_python/docs/srs/SRS_AI_Task001_langgraph-gemma4-task1.md`  
**ADR:** `ai_python/docs/adr/ADR-001-langgraph-gemma4-llm-port.md`  
**Task:** `ai_python/TASKS/Task001.md`

## Tóm tắt

- Port **Option B** (`LlmClient`, `OpenAICompatibleChatClient`, `LlmRegistry`) đã triển khai dưới `app/llm/`; `ChatOpenAI` chỉ được tạo trong `build_chat_openai`.
- Cấu hình **Pydantic Settings** + `validate_llm_required` + **lifespan** FastAPI khớp SRS fail-fast khi `LLM_REQUIRED=1`.
- **Streaming** (`iter_text_chunks` / `join_stream`) và **structured** (`structured_invoke` native + JSON fallback + retry) có unit test (mock, không mạng).
- `.env.example` và README đã bổ sung tên biến; template capability `GATEWAY_CAPABILITY.md` có trong `docs/task001/01-scope/`.

## Findings

- **Nit (không chặn):** `build_llm_registry` luôn yêu cầu credential — hành vi đúng cho “build client thật”; SRS cho phép lazy ở tầng app (không gọi build khi chưa cấu hình).
- **Nit:** `FakeLlmClient.structured_predict` nhánh theo `schema.__name__` — chỉ dùng test, chấp nhận được.

## Khớp SRS / ADR

- FR-01–09 và NFR chính: đạt trong phạm vi Task 1.
- ADR-001 quyết định B + NFR 5 mục: phản ánh trong code (iterator stream, fail-fast, SecretStr, env doc, retry parse).

## Hành động cho DEV (BLOCK)

- Không có (PASS).
