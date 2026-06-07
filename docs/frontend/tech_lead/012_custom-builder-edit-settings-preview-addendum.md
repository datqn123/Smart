# Tech Spec Addendum - Custom Builder Edit Settings + Lightweight Preview

> Source SRS: `docs/frontend/srs/012_custom-builder-settings-first-ui-redesign.md`  
> Base Tech Spec: `docs/frontend/tech_lead/010_custom-builder-settings-first-ui-redesign.md`  
> Agent: TECH_SPEC_WRITER  
> Scope: Frontend UI only, Stage S3-S4  
> Readiness: READY_FOR_CODING

## Goal

Continue the settings-first Custom Builder implementation by deepening:

- S3: Edit Interface Settings.
- S4: Lightweight table/form preview inside settings.

## Scope Boundary

Allowed:

- Improve edit sections for overview, data, display, permissions, validation, and advanced placeholders.
- Add sample-data preview in settings for table and form.
- Keep fixture/mock adapter as the source for sample records and draft persistence.

Forbidden:

- Backend changes.
- `ai_python` changes.
- Real workflow, connector, inventory, or AI behavior.
- Runtime page as the source of truth.

## Implementation Notes

- Edit settings should avoid many panels at once. Each section has one main task and optional preview area.
- Preview is a visual aid only. It must show sample data from the bundle and form controls in read-only/prototype mode.
- Advanced section stays collapsed/disabled by default.
- Publish remains disabled while validation errors or unsaved changes exist.
- Field key changes must keep view/form selections aligned.

## Files

Expected edits:

- `frontend/mini-erp/src/features/custom-builder/pages/CustomBuilderPage.tsx`
- `frontend/mini-erp/src/features/custom-builder/api/customBuilderMockAdapter.ts` only if sample preview helper/data is needed.

## Verification

- `npm run build`
- Browser/manual check if role can access builder.
- Confirm no backend/`ai_python` diff.
