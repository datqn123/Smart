# Tech Spec - Task001 Custom Interface Builder Backend Contract

> File: `docs/backend/task001/02-tech-lead/001_custom-interface-builder-task1-tech-spec.md`  
> Agent: TECH_SPEC_WRITER  
> Source SRS: `docs/backend/srs/003_custom-interface-builder-task1.md`  
> Ngay tao: 03/06/2026  
> Readiness: READY_FOR_CODING

---

## 1. Scope Decision

Implement Task 1 as a cross-layer MVP whose backend is the source of truth for custom interface/menu metadata.

In scope for coding:

- Spring API under `/api/v1/custom`.
- Flyway migration for custom menu metadata and permissions.
- JWT menu permission claim expansion.
- Frontend API wiring for existing prototype pages/sidebar/runtime.
- Focused backend and frontend tests where local patterns already exist.

Out of scope:

- Full custom entity/field/view/record engine.
- Workflow, connector, inventory effect.
- AI runtime changes under `ai_python/`.

Decision for SRS OQ:

| OQ | Decision for implementation |
| :--- | :--- |
| OQ-CI-01 | Staff gets `can_use_custom_entities=true`, but not `can_manage_custom_builder`. Runtime page visibility is still controlled by page roles/permissions. |
| OQ-CI-02 | Do not hard-lock key after publish in this MVP; protect with route uniqueness + etag. |
| OQ-CI-03 | Keep current frontend behavior: dynamic folders merge before Settings. |
| OQ-CI-04 | Archive endpoints may reject published children with a 409 instead of confirm token in MVP. |
| OQ-CI-05 | Publish does not require real custom entity table yet; it requires non-empty `entityKey`. Full entity existence check moves to Phase 1 entity foundation. |

---

## 2. CodeGraph Evidence

Commands used:

- `codegraph status --json`
- `codegraph impact "CustomBuilderPage" --json`
- `codegraph impact "MenuPermissionClaims" --json`
- `codegraph context "implement backend custom interface builder menu tree runtime menu runtime page permissions migrations frontend API integration" --format json`

Key files:

- `backend/smart-erp/src/main/java/com/example/smart_erp/auth/support/MenuPermissionClaims.java`
- `backend/smart-erp/src/main/resources/db/migration/*`
- `frontend/mini-erp/src/features/custom-builder/pages/CustomBuilderPage.tsx`
- `frontend/mini-erp/src/features/custom-builder/runtime/customMenuRuntime.ts`
- `frontend/mini-erp/src/features/custom-builder/pages/CustomRuntimePage.tsx`
- `frontend/mini-erp/src/components/shared/layout/Sidebar.tsx`
- `frontend/mini-erp/src/features/auth/types/menuPermissions.ts`
- `frontend/mini-erp/src/features/auth/lib/parseAccessTokenMenuPermissions.ts`

---

## 3. Architecture

### Backend

Package: `com.example.smart_erp.custominterface`

Suggested structure:

```text
custominterface/
  controller/CustomInterfaceController.java
  dto/*.java
  response/*.java
  repository/CustomInterfaceJdbcRepository.java
  service/CustomInterfaceService.java
```

Use existing project patterns:

- `ApiSuccessResponse<T>` envelope.
- `BusinessException(ApiErrorCode, message, details)` for domain errors.
- `JdbcTemplate` repository.
- `@PreAuthorize` with authorities from JWT `mp`.
- `@Transactional` in service.

### Frontend

Keep existing UI layout and make data source API-backed:

- Add `features/custom-builder/api/customInterfaceApi.ts`.
- Replace local `initialFolders` and `customRuntimeCatalog` as the main source of truth.
- Keep a small fallback runtime catalog only for dev/offline failure so static navigation remains safe.
- Use TanStack Query where app already uses it; otherwise use `useEffect` + `apiJson` for minimal integration.

---

## 4. Data Model

