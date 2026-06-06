# Tech Spec 019 — Custom Builder UX Improvements

## Scope

Implement SRS-016 in the frontend Custom Builder settings page only.

Target file:
- `frontend/mini-erp/src/features/custom-builder/pages/CustomBuilderPage.tsx`

Out of scope:
- backend
- `ai_python`
- mock adapter data/types
- save/publish behavior changes
- inventory, connector runtime, or AI integrations

## CodeGraph Evidence

CodeGraph preflight:
- `codegraph status --json`: initialized, no pending changes
- `codegraph context "Custom Builder UX improvements sticky edit nav per-tab dirty indicator logic connector wizard step indicator CustomBuilderPage" --format json`
- `codegraph query "EditInterfaceSettings" --json`
- `codegraph query "LogicConnectorBuilder" --json`

Relevant symbols:
- `EditInterfaceSettings` in `CustomBuilderPage.tsx`
- `LogicConnectorBuilder` in `CustomBuilderPage.tsx`

## Implementation Plan

### IMP-A Sticky Edit Navigation

Update the edit settings layout only:
- Add `xl:sticky xl:top-4` to the left section nav.
- Add `xl:sticky xl:top-4` to the right validation/preview aside.

Expected behavior:
- Sticky behavior applies only on `xl` screens and larger.
- Smaller breakpoints keep the current stacked flow.

### IMP-B Per-Tab Dirty Indicator

Inside `EditInterfaceSettings`:
- Add `dirtySections: Set<EditSection>` local state.
- Add a local `handleChange` wrapper around the existing `onChange` prop.
- `handleChange` records the currently active edit section before delegating to parent `onChange`.
- Clear `dirtySections` when the parent `dirty` flag becomes false after save.
- Replace edit-setting `onChange((current) => ...)` calls inside `EditInterfaceSettings` with `handleChange((current) => ...)`.
- Render a small amber dot on section nav buttons whose key exists in `dirtySections`.

Notes:
- This is section-level UI state only.
- It does not change save payloads or validation rules.
- Programmatic tab switching does not mark sections dirty.

### IMP-C Connector Wizard Step Indicator

Inside `LogicConnectorBuilder`, when a rule is selected:
- Render a compact step row after the wizard subtitle and before the four select controls.
- Steps: `1. Trigger`, `2. Source`, `3. Operation`, `4. Target`.
- Add trailing helper text that Review below shows the result.

Notes:
- Visual-only change.
- Does not alter selected rule state, dry-run logic, or connector validation.

## Risks

- `handleChange` must be used only for user-edit operations inside `EditInterfaceSettings`; replacing unrelated local state setters would create false dirty dots.
- Dirty dot reset depends on the existing parent `dirty` prop becoming false after save.
- Sticky elements require the existing scroll container to remain unchanged.

## Verification

Run:
- `npx eslint src/features/custom-builder/pages/CustomBuilderPage.tsx`
- `npx tsc --noEmit`

Manual/browser checks:
- Edit mode: scroll down on desktop width and verify left nav and right aside remain visible.
- Change one field in each tab and verify only that tab gets an amber dot.
- Save draft and verify all dots clear.
- Advanced tab: open Logic Connector and verify the step indicator appears above the four selects.
- Mobile width: verify no horizontal overflow and no forced sticky side panels.
