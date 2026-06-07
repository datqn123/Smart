# Tech Spec 016 — Custom Builder Logic Connector & Display Bugfix

**SRS ref:** `docs/frontend/srs/013_custom-builder-logic-connector-bugfix.md`  
**Target files:**
- `frontend/mini-erp/src/features/custom-builder/api/customBuilderMockAdapter.ts`
- `frontend/mini-erp/src/features/custom-builder/pages/CustomBuilderPage.tsx`
- `frontend/mini-erp/src/components/shared/layout/MainLayout.tsx`

---

## FIX-01 — multiply dry-run falsy-zero

**File:** `customBuilderMockAdapter.ts`  
**Function:** `previewMockLogicConnectorRule` (~line 740)

**Problem:**
```ts
// BEFORE (buggy)
if (rule.operation === "multiply") {
  afterValue = numericValue(targetValue) * numericValue(sourceValue || rule.value || 1)
}
```
`sourceValue || ...` treats numeric `0` as falsy.

**Fix — branch on whether sourceFieldKey is set, not on value truthiness:**
```ts
// AFTER
if (rule.operation === "multiply") {
  const multiplier = rule.sourceFieldKey
    ? numericValue(sourceValue)
    : numericValue(rule.value) || 1
  afterValue = numericValue(targetValue) * multiplier
}
```

**Why this is correct:**
- `rule.sourceFieldKey !== ""` → user chose a field → use its value, including 0
- `rule.sourceFieldKey === ""` → scalar mode → use `rule.value` as coefficient, fallback 1 only when value is also empty

---

## FIX-02 — sumLines dry-run

**File:** `customBuilderMockAdapter.ts`  
**Function:** `previewMockLogicConnectorRule` (~line 743)

**Problem:**
```ts
// BEFORE (buggy)
if (rule.operation === "sumLines") {
  afterValue = numericValue(sourceValue) + numericValue(rule.value)
}
```
Ignores `targetValue` entirely.

**Fix — accumulate into target:**
```ts
// AFTER
if (rule.operation === "sumLines") {
  afterValue = numericValue(targetValue) + numericValue(sourceValue)
}
```

`rule.value` is not used for `sumLines` (only `set` and multiply-scalar use it).

---

## FIX-03 — selectedRuleId stale after delete + add

**File:** `CustomBuilderPage.tsx`  
**Component:** `LogicConnectorBuilder` (~line 909–930)

**Problem:** `selectedRuleId` is initialized once. After delete, it can hold a stale ID or `""`. When the rules list re-renders, button highlight (`selectedRule?.id === rule.id`) compares against the stale value.

**Fix — update `selectedRuleId` defensively in delete handler and after add:**

The current `addRule` already calls `setSelectedRuleId(rule.id)` — that part is correct.

The delete handler needs to select the right fallback:
```ts
// AFTER — in the delete button onClick
const nextRules = logicConnector.rules.filter((rule) => rule.id !== selectedRule.id)
const deletedIndex = logicConnector.rules.findIndex((rule) => rule.id === selectedRule.id)
const nextSelected = nextRules[deletedIndex] ?? nextRules[deletedIndex - 1] ?? nextRules[0]
onChange({ ...logicConnector, rules: nextRules })
setSelectedRuleId(nextSelected?.id ?? "")
```

This selects: the rule that "fell into" the deleted slot, or the previous rule, or the first rule, or "" if empty.

---

## FIX-04 — validateLogicConnector: allow scalar multiply

**File:** `customBuilderMockAdapter.ts`  
**Function:** `validateLogicConnector` (~line 924)

**Problem:**
```ts
// BEFORE (buggy)
if (["copy", "add", "subtract", "multiply", "sumLines"].includes(rule.operation) && (!rule.sourceFieldKey || !sourceField)) {
  errors.push(...)
}
```
Rejects `multiply` with `sourceFieldKey = ""` + non-empty `rule.value` (scalar pattern).

**Fix — split the check by operation:**
```ts
// AFTER — operations that ALWAYS need a source field
const requiresSource: BuilderLogicConnectorOperation[] = ["copy", "add", "subtract", "sumLines"]
if (requiresSource.includes(rule.operation) && (!rule.sourceFieldKey || !sourceField)) {
  errors.push({ section: "logic", message: `${rule.name || "Connector rule"} cần source field hợp lệ.` })
}
// multiply: needs source OR value, not both
if (rule.operation === "multiply" && !rule.sourceFieldKey && !rule.value.trim()) {
  errors.push({ section: "logic", message: `${rule.name || "Connector rule"} cần source field hoặc giá trị hệ số.` })
}
```

---

## FIX-05 — formatPreviewValue currency symbol

**File:** `CustomBuilderPage.tsx`  
**Function:** `formatPreviewValue` (~line 355)

**Problem:** `currency` branch uses same `toLocaleString("vi-VN")` as `number` — no ₫ symbol.