Migration name: next Flyway file after existing max. At time of this spec max visible is `V55`; use `V56__task001_custom_interface_builder.sql`.

Tables:

- `custom_menu_folders`
- `custom_menu_pages`
- `custom_menu_folder_versions`
- `custom_menu_page_versions`
- `custom_menu_events`

MVP simplification:

- Store visibility roles as JSONB array text.
- Store permissions as scalar columns for page: `entity_permission`, `data_permission`.
- Published version tables snapshot the current metadata on publish.
- `etag` can be deterministic: `folder-{key}-draft-{draft_version}` / `page-{key}-draft-{draft_version}`.

Seed:

- Owner/Admin: `can_manage_custom_builder=true`, `can_use_custom_entities=true`.
- Staff: `can_manage_custom_builder=false`, `can_use_custom_entities=true`.

Also update `MenuPermissionClaims.MENU_KEYS`, FE `MenuPermissions`, and FE parser key list.

---

## 5. API Contract

Base path: `/api/v1/custom`.

| Method | Path | Permission | Behavior |
| :--- | :--- | :--- | :--- |
| GET | `/menu-tree` | `can_manage_custom_builder` | Return draft/latest tree plus version metadata. |
| POST | `/menu-folders` | `can_manage_custom_builder` | Create folder draft. |
| PATCH | `/menu-folders/{folderKey}` | `can_manage_custom_builder` | Update folder with etag conflict guard. |
| POST | `/menu-pages` | `can_manage_custom_builder` | Create page draft. |
| PATCH | `/menu-pages/{pageKey}` | `can_manage_custom_builder` | Update page with etag conflict guard. |
| POST | `/menu/reorder` | `can_manage_custom_builder` | Persist folder/page sort order. |
| POST | `/menu/validate` | `can_manage_custom_builder` | Return validation summary, no mutation. |
| POST | `/menu/publish` | `can_manage_custom_builder` | Publish all valid draft items. |
| PATCH | `/menu-folders/{folderKey}/archive` | `can_manage_custom_builder` | Archive if no published children. |
| PATCH | `/menu-pages/{pageKey}/archive` | `can_manage_custom_builder` | Archive page. |
| GET | `/runtime-menu` | authenticated | Return published menu filtered for current user. |
| GET | `/pages/{pageKey}/runtime` | authenticated | Return published runtime page or safe 403/404. |

Optional for this coding pass:

- `/menu/preview` may return the same shape as `/runtime-menu` filtered by supplied role, or be omitted if not wired in UI.

---

## 6. Validation Rules

Use exact Vietnamese messages from the SRS where client-visible.

Common:

- `key`: required, regex `^[a-z0-9_]+$`, unique.
- `label`: required, max 160.
- `routePath`: required for page, starts with `/custom/`, unique.
- `entityKey`: required for publish, non-empty for page save.
- `pageType`: one of `record_list`, `form`, `table_detail`.
- `visibilityRoles`: allow `Owner`, `Admin`, `Staff`, `Warehouse`.
- `etag`: required for PATCH/reorder/publish when targeting existing tree.

Error status:

- 400 invalid input.
- 403 no authority.
- 404 missing folder/page/runtime page.
- 409 duplicate/conflict/stale etag.
- 422 validation failed on publish.

---

## 7. Implementation Slices

### Slice 1 - Permissions

Edit:

- `backend/.../auth/support/MenuPermissionClaims.java`
- `frontend/.../auth/types/menuPermissions.ts`
- `frontend/.../auth/lib/parseAccessTokenMenuPermissions.ts`
- migration seed.

Tests:

- Extend `MenuPermissionClaimsTest`.

### Slice 2 - Backend Metadata API

Add:

- DTO/response records.
- JDBC repository.
- service.
- controller.
- migration.

Tests:

- Service unit test for validation/etag if feasible.
- Controller/security test if existing setup supports it.
- At minimum run Maven test for touched auth tests and compile.

