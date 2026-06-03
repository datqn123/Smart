# Code Review - Custom Interface Builder Task 1

## Scope

- Source SRS: `docs/backend/srs/003_custom-interface-builder-task1.md`
- Tech spec: `docs/backend/task001/02-tech-lead/001_custom-interface-builder-task1-tech-spec.md`
- QA spec: `docs/backend/task001/04-tester/001_custom-interface-builder-task1-test-plan.md`
- Review target: backend custom interface API, migration, JWT menu permissions, frontend builder/runtime wiring.

## CodeGraph

- Ran `codegraph status --json` before workflow discovery.
- Ran `codegraph impact`, `codegraph context`, and `codegraph affected` during planning and implementation discovery.
- Ran `codegraph sync` after implementation patches.
- Final review impact focused on `CustomInterfaceService`, `CustomInterfaceController`, sidebar/runtime builder consumers, and auth menu permission parsing.

## Findings

No blocking findings remain after review fixes.

Issues found during review and fixed before completion:

- PostgreSQL uniqueness checks no longer use nullable `? IS NULL` parameters. Repository methods now split null and non-null `exceptId` paths to avoid runtime parameter type inference failures.
- Publish and reorder now validate the submitted tree ETag before mutation, matching the SRS conflict handling requirement.
- Tree ETag now reflects node key, status, order, route, and node ETag instead of only a draft version sum.
- Frontend builder nodes now keep `originalKey`, so renaming a folder or page still PATCHes the existing backend record instead of calling the endpoint with the unsaved new key.

## Verification

- `backend/smart-erp`: `.\mvnw.cmd -q -Dtest=MenuPermissionClaimsTest test` passed.
- `backend/smart-erp`: `.\mvnw.cmd -q -DskipTests compile` passed.
- `frontend/mini-erp`: `npm run build` passed.

## Residual Risk

- No live browser smoke test was run against a seeded local database in this review pass.
- Backend custom interface endpoints currently have compile coverage and permission-claim unit coverage, but not controller/repository integration tests against PostgreSQL.
- Vite reports an existing chunk-size warning after production build; it is not introduced by this task's API/runtime wiring.
