# Task003 — Triển khai Agents v1 trên LangGraph + Gemma 4 (PRD FINAL)

**PRD:** `ai_python/docs/prd/PRD_langgraph-gemma4-task3-agents.md`  
**SRS:** `ai_python/docs/srs/SRS_AI_Task003_langgraph-gemma4-task3-agents.md`  
**ADR:** `ai_python/docs/adr/ADR-003-langgraph-gemma4-task3-agents.md`  
**Artifact folder:** `ai_python/docs/task003/`

## Definition of Done

- [x] BA✓ — SRS Approved
- [x] TL✓ — ADR-003 ghi NFR 5 mục
- [x] DEV✓ — Code + pytest (38 passed) + ruff PASS (mypy/coverage N/A theo repo)
- [x] CR✓ — `docs/task003/05-code-review/CODE_REVIEW_Task003.md` verdict PASS (iteration 2)

**Tuỳ chọn pre-release:** AI_TESTER / AI_BRIDGE.

## Checklist triển khai (ánh xạ FR-* SRS / TASK-* DESIGN — Option C đã chốt)

- [x] AG-01..02 — intent (structured + fallback general_chat) + chat_normal (LLM, không tool DB)
- [x] AG-03 — gen_sql + SchemaLoader.load(schema_version) + bucket feedback + tăng sql_attempt_count trước LLM
- [x] AG-04 — sql_review structured {ok, issues[]} qua get_llm_client("sql_review")
- [x] AG-05 — validate_sql upgrade: SELECT-only, allowlist, LIMIT inject/bắt buộc, deny DDL/DML
- [x] AG-06 — execute_sql wiring qua SqlExecutor stub (giữ port, không python_ro)
- [x] AG-07 — validate_result max_rows/max_bytes; empty không retry
- [x] SUM-01..02 — summarize_answer locale vi-VN; xử lý empty
- [x] REG-01..03 — registry hardening unknown intent → general_chat + howto thêm intent
- [x] DBM-01..03 — schema YAML format + SchemaLoader Protocol + FileSchemaLoader + allowlist reuse
- [x] CTX cite — bảng vị trí Agent đọc field state vs config["configurable"]
- [x] TEST — fake LLM unit/Agent + retry test (3 lần) + empty-result test + unknown intent test + coverage ≥ 85% nodes mới
