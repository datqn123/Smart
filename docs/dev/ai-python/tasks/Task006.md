# Task006 — SQL DB Metadata Production

**SRS:** `d:\do_an_tot_nghiep\project\docs\ai-python\srs\SRS_AI_Task006_sql-dbmeta-production.md`  
**Artifact folder:** `d:\do_an_tot_nghiep\project\docs\ai-python\task006\`

## Goal

- Triển khai Phase 1 production SQL executor theo hướng `http_spring` trong `ai_python/`, giữ `python_ro` ở trạng thái deferred rõ ràng, đồng thời bổ sung workflow CLI scan/validate DB metadata YAML tương thích runtime loader hiện tại.

## Definition of Done

- [x] BA✓ — SRS Task006 approved, scope và acceptance criteria đã chốt.
- [x] TL✓ — Thiết kế executor/config/metadata CLI được review, mapping FR/NFR rõ cho implementation.
- [x] DEV✓ — Code + pytest cho executor factory, HTTP mapping, read-only safety, row/timeout limits, metadata validation và docs đạt yêu cầu SRS.
- [x] CR✓ — Code review PASS và artifact review lưu tại `docs/task006/05-code-review/`.

**Tuỳ chọn pre-release:** AI_TESTER / AI_BRIDGE nếu cần kiểm tra release hoặc handoff tích hợp Spring.

## Checklist triển khai (aligned SRS Task006)

### Phase 1 — Executor contract & factory config

- [ ] FR-EXEC-01..03 — Chuẩn hoá result/error contract và triển khai `http_spring` là production executor Phase 1.
- [ ] FR-EXEC-04..05 — `python_ro` fail-fast với message deferred; factory validate mode, env, timeout, row limits.
- [ ] SRS §4.1 + §4.3 — Graph-facing executor behavior và env contract giữ tương thích runtime hiện tại.

### Phase 2 — SQL safety & Spring HTTP mapping

- [ ] FR-SAFE-01..03 — Reject DDL/DML/transaction/multi-statement trước dispatch và enforce row-limit boundary.
- [ ] FR-HTTP-01..03 — HTTP request/response mapping cho Spring success, policy/auth/upstream/timeout/malformed failures.
- [ ] NFR-ERR-01 + NFR-OBS-01 — Error/log feedback không lộ secrets và có metadata observability cần thiết.

### Phase 3 — DB metadata CLI workflow

- [ ] FR-META-01..04 — Validate YAML schema, scan CLI tạo artifact, validate CLI dùng được cho CI/deploy/manual workflow.
- [ ] SRS §5.3 — Artifact giữ compatibility với runtime loader và cho phép future-safe fields.
- [ ] NFR-META-01 + NFR-START-01 — Metadata freshness workflow rõ ràng; runtime fail-fast khi YAML thiếu/invalid.

### Phase 4 — Docs, tests, and acceptance

- [ ] FR-DOC-01 — Cập nhật operator docs và `.env.example` cho modes, env vars, commands, Spring handoff, `python_ro` deferred.
- [ ] FR-TEST-01 + NFR-REL-01 — Pytest coverage cho factory, HTTP executor, safety, limits, timeout, metadata validation, no-secret errors.
- [ ] AC-EXEC/SAFE/HTTP/META/DOC/SCOPE — Acceptance criteria SRS §7 đạt trước khi đóng task.

