# QA Spec 019 — Custom Builder Layout Stability

**SRS ref:** `docs/frontend/srs/015_custom-builder-layout-stability.md`  
**Tech Spec ref:** `docs/frontend/tech_lead/018_custom-builder-layout-stability.md`

## Scope

Verify Custom Builder layout stability after class-only fixes in `CustomBuilderPage.tsx`.

## Automated Checks

### TC-QA-01 — Lint

Run:
```bash
cd frontend/mini-erp
npm run lint
```

Expected:
- Exit code 0.
- No lint errors.
- No new warnings from `CustomBuilderPage.tsx`.

### TC-QA-02 — TypeScript

Run:
```bash
cd frontend/mini-erp
npx tsc --noEmit
```

Expected:
- Exit code 0.
- No TypeScript errors.

## Manual Browser Checks

### TC-A — Mode Container Width

Steps:
1. Open `/settings/custom-builder`.
2. Verify list mode page content is centered and constrained.
3. Click `Tạo giao diện mới`.
4. Verify create wizard remains centered and constrained.
5. Return to list and click `Sửa` on an existing interface.

Expected:
- List and create modes keep `mx-auto max-w-7xl`.
- Edit mode uses full available content width.
- No horizontal overflow appears on desktop or mobile.

### TC-B — Conditional Logic SelectTrigger

Steps:
1. Open edit mode.
2. Go to tab `Dữ liệu`.
3. Inspect the `Logic cơ bản` / conditional visibility row.
4. Change `Toán tử` between `Bằng` and `Có dữ liệu`.

Expected:
- SelectTrigger fills its grid cell.
- No overflow beyond the 160px or 140px fixed columns.
- Row does not shift when the option text changes.

### TC-C — Default Sort SelectTrigger

Steps:
1. Go to tab `Hiển thị`.
2. Inspect the `Default sort` row.
3. Change sort direction between `Tăng dần` and `Giảm dần`.

Expected:
- Both select triggers fill their cells.
- Direction select stays within the 150px fixed column.
- No layout shift occurs.

### TC-D — Field Builder SelectTrigger

Steps:
1. Open create wizard step `Dữ liệu cần quản lý`.
2. Inspect field type selects.
3. Open edit mode tab `Dữ liệu`.
4. Inspect field type selects there as well.

Expected:
- Field type SelectTrigger fills the 180px cell in both create and edit contexts.
- Long labels do not push adjacent controls.

### TC-E — Column Settings SelectTrigger

Steps:
1. In edit mode, go to tab `Hiển thị`.
2. Inspect a selected list column row.
3. Change `Align` and `Format`.

Expected:
- Align and Format SelectTrigger controls fill their `1fr` cells.
- Controls align visually with the Width input.
- No layout shift occurs.

## Regression Checks

- Permissions tab still renders role checkboxes.
- Workflow and Logic Connector advanced sections still open.
- Preview table and preview form still render.
- Mobile viewport does not show horizontal scrolling.
