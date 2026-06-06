# QA Spec 020 — Custom Builder UX Improvements

## Scope

Validate SRS-016 frontend-only UX improvements for Custom Builder settings.

Target:
- `frontend/mini-erp/src/features/custom-builder/pages/CustomBuilderPage.tsx`

Do not validate backend persistence, `ai_python`, inventory effects, or real connector execution.

## Automated Checks

1. `npx eslint src/features/custom-builder/pages/CustomBuilderPage.tsx`
   - Expected: zero errors.

2. `npx tsc --noEmit`
   - Expected: zero TypeScript errors.

## Manual Test Cases

### TC-01 Sticky Nav Desktop

Steps:
1. Open `/settings/custom-builder`.
2. Open an existing interface in edit/settings mode.
3. Use a desktop viewport at least `1280px` wide.
4. Scroll down inside the page.

Expected:
- Left settings nav remains visible with sticky top spacing.
- The selected section remains clear.
- Main content scrolls normally.

### TC-02 Sticky Aside Desktop

Steps:
1. Stay in edit/settings mode on desktop width.
2. Scroll through a long section such as `Dữ liệu` or `Nâng cao`.

Expected:
- Right validation/preview aside remains visible with sticky top spacing.
- No overlap with the header or main content.

### TC-03 Mobile Layout

Steps:
1. Set viewport below `1280px`, including a mobile width such as `390px`.
2. Open edit/settings mode.
3. Scroll through all sections.

Expected:
- Left nav and right aside behave as normal stacked content.
- No horizontal overflow caused by sticky changes.

### TC-04 Per-Tab Dirty Dot

Steps:
1. Open edit/settings mode with no unsaved changes.
2. Change one field in `Tổng quan`.
3. Move to `Dữ liệu` without editing.

Expected:
- `Tổng quan` nav item shows an amber dot.
- `Dữ liệu` does not show a dot until a data field is edited.
- Global unsaved badge can remain visible.

### TC-05 Dirty Dot Persists Across Tab Switch

Steps:
1. Edit a value in `Hiển thị`.
2. Switch to `Quyền truy cập`.
3. Switch back to `Hiển thị`.

Expected:
- `Hiển thị` amber dot remains visible across tab switches.
- `Quyền truy cập` remains clean unless edited.

### TC-06 Dirty Dot Reset After Save

Steps:
1. Edit values in at least two tabs.
2. Verify both tabs show amber dots.
3. Click `Lưu nháp`.

Expected:
- Save completes through the existing mock adapter flow.
- All amber dots disappear after parent `dirty` returns false.
- No validation or publish behavior regresses.

### TC-07 Connector Wizard Step Indicator

Steps:
1. Open `Nâng cao`.
2. Expand the advanced content.
3. Enable or select a Logic Connector rule.

Expected:
- A compact row appears above the four select controls:
  `1. Trigger -> 2. Source -> 3. Operation -> 4. Target -> xem kết quả ở Review bên dưới`
- The labels match the four select labels underneath.
- Changing selects still updates the dry-run and read-only JSON as before.

### TC-08 Regression: Validation and Publish Readiness

Steps:
1. Open `Kiểm tra`.
2. Verify validation summary still groups issues by section.
3. Use `Sửa lỗi đầu tiên` when an error exists.

Expected:
- Jump action still navigates to the relevant section.
- Publish remains disabled while errors or dirty state exist.
