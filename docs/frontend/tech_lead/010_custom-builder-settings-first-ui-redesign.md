# Tech Spec - Custom Builder Settings-first UI Redesign

> Source SRS: `docs/frontend/srs/012_custom-builder-settings-first-ui-redesign.md`  
> Agent: TECH_SPEC_WRITER  
> Scope: Frontend UI only, Stage S1-S3  
> Readiness: READY_FOR_CODING

## Scope

Implement the Custom Builder as a settings-first experience at `/settings/custom-builder`.

- S1: Builder List Page is the first screen; no auto-selected mock page.
- S2: Create Interface Wizard with 5 clear steps.
- S3: Edit Interface Settings with section navigation and advanced placeholders collapsed/disabled.

Out of scope: backend, `ai_python`, real workflow, real connector, real inventory effect, real AI, runtime page rework beyond preserving existing mock runtime safety.

## Evidence

- SRS 012 supersedes SRS 010/011 for the primary UI flow.
- CodeGraph context identified:
  - `frontend/mini-erp/src/features/custom-builder/pages/CustomBuilderPage.tsx`
  - `frontend/mini-erp/src/features/custom-builder/api/customBuilderMockAdapter.ts`
  - `frontend/mini-erp/src/features/custom-builder/runtime/customMenuRuntime.ts`
  - `frontend/mini-erp/src/features/custom-builder/pages/CustomRuntimePage.tsx`

## Architecture Decision

Use the existing frontend fixture/mock adapter as the source of builder data and state. Components must not scatter mock arrays inside page JSX. The page can keep transient UI draft state, but catalog defaults, existing interfaces, menu folders, validation, create/save behavior, and sample bundles stay in the adapter.

## Implementation Slices

1. Builder list
   - Load list via mock adapter.
   - Provide search, status filter, loading, empty, error, pending action states.
   - Show table/list with name, parent menu, display type, field count, status, updated time, actions.

2. Create wizard
   - Five steps: basic info, menu location, data fields, display, review/save.
   - Each step owns only its form fields.
   - Side summary is collapsible and responsive.
   - Reference fields use canonical `reference` with `refType/refEntityKey`.

3. Edit settings
   - Section nav: overview, data, display, permissions, validation, advanced.
   - Advanced stays collapsed/disabled by default.
   - Publish disabled until validation passes.

## Files To Edit

- `frontend/mini-erp/src/features/custom-builder/api/customBuilderMockAdapter.ts`
- `frontend/mini-erp/src/features/custom-builder/pages/CustomBuilderPage.tsx`

Files to preserve unless needed for compatibility:

- `frontend/mini-erp/src/features/custom-builder/pages/CustomRuntimePage.tsx`
- `frontend/mini-erp/src/features/custom-builder/runtime/customMenuRuntime.ts`
- `frontend/mini-erp/src/components/shared/layout/Sidebar.tsx`

Forbidden:

- backend files
- `ai_python/**`

## UI Contracts

- Builder list must be the default view.
- Create action opens wizard; successful draft creation opens edit settings.
- Validation errors include a step/section and a jump action.
- Pending save/create/publish disables related actions.
- Empty state has one clear CTA.
- Advanced capabilities are visible only as collapsed/disabled placeholders.

## Horizontal Analysis

Risk areas checked:

- Earlier UI packed explorer, runtime preview, validation and permissions into one screen. New flow separates list, wizard, edit sections.
- Prior mock data mixed labels such as product/location references. New field UI should normalize to `reference`.
- Button contrast issues from primary defaults should be avoided on critical CTAs with explicit readable classes.
- Backend remains authoritative; frontend validation is guidance only.

## Test Handoff

Run:

- `npm run build` in `frontend/mini-erp`
- Browser/manual verification for desktop and mobile if Browser tool is callable.

P0 checks:

- `/settings/custom-builder` opens list/empty, not auto-selected editor.
- Wizard prevents invalid next/publish and preserves entered data.
- Edit settings has sections and advanced collapsed.
- No backend/`ai_python` changes.