### Slice 3 - Frontend API Wiring

Add:

- `frontend/mini-erp/src/features/custom-builder/api/customInterfaceApi.ts`

Edit:

- `CustomBuilderPage.tsx`
- `customMenuRuntime.ts`
- `CustomRuntimePage.tsx`
- `Sidebar.tsx`

Behavior:

- Builder loads API tree.
- Save folder/page uses POST/PATCH depending on existing id/key.
- Publish calls backend and refetches.
- Runtime menu loads API asynchronously in Sidebar.
- Runtime page loads API by `pageKey`; keeps safe 403/404 UI.
- If runtime menu API fails, static menu must still render.

### Slice 4 - Verification

Run:

```powershell
cd backend/smart-erp; mvn -q -Dtest=MenuPermissionClaimsTest test
cd backend/smart-erp; mvn -q -DskipTests compile
cd frontend/mini-erp; npm run build
```

If the project lacks dependencies or local DB, record the blocker and run the closest compile/typecheck command possible.

---

## 8. Horizontal Analysis

| Scope | Risk | Handling |
| :--- | :--- | :--- |
| Auth/JWT | New permissions not included in `mp` cause frontend hidden menu and backend 403. | Update backend allowlist, FE type/parser, role seed, tests. |
| Error envelope | Raw validation/SQL errors leak to UI. | Throw `BusinessException` with Vietnamese messages and field details. |
| Dynamic menu | Runtime API failure could break static sidebar. | Sidebar custom menu load is optional and failure-safe. |
| Concurrency | Multiple Admin edits overwrite config. | Use `etag` on patch/reorder/publish. |
| Route collision | Custom page shadows static routes. | Require `/custom/` prefix and unique route. |
| Entity foundation missing | Publish blocked by missing `custom_entity_definitions`. | For Task 1 only require non-empty entityKey; future entity foundation tightens this. |
| AI | Metadata can become prompt injection later. | No AI code changes; keep label/description untrusted. |

---

## 9. Files To Edit

Backend:

- `backend/smart-erp/src/main/resources/db/migration/V56__task001_custom_interface_builder.sql`
- `backend/smart-erp/src/main/java/com/example/smart_erp/auth/support/MenuPermissionClaims.java`
- `backend/smart-erp/src/test/java/com/example/smart_erp/auth/support/MenuPermissionClaimsTest.java`
- `backend/smart-erp/src/main/java/com/example/smart_erp/custominterface/**`
- `backend/smart-erp/src/test/java/com/example/smart_erp/custominterface/**` if time permits.

Frontend:

- `frontend/mini-erp/src/features/auth/types/menuPermissions.ts`
- `frontend/mini-erp/src/features/auth/lib/parseAccessTokenMenuPermissions.ts`
- `frontend/mini-erp/src/features/auth/store/useAuthStore.ts`
- `frontend/mini-erp/src/features/custom-builder/api/customInterfaceApi.ts`
- `frontend/mini-erp/src/features/custom-builder/pages/CustomBuilderPage.tsx`
- `frontend/mini-erp/src/features/custom-builder/runtime/customMenuRuntime.ts`
- `frontend/mini-erp/src/features/custom-builder/pages/CustomRuntimePage.tsx`
- `frontend/mini-erp/src/components/shared/layout/Sidebar.tsx`

Docs:

- QA spec under `docs/backend/task001/03-qa/`.
- Code review under `docs/backend/task001/05-code-review/`.

---

## 10. Coding Guardrails

- Do not edit `ai_python/`.
- Do not remove existing mock data until API-backed fallback is in place.
- Do not implement SQL/script execution, dynamic endpoint generation, or physical table creation.
- Keep publish transactional.
- Keep runtime endpoints read-only.
- Use ASCII for new code comments/docs unless file already contains Vietnamese text.

Handoff: `READY_FOR_CODING`.
