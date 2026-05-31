# ADR-003 — LangGraph Agent v1 (schema fixture, validation feedback, execute_sql stub) (Task 3)

**SRS:** `docs/ai-python/srs/SRS_AI_Task003_langgraph-gemma4-task3-agents.md`  
**Task:** `docs/ai-python/tasks/Task003.md`  
**Date:** 2026-05-10

## 1. Bối cảnh & quyết định

Triển khai logic Agent v1 trên skeleton Task 2; Task 1 + 2 đã chốt port `LlmClient` và `SqlExecutor`. Task 3 cần **3 quyết định kỹ thuật** đồng bộ Option C đã FINAL trong PRD: (a) **`SchemaLoader` Protocol** + `FileSchemaLoader` đọc YAML — không mở DB runtime; (b) **`validation_feedback`** dạng structured dict bucket cố định để LLM `gen_sql` retry tập trung theo nguồn lỗi; (c) **`execute_sql` chỉ wiring stub** v1, giữ port `SqlExecutor` của Task 2 cho phase sau. Đồng thời chốt **strategy LIMIT inject** + **parser deterministic** cho `validate_sql` upgrade.

## 2. Phương án đã xem xét

- **Trục VALIDATE-SQL parser** (cho FR-AG-05):
  - **A — Regex thuần:** đơn giản, ít dependency — dễ false positive/false negative với SQL phức tạp.
  - **B — `sqlparse`:** tokenizer mature, đủ tách statement + heuristic SELECT-only — không validate ngữ pháp đầy đủ như engine thật.
  - **C — `sqlglot`:** AST đầy đủ — nặng hơn, API `.tokens`/`.find_all` phù hợp policy — chi phí bundle và học curve cao hơn B.

- **Trục LIMIT inject strategy** (FR-AG-05):
  - **A — Fail nếu thiếu LIMIT:** buộc LLM viết đúng — rõ ràng nhưng tăng retry và friction CI.
  - **B — Auto-inject `LIMIT N`:** thực dụng — có thể che lỗi prompt/model (LLM không học LIMIT).
  - **C — Hybrid:** inject khi thiếu + log warning + ghi feedback nhẹ vào bucket — cân bằng an toàn và UX — phức tạp hơn A một chút.

- **Trục SchemaArtifact storage path** (FR-DBM-01..02):
  - **A — `ai_python/app/data/schema/<schema_version>.yaml` (in-package):** portable qua `importlib.resources` — cần rebuild/package khi đổi fixture.
  - **B — `ai_python/data/schema/...` (sibling):** tách khỏi package — path cố định có thể lệch deploy layout.
  - **C — ENV `SCHEMA_DIR` + default in-package:** linh hoạt môi trường — thêm biến cấu hình cần document.

- **Trục feedback bucket extras** (FR-AG-04/05/06):
  - **A — Bucket cố định 4 nguồn, không `extras`:** schema chặt, dễ test — thiếu chỗ cho metadata ad-hoc.
  - **B — Thêm `extras: dict | None`:** mở rộng không phá contract bucket — rủi ro prompt “rác” nếu không giới hạn kích thước/nội dung.

## 3. Quyết định

- **VALIDATE-SQL parser** = **`sqlparse` (B)** — đủ cho v1 SELECT-only + DDL/DML deny; nhẹ hơn `sqlglot`, phổ biến trong hệ sinh thái Python.
- **LIMIT inject** = **Hybrid (C)** — inject `LIMIT MAX_ROWS` (mặc định 1000, env `SQL_LIMIT_MAX`) khi thiếu; ghi note vào bucket `policy` (nhẹ, không fail) để feedback `gen_sql`.
- **SchemaArtifact storage** = **(C) ENV `SCHEMA_DIR` + default `ai_python/app/data/schema/`** (fallback in-package). Loader đọc `<schema_version>.yaml`.
- **Feedback bucket extras** = **(B) có `extras: dict | None`** — đồng bộ PRD Option C.
- **Module layout mới:**
  - `ai_python/app/graph/dbmeta.py` — `SchemaLoader` Protocol + `FileSchemaLoader` + Pydantic `SchemaArtifact` / `TableMeta`.
  - `ai_python/app/graph/feedback.py` — refine theo bucket dict (nếu Task 2 đã có scaffold thì upgrade, không break test cũ).
  - `ai_python/app/graph/nodes/{intent,chat_normal,sql_pipeline,summarize}.py` — thay implementation stub Task 2.
  - `ai_python/app/graph/validate_sql.py` — upgrade dùng `sqlparse` + LIMIT inject hybrid + allowlist từ DBM.
  - `ai_python/app/data/schema/v1.yaml` — fixture mẫu cho test.
  - `docs/ai-python/intent_registry_howto.md` — checklist thêm intent (REG-03).
- **Định danh role registry LLM** (đồng bộ ADR-001): `intent`, `chat`, `sql_review`, `gen_sql`, `summarize` — DEV có thể merge `intent` + `chat` về `default` nếu env không cấu hình riêng (fallback).

## 4. Hệ quả

- Thêm dependency: `sqlparse` (pin version); thêm `PyYAML` nếu Task 1/2 chưa có — pin rõ ràng trong dependency lock/requirements.
- `.env.example` thêm: `SCHEMA_DIR`, `SQL_LIMIT_MAX`, `LLM_ROLE_*` (DEV chốt cú pháp nếu mở rộng role registry).
- **Migration** từ Task 2 stubs: thay implementation, **không** đổi tên file/symbol công khai để không break test Task 2 (`tests/test_graph.py`); nếu cần đổi shape `validation_feedback` thì update test đồng thời.
- **Risk migration:** bucket feedback dict khác Task 2 nếu Task 2 đã dùng string/list — DEV verify và migrate test.
- **Token cost:** prompt `gen_sql` có thể dài hơn do feedback bucket — mitigate: template chỉ render bucket có nội dung (`if extras` và bucket non-empty).

## 5. NFR (5 mục)

1. **Hiệu năng:** AG-01 p95 < 50ms (mock LLM); AG-05 `validate_sql` parser p95 < 20ms; AG-07 `validate_result` p95 < 5ms (đo qua test fake LLM).
2. **Reliability:** Giữ `MAX_SQL_ATTEMPTS=3` (Task 2); empty result không retry (D4); fail bất kỳ nhánh nào → ghi bucket feedback trước khi route lại `gen_sql`.
3. **Bảo mật:** 100% `execute_sql` đi qua `validate_sql`; deny DDL/DML keyword bằng `sqlparse` token check; không leak schema bảng vào prompt `intent`; không tạo `ChatOpenAI` rải rác (ADR-001).
4. **Vận hành:** ENV mới `SCHEMA_DIR`, `SQL_LIMIT_MAX` trong `.env.example`; log mỗi node có `correlation_id` (Task 2 LG-13/14); `MASK_SQL=1` mask SQL trong log.
5. **Chi phí token:** Prompt `gen_sql` chỉ render bucket feedback có nội dung; AG-04 `sql_review` ưu tiên structured native (Task 1 LM-04) — fallback prompt-JSON với retry parse giới hạn ≤ 2; không double-summarize trong subgraph.