**Fix:**
```ts
// AFTER
function formatPreviewValue(value: string | number, format: BuilderViewColumn["format"]) {
  if (format === "currency") {
    const amount = Number(value)
    return Number.isNaN(amount)
      ? String(value)
      : new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" }).format(amount)
  }
  if (format === "number") {
    const amount = Number(value)
    return Number.isNaN(amount) ? String(value) : amount.toLocaleString("vi-VN")
  }
  return String(value)
}
```

`Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" })` renders `1.200.000 ₫` — consistent with the rest of the app.

---

## FIX-06 — allowedOperations derive from type

**File:** `customBuilderMockAdapter.ts`  
**Function:** `validateLogicConnector` (~line 908)

**Problem:** Hardcoded array duplicates the type union.

**Fix — derive from a canonical lookup object that already exists:**

`logicOperationLabels` in `CustomBuilderPage.tsx` is a `Record<BuilderLogicConnectorOperation, string>` — all keys are exhaustively typed. We can use the same pattern in the adapter by exporting a const:

```ts
// In customBuilderMockAdapter.ts — add near the operation type definition
export const LOGIC_CONNECTOR_OPERATIONS: Record<BuilderLogicConnectorOperation, true> = {
  copy: true,
  set: true,
  add: true,
  subtract: true,
  multiply: true,
  sumLines: true,
}
```

Then in `validateLogicConnector`:
```ts
// AFTER — remove the local allowedOperations array
if (!(rule.operation in LOGIC_CONNECTOR_OPERATIONS)) {
  errors.push(...)
}
```

TypeScript will error if a new operation is added to the type but not to `LOGIC_CONNECTOR_OPERATIONS` because the `Record<BuilderLogicConnectorOperation, true>` annotation requires all keys.

---

## FIX-07 — MainLayout sidebar flash on mobile

**File:** `MainLayout.tsx`

**Problem:** `useUIStore` inits `sidebarOpen: true`. `useEffect` runs post-render → flash on mobile.

**Fix — change `useUIStore` initial state to `false` by default:**

Open `frontend/mini-erp/src/store/useUIStore.ts`, change the `sidebarOpen` initial value:

```ts
// BEFORE
sidebarOpen: true,

// AFTER
sidebarOpen: typeof window !== "undefined" ? window.innerWidth >= 768 : false,
```

This sets `true` on desktop (≥768px) and `false` on mobile at store construction time — no flash, no useEffect needed for the initial state.

The existing `useEffect` in `MainLayout.tsx` that responds to viewport resize changes can stay as-is (it handles dynamic resize events, not initial state). However the `closeOnMobile()` call at the top of that effect becomes a no-op on mobile because the store now initialises correctly — it's harmless but can be left for defensive coverage.

**Note:** `useUIStore` uses `zustand/middleware persist` for `sidebarWidth`. Check that `sidebarOpen` is NOT in the persisted keys — if it is, the persisted `true` will override the new init. If needed, remove `sidebarOpen` from persist partialize.

---

## FIX-08 — inferColumnFormat helper

**File:** `customBuilderMockAdapter.ts`

**Problem:** Format-inference ternary duplicated in ≥3 places.

**Fix — export a single helper function:**

```ts
// In customBuilderMockAdapter.ts — add after BuilderViewColumn type definition
export function inferColumnFormat(fieldType: BuilderFieldType): BuilderViewColumn["format"] {
  if (fieldType === "money") return "currency"
  if (fieldType === "number") return "number"
  if (fieldType === "date") return "date"
  return "text"
}
```

**Update all call sites:**

1. `createMockBuilderPage` (~line 670): replace ternary with `inferColumnFormat(field?.type ?? "text")`
2. `defaultColumnForField` in `CustomBuilderPage.tsx` (~line 760): replace ternary with `inferColumnFormat(field.type)`

---

## Implementation order

Apply in this order to minimize conflicts:

1. FIX-06 (add `LOGIC_CONNECTOR_OPERATIONS` and `inferColumnFormat` exports) — pure additions, no breakage
2. FIX-08 (replace ternary duplication using `inferColumnFormat`) — call-site update only
3. FIX-01 + FIX-02 (dry-run math fixes) — isolated to `previewMockLogicConnectorRule`
4. FIX-04 (validate scalar multiply) — change validation logic only
5. FIX-03 (selectedRuleId delete handler) — UI component only
6. FIX-05 (currency format) — UI helper only
7. FIX-07 (sidebar initial state) — store + verify persist config

---

## Verification checklist for Codex

- [ ] `npm run lint` — zero errors, zero warnings
- [ ] `npm run build` (or `tsc --noEmit`) — no TypeScript errors
- [ ] No changes to `backend/` or `ai_python/`
- [ ] No new files except this diff
- [ ] `LOGIC_CONNECTOR_OPERATIONS` is exported and used in `validateLogicConnector`
- [ ] `inferColumnFormat` is exported and used in all 2+ call sites
- [ ] `useUIStore` `sidebarOpen` initial value updated; confirm persist does NOT include `sidebarOpen`
