# Task001 — LLM Gemma4 / OpenAI-compatible (port Option B)

**SRS:** `ai_python/docs/srs/SRS_AI_Task001_langgraph-gemma4-task1.md`  
**PRD:** `ai_python/docs/prd/PRD_langgraph-gemma4-task1.md`  
**ADR:** `ai_python/docs/adr/ADR-001-langgraph-gemma4-llm-port.md`  
**Artifact folder:** `ai_python/docs/task001/`

## Definition of Done

- [x] BA✓ — SRS Approved  
- [x] TL✓ — ADR ghi NFR 5 mục  
- [x] DEV✓ — Code + pytest (mock) pass  
- [x] CR✓ — `docs/task001/05-code-review/CODE_REVIEW_Task001.md` verdict PASS  

**Tuỳ chọn pre-release:** AI_TESTER / AI_BRIDGE — không nằm DoD lean.

## Checklist triển khai

- [x] LM-01 Settings + `.env.example` + validate `LLM_REQUIRED`  
- [x] LM-02 `LlmClient` + `OpenAICompatibleChatClient` + registry  
- [x] LM-03 `stream_text_deltas` / `join_stream`  
- [x] LM-04 `structured_predict` + fallback + schemas  
- [x] Tests + README env names  
