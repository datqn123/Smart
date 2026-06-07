# Tech Spec 017 — Custom Builder: Wizard Step Label, Dry-run State & Conditional Input

**SRS ref:** `docs/frontend/srs/014_custom-builder-wizard-conditional-ui-bugfix.md`  
**Target files:**
- `frontend/mini-erp/src/features/custom-builder/pages/CustomBuilderPage.tsx`
- `frontend/mini-erp/src/features/custom-builder/api/customBuilderMockAdapter.ts`

---

## FIX-A — Connector wizard subtitle

**File:** `CustomBuilderPage.tsx`  
**Line:** 1015

**Before:**
```tsx
<p className="mt-1 text-xs text-slate-500">Đi theo 5 bước: trigger, source, operation, target, review.</p>
```

**After:**
```tsx
<p className="mt-1 text-xs text-slate-500">Đi theo 4 bước: trigger, source, operation, target — xem kết quả ở Review bên dưới.</p>
```

**Why:** Table chỉ có 4 cột đánh số (1–4). "5. Review dry-run mock" là panel riêng bên dưới, không phải cột trong bảng. Subtitle "5 bước: ... review" gây nhầm vị trí.

---

## FIX-B — Dry-run "set": đổi giá trị ban đầu trong sampleRecord

**File:** `customBuilderMockAdapter.ts`  
**Line:** ~458 (trong `sampleRecords[0].values`)

**Before:**
```ts
handling_status: "Chờ xử lý",
```

**After:**
```ts
handling_status: "Nháp",
```

**Why:** Mock rule `operation: "set"` trên `handling_status` với `value: "Chờ xử lý"`. Nếu sampleRecord cũng khởi đầu với `"Chờ xử lý"` → `beforeValue = afterValue = "Chờ xử lý"` → dry-run không thể hiện thay đổi. `"Nháp"` là giá trị hợp lệ trong `options: ["Nháp", "Chờ xử lý", "Đã xử lý"]`.

**Scope check:** `sampleRecords` chỉ dùng trong `previewMockLogicConnectorRule` (dry-run) và `LightweightPreview` (bảng xem thử). Đổi sang `"Nháp"` ảnh hưởng bảng xem thử trong Edit Settings tab — giá trị sẽ hiển thị là "Nháp" thay vì "Chờ xử lý". Điều này chấp nhận được vì đây là fixture minh họa.

---

## FIX-C — Conditional logic "Giá trị" input: xóa bg-white

**File:** `CustomBuilderPage.tsx`  
**Line:** 640

**Before:**
```tsx
<Input
  className="mt-1.5 bg-white"
  value={conditional?.value ?? ""}
  onChange={...}
  disabled={!conditional || conditional.operator === "not_empty"}
/>
```

**After:**
```tsx
<Input
  className="mt-1.5"
  value={conditional?.value ?? ""}
  onChange={...}
  disabled={!conditional || conditional.operator === "not_empty"}
/>
```

**Why:** ShadCN Input mặc định `bg-transparent` + `disabled:opacity-50`. Class `bg-white` ghi đè làm nền trắng. Khi disabled: `white bg + 50% opacity` trên card `bg-white` = viền gần như vô hình. Xóa `bg-white` → input dùng `bg-transparent` → viền ở 50% opacity vẫn đủ tương phản với nền card.

---

## Implementation order

1. FIX-C (1 dòng xóa class)
2. FIX-B (1 dòng đổi string)
3. FIX-A (1 dòng đổi text)

Tất cả 3 fix độc lập — không phụ thuộc nhau, không thay đổi logic.

---

## Verification checklist

- [ ] `npm run lint` — zero errors
- [ ] `npx tsc --noEmit` — zero TypeScript errors
- [ ] Không thay đổi file nào ngoài 2 file trên
- [ ] Không thêm import mới
- [ ] Dry-run "set" rule: Target trước = "Nháp", Target sau = "Chờ xử lý"
- [ ] Conditional "Giá trị" input visible (dù mờ) khi condition = "Không dùng"
- [ ] Connector wizard subtitle không còn đề cập "5 bước"
