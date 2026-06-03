# Test Plan - Task001 Custom Interface Builder

> File: `docs/backend/task001/04-tester/001_custom-interface-builder-task1-test-plan.md`  
> Agent: QA_SPEC_WRITER  
> Source SRS: `docs/backend/srs/003_custom-interface-builder-task1.md`  
> Tech Spec: `docs/backend/task001/02-tech-lead/001_custom-interface-builder-task1-tech-spec.md`  
> Ngay tao: 03/06/2026  
> Readiness: QA_READY_FOR_CODING

---

## 1. CodeGraph Evidence

Commands used:

- `codegraph affected backend/smart-erp/src/main/java/com/example/smart_erp/auth/support/MenuPermissionClaims.java frontend/mini-erp/src/features/custom-builder/pages/CustomBuilderPage.tsx frontend/mini-erp/src/features/custom-builder/runtime/customMenuRuntime.ts frontend/mini-erp/src/components/shared/layout/Sidebar.tsx --json`
- `codegraph context "QA custom interface builder backend api permissions runtime menu etag publish frontend sidebar runtime page" --format json`

Result:

- No affected tests detected automatically.
- Manual test scope must cover auth claim, backend API, runtime resolver, and frontend build.

---

## 2. P0 Verification Matrix

| ID | Scope | Case | Expected |
| :--- | :--- | :--- | :--- |
| P0-01 | Auth | `MenuPermissionClaims` parses `can_manage_custom_builder` and `can_use_custom_entities` | Both keys appear in `mp` map and authorities when true |
| P0-02 | Migration | Role seeds include new permissions | Owner/Admin true for both; Staff false/true as Tech Spec |
| P0-03 | Backend API | Admin creates folder and page | 2xx envelope, draft version/etag returned |
| P0-04 | Backend API | Staff calls builder write endpoint | 403 |
| P0-05 | Validation | Invalid key or route | 400 with field details |
| P0-06 | Conflict | Duplicate page key or stale etag | 409 business message |
| P0-07 | Publish | Publish valid draft | Published version created; runtime menu includes page |
| P0-08 | Runtime | User without page permission | Runtime page 403 or filtered from menu, no sensitive metadata |
| P0-09 | Frontend | Sidebar runtime API fails | Static menu still renders |
| P0-10 | Frontend | Build/typecheck | `npm run build` passes |

---

## 3. P1 Regression Matrix

| ID | Scope | Case | Expected |
| :--- | :--- | :--- | :--- |
| P1-01 | Builder UI | Empty API tree | User can create folder, create page disabled until folder exists |
| P1-02 | Builder UI | Save pending | Buttons disabled while request pending |
| P1-03 | Runtime route | Unknown `pageKey` | In-app 404 safe state |
| P1-04 | Runtime route | Existing page with warnings | Runtime preview still shows warnings safely |
| P1-05 | Archive | Folder with published child | 409 or impact rejection |
| P1-06 | Reorder | Reorder pages | Server order reflected after refetch |
| P1-07 | Auth refresh | API 401 from custom endpoints | Existing `apiJson` refresh path remains used |

---

## 4. Backend Test Notes

Required focused tests:

- Extend `MenuPermissionClaimsTest`.
- Add service-level tests for:
  - duplicate/invalid key validation,
  - stale etag,
  - publish creates runtime-visible snapshots,
  - runtime permission filtering.

Acceptable fallback if repository integration tests are too heavy in this pass:

- Run `mvn -q -Dtest=MenuPermissionClaimsTest test`.
- Run `mvn -q -DskipTests compile`.
- Manually inspect controller annotations and service validation paths.

---

## 5. Frontend Test Notes

Required verification:

- `npm run build`.
- Manual route smoke when dev server is available:
  - `/settings/custom-builder`
  - `/custom/phieu_kiem_hang_hong`
  - `/custom/not_found`

Runtime failure simulation:

- Make `GET /api/v1/custom/runtime-menu` reject or return 403.
- Sidebar must keep static items and not crash.

---

## 6. Failure Modes

| Failure | Detection |
| :--- | :--- |
| Permission key missing in JWT | P0-01, backend compile/test |
| Raw SQL/stack error leaks | API error tests/manual response inspection |
| Mock and API type drift | Frontend build |
| Runtime reads draft data | Publish/runtime service tests |
| Staff sees builder | Sidebar/menu permission and backend 403 tests |
| Entity foundation absent blocks Task 1 | Publish accepts non-empty `entityKey` in MVP |

---

## 7. AI Agentic Scope

Not in scope for coding. No LangGraph/Harness/tool tests are required. Preserve architecture boundary for future AI phases:

- LangGraph: orchestration only.
- Harness: deterministic validation/execution.
- Tools: scoped Spring integrations.

---

## 8. Readiness

QA readiness: `QA_READY_FOR_CODING`.

The Coding Agent may proceed. Minimum verification must include backend permission tests, backend compile, and frontend build. If any cannot run, report the exact command and failure.
