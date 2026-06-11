# Custom Builder MVP Design

## Status

Approved direction: metadata-first MVP production.

Date: 2026-06-11

## Background

The current custom-builder frontend has a convincing UI shell, but the main builder and runtime flows are backed by frontend fixtures. `CustomBuilderPage` loads and saves through `customBuilderMockAdapter`, publish intentionally returns a mock conflict, and `CustomRuntimePage` renders sample records instead of persisted data. The backend already has a useful foundation for custom menu folders/pages, publish state, runtime menu filtering, role/permission checks, and optimistic etags, but it does not yet persist custom entity fields, views, per-entity permissions, or runtime records.

This design turns the feature into a production MVP without attempting a full no-code automation engine.

## Goals

1. Admins with `can_manage_custom_builder` can create, edit, validate, save draft, and publish a custom page backed by persisted metadata.
2. Runtime users with `can_use_custom_entities` and the page-specific permissions can see published custom pages in the sidebar.
3. Published custom pages render real table/form UI from backend metadata.
4. Runtime users can create, view, update, delete, search, and paginate records for a published custom entity.
5. Backend is the source of truth for metadata, validation, publish state, and record data.
6. Existing custom menu folder/page behavior is preserved and extended rather than replaced wholesale.

## Non-Goals

1. Workflow execution is not part of MVP.
2. Logic connector execution is not part of MVP.
3. Inventory effects, stock movements, financial posting, and AI copilot actions are not part of MVP.
4. Arbitrary SQL/table creation per custom entity is not part of MVP.
5. Advanced report builder, formulas, dashboards, and cross-entity joins are not part of MVP.
6. Public unauthenticated access to custom pages is not part of MVP.

## MVP Scope

The MVP supports these field types:

- `text`
- `long_text`
- `number`
- `money`
- `date`
- `boolean`
- `single_select`
- `reference`

Reference fields support an allowlist of core targets:

- `products`
- `suppliers`
- `customers`
- `inventory_locations`
- `users`

Runtime records are stored as JSONB values keyed by field key. This gives a production path without schema churn for each custom entity. Backend validation enforces required fields, supported field types, select options, reference target allowlist, and basic value shape.

## Architecture

Backend owns custom-builder state. Frontend becomes a metadata editor and runtime renderer.

The existing `custom_menu_folders` and `custom_menu_pages` tables remain the navigation layer. New custom entity tables hang off `custom_menu_pages.entity_key`. Publish snapshots the entity metadata so runtime pages are stable and only read published definitions. Draft metadata can change without affecting already published runtime pages.

At runtime, the frontend first loads the published page bundle from backend. That bundle contains the page node, entity definition, fields, list view, form layout, permissions, and the current published version. The records API then reads and writes `custom_records` for that entity.

## Backend Data Model

### `custom_entities`

Stores one draft entity definition per custom entity.

Important columns:

- `id`
- `entity_key`
- `label`
- `description`
- `status`: `Draft`, `NeedsConfig`, `Published`, `Hidden`
- `draft_version`
- `published_version`
- `etag`
- `created_by`, `updated_by`
- `created_at`, `updated_at`, `published_at`, `archived_at`

### `custom_entity_fields`

Stores draft field definitions.

Important columns:

- `id`
- `entity_key`
- `field_key`
- `label`
- `field_type`
- `required`
- `filterable`
- `sortable`
- `searchable`
- `order_index`
- `helper_text`
- `options_json`
- `reference_json`
- `validation_json`
- `default_value_json`
- `status`: `Active`, `Draft`, `Archived`
- `created_at`, `updated_at`

### `custom_entity_views`

Stores draft view configuration.

Important columns:

- `id`
- `entity_key`
- `list_columns_json`
- `filter_fields_json`
- `default_sort`
- `form_sections_json`
- `updated_at`

### `custom_entity_permissions`

Stores draft action permissions.

Important columns:

- `id`
- `entity_key`
- `action`: `view`, `create`, `update`, `delete`
- `roles_json`

### `custom_entity_versions`

Stores immutable published snapshots.

Important columns:

- `id`
- `entity_key`
- `version`
- `page_key`
- `entity_snapshot_json`
- `fields_snapshot_json`
- `views_snapshot_json`
- `permissions_snapshot_json`
- `published_by`
- `published_at`

### `custom_records`

Stores runtime records for published custom entities.

Important columns:

- `id`
- `entity_key`
- `published_version`
- `values_json`
- `state`: default `Active`
- `created_by`, `updated_by`, `deleted_by`
- `created_at`, `updated_at`, `deleted_at`

Indexes:

- `(entity_key, deleted_at)`
- `(entity_key, created_at DESC)`
- GIN on `values_json` for MVP search containment where useful

## Backend API Contract

### Builder Metadata

`GET /api/v1/custom/builder/menu-tree`

Returns draft menu tree plus summary counts for custom entities.

`GET /api/v1/custom/builder/pages/{pageKey}/bundle`

Returns editable draft bundle:

- `menuPage`
- `entityDefinition`
- `fields`
- `views`
- `permissions`
- `validationSummary`
- `etag`

`POST /api/v1/custom/builder/pages`

Creates menu page, entity definition, default fields/view/permissions in one transaction.

`PATCH /api/v1/custom/builder/pages/{pageKey}/bundle`

Updates page metadata, entity metadata, fields, views, and permissions in one transaction. Requires current etag.

`POST /api/v1/custom/builder/pages/{pageKey}/validate`

Runs backend validation and returns `ValidationSummaryData`.

`POST /api/v1/custom/builder/pages/{pageKey}/publish`

Requires current etag. Runs validation, snapshots metadata into `custom_entity_versions`, marks menu page/entity as `Published`, and updates published version.

### Runtime Metadata

`GET /api/v1/custom/runtime-menu`

Returns only published folders/pages visible to the authenticated user. Existing role and permission filtering remain enforced.

`GET /api/v1/custom/pages/{pageKey}/runtime`

Returns published runtime bundle for a visible page:

- page metadata
- published entity definition
- published fields
- published views
- published permissions
- version

### Runtime Records

`GET /api/v1/custom/pages/{pageKey}/records?page=&size=&search=`

Returns paginated records for the published page. Search is MVP text search over searchable fields converted to string.

`POST /api/v1/custom/pages/{pageKey}/records`

Creates a record after checking create permission and validating request values against published fields.

`GET /api/v1/custom/pages/{pageKey}/records/{recordId}`

Returns one record if the user can view the page.

`PATCH /api/v1/custom/pages/{pageKey}/records/{recordId}`

Updates values after checking update permission and backend validation.

`DELETE /api/v1/custom/pages/{pageKey}/records/{recordId}`

Soft deletes a record after checking delete permission.

## Validation Rules

Builder validation:

- Page route must start with `/custom/`.
- Page key, entity key, and field keys use lowercase letters, numbers, and underscores.
- Field keys are unique inside an entity.
- Entity must have at least one active field.
- List view must have at least one column.
- List columns must reference existing active fields.
- Required active fields must appear in the form layout.
- `single_select` fields require at least one non-empty unique option.
- `reference` fields require `refType` and an allowed `refEntityKey`.
- Published pages cannot reference archived fields in views.

Runtime record validation:

- Required fields must be present and non-empty.
- Number and money fields must parse as finite numbers.
- Date fields must be ISO date strings.
- Boolean fields must be booleans.
- Single-select values must match configured options.
- Unknown field keys are rejected.
- Read-only and archived fields are ignored on write.

## Frontend Design

### API Layer

`frontend/mini-erp/src/features/custom-builder/api/customInterfaceApi.ts` becomes the production API client for:

- builder menu tree
- builder page bundle
- save draft
- validate
- publish
- runtime bundle
- runtime records

`customBuilderMockAdapter.ts` is removed from app runtime imports. It can remain only for isolated tests during migration, or be deleted once tests have API mocks.

### Builder Page

`CustomBuilderPage.tsx` keeps the existing UI structure but swaps data source and side effects:

