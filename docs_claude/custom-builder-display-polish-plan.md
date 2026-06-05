# Custom Builder Display Polish Plan

## Goal

Finish the Custom Builder Display tab polish after Stage 015 by adding list column configuration, default sort/filter controls, and a basic multi-section form builder without touching backend or `ai_python`.

## Files

- Modify `frontend/mini-erp/src/features/custom-builder/api/customBuilderMockAdapter.ts`
  - Allow `currency` as a display format.
  - Add validation for default sort and filter field references.
- Modify `frontend/mini-erp/src/features/custom-builder/pages/CustomBuilderPage.tsx`
  - Add display tab controls for column width, align, format.
  - Add default sort and filter field controls.
  - Add form section add/remove/reorder/rename and field membership controls.

## Steps

1. Extend adapter types and validation.
2. Add small UI helpers for field lookup and display defaults.
3. Replace the current two-card Display tab with settings-first sections:
   - Table columns
   - Default sort and filters
   - Form sections
   - Preview
4. Preserve existing mock adapter structure and runtime safety.
5. Run:
   - `npm run lint`
   - `npm run build`
   - Browser verification desktop and mobile
6. Review scope:
   - No backend changes
   - No `ai_python` or `AGENTS` changes
   - Validation errors still appear in `Kiem tra`
