# Code Review — Task003
- Reviewer: AI_CODE_REVIEWER (driver resume)
- Branch: `feature/ai-task003`
- Implementation commit: `b63fce1` · Branch tip (incl. this review bundle): `feature/ai-task003` (`git rev-parse HEAD`)
- Iteration: 1

## Summary
- Block: 0
- Major: 0
- Minor: 1
- Info: 2
- Verdict: **PASS**

## Issues

### [Minor] CR-1 — Legacy GET `/v1/chat/stream` dùng event `delta`/`done` (không khớp vocabulary Design §4 đầy đủ)
- File: `ai_python/app/main.py`
- Rule: Design §4 SSE names cho chat thống nhất
- Evidence: Endpoint cũ emit `event: delta`; Task003 dùng envelope JSON qua `task003_router` (`token`, `tool_*`, `error`, `done`).
- Fix suggestion: Deprecated doc hoặc align sau; không chặn slice Task003 vì entry mới là `POST /v1/task003/stream`.

### [Info] CR-2 — OpenAI/MKP I/O không bọc try/except trong `mkp_async` mọi nhánh
- Ghi chú: entry `Task003Orchestrator.stream_turn` có map lỗi ra SSE `error`; chấp nhận.

### [Info] CR-3 — Conventional commits
- Commit Task003: `feat(ai_python): Task003 RAG-first ...` — khớp guideline.

## Checklist
- [x] 3.1 Coding rules — `ruff` / `mypy` clean; no `print`; no hardcoded secrets
- [x] 3.2 Design conformance — read slice; không mutation; MCP read-only abstraction
- [x] 3.3 SRS conformance — tests reference AC/policy/SSE trong `tests/`
- [x] 3.4 ADR conformance — MKP env; layer structure
- [x] 3.5 Perf & security — scripted MCP trong test; correlation_id trong flow