- list loads from `getBuilderMenuTree`
- editor loads from `getBuilderPageBundle`
- create calls backend create page API
- save draft calls patch bundle API
- publish calls backend publish API
- validation errors from backend are mapped to existing section panels
- mock copy such as "fixture", "Mock 409", and "Backend: không sửa" is removed

Advanced UI sections for workflow, logic connector, inventory effect, and AI are hidden or disabled for MVP with clear non-production labels.

### Runtime Page

`CustomRuntimePage.tsx` becomes a real generic renderer:

- loads runtime bundle from backend
- loads records page from backend
- search triggers records reload
- selecting a row loads detail locally from current page result or by record API
- create calls POST records
- edit calls PATCH records
- delete calls DELETE records
- after mutation, list reloads and toasts show backend result

Client validation remains lightweight; backend errors are displayed as field errors or toast details.

### Sidebar

`Sidebar.tsx` keeps loading `/api/v1/custom/runtime-menu`. Fixture fallback is removed from production code. A development-only fallback is allowed only when `import.meta.env.DEV && VITE_USE_CUSTOM_BUILDER_FIXTURE === "true"`.

## Security

Backend authorization is mandatory. Frontend visibility is not a security boundary.

Required checks:

- Builder APIs require `can_manage_custom_builder`.
- Runtime menu requires `can_use_custom_entities` or `can_manage_custom_builder`.
- Runtime page access checks folder status, page status, role visibility, entity permission, and data permission.
- Record APIs additionally check per-entity action permissions from the published snapshot.
- Runtime queries never accept arbitrary SQL, column names, or table names from the client.
- JSONB field access is built from server-side published metadata only.

## Error Handling

Backend returns existing envelope shape with `ApiSuccessResponse` and structured `BusinessException` errors.

Important cases:

- 400 for invalid request shape or invalid field values.
- 403 for missing action permission.
- 404 for unpublished, hidden, or missing page/record.
- 409 for stale etag or duplicate key/route.
- 422 for publish validation failure.

Frontend behavior:

- 409 prompts reload before saving again.
- 422 opens validation panel and highlights blocking sections.
- 403 shows a no-permission state.
- 404 shows "Không tìm thấy giao diện tùy chỉnh".
- Record mutation errors preserve form draft values.

## Migration Strategy

1. Add new tables without removing existing custom menu tables.
2. Backfill one entity for the existing `phieu_kiem_hang_hong` published page.
3. Keep existing menu API stable while adding builder bundle APIs.
4. Switch frontend builder to real APIs behind normal code path.
5. Switch runtime page to real runtime bundle and records APIs.
6. Remove production imports of `customBuilderMockAdapter`.

## Testing Strategy

Backend:

- Repository tests for metadata persistence, version snapshots, record CRUD, soft delete.
- Service tests for builder validation and runtime record validation.
- WebMvc tests for builder authorization, publish validation, runtime menu filtering, and record action permissions.

Frontend:

- API mapping tests for builder bundle and runtime records.
- Component tests for builder validation display and publish/save flows with mocked API responses.
- Component tests for runtime create/edit/delete behavior.
- Sidebar test for runtime menu from backend response.

E2E:

- Login as authorized admin.
- Create a custom page with fields and view.
- Save draft.
- Publish.
- Confirm page appears in sidebar.
- Open runtime page.
- Create a record.
- Reload page.
- Confirm record persists.

## Rollout Criteria

MVP is considered complete when:

1. No production app code imports `customBuilderMockAdapter`.
2. A custom page can be created, saved, published, opened from sidebar, and used to persist records.
3. Runtime data survives browser reload and server restart.
4. Backend rejects invalid records and unauthorized actions.
5. Frontend typecheck passes.
6. Targeted backend and frontend tests for custom-builder pass.
7. Existing custom menu permissions continue to work for Owner/Admin/Staff role differences.

## Open Decisions Resolved For MVP

- Record storage uses JSONB, not generated physical tables.
- Runtime reads published snapshots, not mutable draft metadata.
- Workflow and logic connector UI are not active in MVP.
- Reference fields use a fixed allowlist.
- Existing menu folder/page tables remain the navigation source.
