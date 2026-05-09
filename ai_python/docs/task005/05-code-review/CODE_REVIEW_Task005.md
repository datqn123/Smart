# Code Review — Task005
- Reviewer: AI_CODE_REVIEWER
- Task / nhãn branch (từ `Task005.md`): `db_rag_agent_context` — `feature/ai-task005`
- HEAD / commit: `ac05124` (`feature/ai-task005` vs `develop`; prior iteration `9d5dafd`)
- Iteration: 2

## Summary
- Block: 0
- Major: 0
- Minor: 1
- Info: 3
- Verdict: **PASS**

**Re-review scope:** Sau commit `ac05124` (*test(ai-python): Task005 AC traceability and SRS §10 JSON fixtures*) — đóng **CR-001**, **CR-002** (iteration 1).

**Auto-advance (G-AI-CR):** Có — 0 Block, 0 Major chưa giải quyết (WORKFLOW_RULE §2 `G-AI-CR`).

**Security (secrets):** Không phát hiện secret/API key hardcode trong `ai_python/app/`; pattern grep `sk-` / `Bearer ` / `api_key="` trong app không có.

## Resolved (iteration 1 → 2)

### ~~[Major] CR-001~~ — SRS §7 AC traceability
- **Status:** Resolved in `ac05124`.
- **Evidence:** `# AC: AC1` … `# AC: AC6` xuất hiện trên các file test Task005 (`integration/` + `unit/`); mỗi AC có ≥1 tham chiếu.

### ~~[Major] CR-002~~ — SRS §10 sample JSON → fixtures
- **Status:** Resolved in `ac05124`.
- **Evidence:** `ai_python/tests/fixtures/task005/*.json` (describe request/response, query_readonly request/response, `health_artifact.json`, `mcp_tool_error.json`, registry JSON); integration tests load qua `pathlib` thay vì inline toàn bộ payload SRS §10.2.

## Issues

### [Minor] CR-003 — Metadata audit MCP SRS §4 chưa hiện trên client surface
- File: `ai_python/app/mcp/db_readonly_port.py`, `app/mcp/task005_unconfigured_client.py`
- Rule: SRS §4 / ADR-003 — audit `user_id`, `session_id`, `high_level_args` (redact) kèm `correlation_id`.
- Evidence: Port chỉ nhận `SqlDescribeIn` / `SqlQueryReadonlyIn`; không có trường session/user trên boundary Python (có thể do transport adapter tương lai). Logging app có `correlation_id` trên `describe.*` / `smoke.*` / `run.*`.
- Fix suggestion: Khi nối MCP thật, mở rộng adapter để gửi audit fields cố định (`batch_corpus_job`, `job_run_id`) hoặc document “do MCP layer” trong README Task005.

### [Info] CR-004 — Conventional Commits trong phạm vi diff
- Rule: AI_CODE_REVIEWER §3.1
- Evidence: `ac05124` dùng prefix `test(ai-python):` — khớp Conventional Commits.

### [Info] CR-005 — Module `smart_erp_mcp/chat_reply.py` ngoài slice Task005 batch
- File: `ai_python/app/smart_erp_mcp/chat_reply.py`
- Rule: SRS §1 scope (batch corpus là primary)
- Evidence: Helper format chat text + unit test; không vi phạm read-only DB; không chặn G-AI-CR cho slice batch.

### [Info] CR-006 — Prompt injection / RAG chunk vs LLM
- Rule: WORKFLOW_RULE §3 / CR §3.5 (Prompt injection guard)
- Evidence: `task005_ingest` chỉ chunk artifact schema/health; không có gọi LLM consume chunk trong slice này. Rủi ro injection là giai đoạn Chat Agent sau — ghi nhận cho BRIDGE/TST sau.

## Checklist
- [x] 3.1 Coding rules — `ruff check app/ tests/` pass; `mypy app/` pass; không `print(` trong `app/`; không hardcoded secret trong pattern CR; logging qua `get_logger` / `log_event`.
- [x] 3.2 Design conformance — Task005 v1 batch/CLI: không áp Chat Agent mutation/SSE runtime; `CorpusJobContext` trong `app/contracts/task005.py`; MCP I/O pydantic khớp SRS §4; không phát hiện mutation từ chat path trong scope Task005.
- [x] 3.3 SRS conformance — AC1–AC6 có `# AC:` trong tests; mẫu MCP/artifact §10.2 có fixture JSON; logic pipeline khớp AC (describe + smoke summary-only + RAG namespaces + exit policy + `correlation_id`).
- [x] 3.4 ADR conformance — Không bắt buộc LLM cho pipeline chính; caps (`MAX_*`) khớp SRS; layer hợp lý; env MKP theo ADR khi dùng.
- [x] 3.5 Perf & security — Không Excel/signed URL trong slice; artifact không persist full rows; không scope `backend/`/`frontend/`.

## Machine checks (record) — iteration 2

| Check | Result |
| :--- | :--- |
| `ruff check app/ tests/` | Pass |
| `mypy app/` | Pass |
| `pytest` | Pass (57 tests) |
