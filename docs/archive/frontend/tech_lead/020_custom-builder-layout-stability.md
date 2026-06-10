# Tech Spec 018 — Custom Builder Layout Stability

**SRS ref:** `docs/frontend/srs/015_custom-builder-layout-stability.md`  
**Target file:** `frontend/mini-erp/src/features/custom-builder/pages/CustomBuilderPage.tsx`

## Goal

Fix layout instability in Custom Builder by widening edit mode and forcing ShadCN `SelectTrigger` controls to fill their grid cells.

## Constraints

- Do not edit backend, `ai_python`, mock adapter, ShadCN select source, or any file outside `CustomBuilderPage.tsx`.
- Do not add imports.
- Do not change logic, state, data flow, breakpoints, or JSX structure.
- All implementation changes are className-only.

## Implementation Tasks

### BUG-B — Conditional Logic Row

Modify the conditional visibility row wrapper in `FieldLogicSettings`.

Before:
```tsx
<div className="flex flex-col gap-3 lg:grid lg:grid-cols-[1fr_160px_1fr_140px_auto] lg:items-end">
```

After:
```tsx
<div className="flex flex-col gap-3 lg:grid lg:grid-cols-[1fr_160px_1fr_140px_auto] lg:items-end [&_[data-slot=select-trigger]]:w-full">
```

### BUG-C — Default Sort Row

Modify the default sort row wrapper in the Display tab.

Before:
```tsx
<div className="mt-3 grid items-end gap-3 sm:grid-cols-[1fr_150px]">
```

After:
```tsx
<div className="mt-3 grid items-end gap-3 sm:grid-cols-[1fr_150px] [&_[data-slot=select-trigger]]:w-full">
```

### BUG-D.1 — Create Wizard Field Builder Row

Modify the field row wrapper in wizard step 3.

Before:
```tsx
<div key={field.id} className="grid gap-3 rounded-md border border-slate-200 p-3 lg:grid-cols-[1fr_1fr_180px_120px_120px]">
```

After:
```tsx
<div key={field.id} className="grid gap-3 rounded-md border border-slate-200 p-3 lg:grid-cols-[1fr_1fr_180px_120px_120px] [&_[data-slot=select-trigger]]:w-full">
```

### BUG-D.2 — Edit Data Tab Field Builder Row

Modify the field row wrapper in the edit Data tab.

Before:
```tsx
<div key={field.id} className="grid gap-3 rounded-md border border-slate-200 p-3 md:grid-cols-[1fr_1fr_180px_120px]">
```

After:
```tsx
<div key={field.id} className="grid gap-3 rounded-md border border-slate-200 p-3 md:grid-cols-[1fr_1fr_180px_120px] [&_[data-slot=select-trigger]]:w-full">
```

### BUG-E — Column Settings Row

Modify the column settings wrapper in the Display tab.

Before:
```tsx
<div className="mt-3 grid gap-3 md:grid-cols-[140px_1fr_1fr]">
```

After:
```tsx
<div className="mt-3 grid gap-3 md:grid-cols-[140px_1fr_1fr] [&_[data-slot=select-trigger]]:w-full">
```

### BUG-A — Page Container Width

Modify the top-level content width wrapper.

Before:
```tsx
<div className="mx-auto max-w-7xl">
```

After:
```tsx
<div className={mode === "edit" ? "w-full" : "mx-auto max-w-7xl"}>
```

## Verification

Run:
```bash
cd frontend/mini-erp
npm run lint
npx tsc --noEmit
```

Manual checks:
- `/settings/custom-builder` list mode keeps centered `max-w-7xl`.
- Create wizard keeps centered `max-w-7xl`.
- Edit mode fills available width with `w-full`.
- SelectTrigger controls in conditional logic, default sort, field builder rows, and column settings fill their grid cells.
