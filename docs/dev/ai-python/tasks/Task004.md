# Task004 — Triển khai FastAPI gateway cho LangGraph + Gemma4 (Spring trust boundary)

**SRS:** `d:\do_an_tot_nghiep\project\docs\ai-python\srs\SRS_AI_Task004_langgraph-gemma4-task4-spring-fastapi.md`  
**Artifact folder:** `d:\do_an_tot_nghiep\project\docs\ai-python\task004\`

## Goal

- Triển khai lớp API FastAPI cho invoke + stream (SSE) theo SRS Task004, đảm bảo contract tương thích với Task1/2/3, bảo toàn context từ Spring trust boundary và duy trì canonical response envelope.

## Definition of Done

- [ ] BA✓ — SRS Task004 approved, scope và acceptance criteria chốt.
- [ ] TL✓ — Thiết kế API/integration đã được review, mapping FR/NFR rõ cho implementation.
- [ ] DEV✓ — Code + test contract invoke/stream pass, error mapping và auth/validation paths đạt yêu cầu SRS.
- [ ] CR✓ — Code review PASS và artifact review lưu tại `docs/task004/05-code-review/`.

**Tuỳ chọn pre-release:** AI_TESTER / AI_BRIDGE.

## Checklist triển khai (aligned SRS Task004)

### Phase 1 — API contracts & transport

- [ ] FR-API-01..02 — Expose `POST /api/v1/ai/chat/invoke` và `POST /api/v1/ai/chat/stream` (SSE only).
- [ ] FR-API-05..08 — Canonical success/error envelope cho invoke và terminal event guarantee cho stream.
- [ ] SRS §4.1..§4.6 — Request/response schema, error envelope, SSE event shape bám đúng contract.

### Phase 2 — Validation, context propagation, security

- [ ] FR-API-03..04 — Validate `X-Correlation-Id`, metadata bắt buộc (`user_id`, `tenant_id`), optional `thread_id`, `schema_version`.
- [ ] FR-CTX-01 — Forward `correlation_id`, `tenant_id`, `user_id`, `thread_id`, `schema_version` vào graph config/state.
- [ ] FR-SEC-01 — Enforce JWT/signed context tại biên FastAPI theo Option B trust boundary.

### Phase 3 — Compatibility & SQL execution posture

- [ ] FR-COMP-01 — Giữ compatibility với contracts Task1 (`LlmClient`), Task2 (graph/checkpointer/stream hooks), Task3 (agent behavior).
- [ ] FR-SQL-01 — Production SQL mode route qua Spring HTTP proxy (`http_spring`), mode direct DB chỉ non-prod constrained.
- [ ] SRS §4.7 + §5 — Boundaries integration và state/data shapes được wiring nhất quán.

### Phase 4 — NFR, testing, acceptance

- [ ] NFR-PERF/REL/SEC/OBS/COMP — Theo SRS §6 (latency, reliability, security, observability, compatibility).
- [ ] FR-TEST-01 + NFR-TEST-01 — Contract tests cho invoke/stream success + failure paths deterministic.
- [ ] SRS §7 — Acceptance Given/When/Then và checklist acceptance đạt trước khi đóng task.

