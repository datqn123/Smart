# ADR-001 — Port `LlmClient` + OpenAI-compatible (Gemma / FPT Cloud)

**SRS:** `ai_python/docs/srs/SRS_AI_Task001_langgraph-gemma4-task1.md`  
**Task:** `ai_python/TASKS/Task001.md`  
**Date:** 2026-05-10

## 1. Bối cảnh & quyết định

Task 1 cần kết nối Gemma 4 qua gateway OpenAI-compatible trong khi roadmap có **nhiều model / nhiều chức năng**. Quyết định: giới hạn phụ thuộc LangGraph/LangChain ở **implementation** bên trong, còn nghiệp vụ và test dựa trên **port `LlmClient`** và **registry theo role**.

## 2. Phương án đã xem xét

- **A — Thin factory `ChatOpenAI`:** nhanh, khó mở rộng đa provider/mock.  
- **B — Port + adapter + registry:** boilerplate hơn, phù hợp đa model.  
- **C — SDK `openai` thuần song song LangChain:** rủi ro lệch stream/invoke.

## 3. Quyết định

Áp dụng **Option B (PRD)**: `typing.Protocol` `LlmClient`, class `OpenAICompatibleChatClient` bọc `ChatOpenAI`, `LlmRegistry` với role tối thiểu `default`.

## 4. Hệ quả

- Node LangGraph sau này chỉ inject `LlmClient` hoặc gọi registry — không import `ChatOpenAI` trực tiếp.  
- Thêm model/role: thêm implementation hoặc map env mới trong registry; không đổi Protocol trừ khi thiếu capacity (version bump ADR).  
- Spike gateway capability ghi `docs/task001/01-scope/GATEWAY_CAPABILITY.md`.

## 5. NFR (5 mục)

1. **Hiệu năng:** Wrapper stream phải là iterator — không đọc toàn bộ response vào bộ nhớ một lần cho đường stream chuẩn.  
2. **Reliability:** `LLM_REQUIRED=1` → thiếu `LLM_API_KEY` fail fast khi build registry; parse structured retry tối đa 3.  
3. **Bảo mật:** Không log secret; không commit key; `SecretStr` cho api_key trong settings.  
4. **Vận hành:** Biến env có tài liệu `.env.example` + README; `LLM_SEND_TOP_K` mặc định tắt để tránh 400 gateway.  
5. **Chi phí token:** Structured path ưu tiên native nếu gateway hỗ trợ; fallback JSON prompt ngắn, không retry vô hạn.
