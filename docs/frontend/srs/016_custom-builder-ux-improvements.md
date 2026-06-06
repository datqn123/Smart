# SRS-016 — Custom Builder: UX Improvements (Sticky Nav, Per-tab Dirty, Wizard Step Indicator)

## Metadata

| Mục | Giá trị |
|-----|---------|
| Phạm vi | Frontend-only |
| File target | `CustomBuilderPage.tsx` |
| Không đụng | backend, ai_python, mockAdapter, ShadCN source |
| Phụ thuộc | Không phụ thuộc SRS-015 |

---

## 1. Tổng quan

Sau khi quan sát luồng sử dụng Custom Builder Settings, phát hiện 3 vấn đề UX làm người dùng mất orientation và mất dữ liệu chưa lưu mà không hay:

1. **Sidebar nav cuộn mất** — khi cuộn xuống trong tab "Dữ liệu" hoặc "Nâng cao", sidebar điều hướng 6 tab cuộn theo và biến mất khỏi viewport
2. **Không biết tab nào có thay đổi chưa lưu** — badge "Có thay đổi chưa lưu" chỉ hiện chung ở header, không chỉ rõ tab nào đang dirty
3. **Logic Connector wizard không rõ flow** — 4 select nằm ngang không truyền đạt được đây là pipeline theo thứ tự, người dùng không biết phải điền từ trái sang phải

---

## 2. Phân tích code hiện tại

### IMP-A — Sidebar nav (line 1934)

```tsx
<nav className="min-w-0 rounded-md border border-slate-200 bg-white p-2 xl:self-start">
```

Có `xl:self-start` nhưng **thiếu `xl:sticky xl:top-4`**. So sánh: wizard `CreateInterfaceWizard` aside (line 1697) đã dùng đúng pattern:

```tsx
className="... xl:sticky xl:top-4 xl:self-start"
```

Tương tự, aside bên phải của EditInterfaceSettings (line 2327) cũng thiếu sticky.

### IMP-B — Per-tab dirty indicator

`dirty` prop (boolean) đến từ parent `CustomBuilderPage`, chỉ phân biệt có/không thay đổi toàn trang. Không có thông tin tab nào bị dirty.

`section` state (line 1737) là local state trong `EditInterfaceSettings`. Mỗi khi `onChange` callback được gọi, đó là lúc có thể ghi nhận tab nào đang active.

Cần thêm local state `dirtySections: Set<EditSection>` trong `EditInterfaceSettings`:
- Thêm `section` hiện tại vào set khi `onChange` được gọi
- Reset set về rỗng khi bundle được lưu (detect qua `dirty` prop đổi từ `true` → `false`)

### IMP-C — Wizard step indicator (line 1010–1033)

Hiện tại chỉ có subtitle text: `"Đi theo 4 bước: trigger, source, operation, target..."`. Không có visual indicator. Cần thêm một row breadcrumb-style giữa subtitle và grid 4 select, hiển thị: `1. Trigger → 2. Source → 3. Operation → 4. Target`.

---

## 3. Yêu cầu chi tiết

### IMP-A — Sticky sidebar nav và aside trong Edit mode

**File:** `CustomBuilderPage.tsx`

**Thay đổi 1 — Nav sidebar (line ~1934):**
```tsx
// Trước
<nav className="min-w-0 rounded-md border border-slate-200 bg-white p-2 xl:self-start">

// Sau
<nav className="min-w-0 rounded-md border border-slate-200 bg-white p-2 xl:sticky xl:top-4 xl:self-start">
```

**Thay đổi 2 — Aside bên phải (line ~2327):**
```tsx
// Trước
<aside className="rounded-md border border-slate-200 bg-white p-4 xl:self-start">

// Sau
<aside className="rounded-md border border-slate-200 bg-white p-4 xl:sticky xl:top-4 xl:self-start">
```

**Điều kiện hoạt động:** `sticky` chỉ có tác dụng khi ancestor có overflow scroll. Container page (`h-full overflow-y-auto`, line 2494) đã thỏa điều kiện này.

**Acceptance:**
- [ ] Trên màn `xl` (≥ 1280px): nav sidebar dính ở `top: 16px` khi cuộn xuống
- [ ] Aside bên phải (Validation + Preview) cũng dính khi cuộn
- [ ] Trên màn nhỏ hơn `xl`: không bị ảnh hưởng (sticky không có hiệu lực)
- [ ] Khi content của main panel ngắn hơn viewport: nav và aside không dính (behavior đúng)

---

### IMP-B — Per-tab dirty indicator

**File:** `CustomBuilderPage.tsx`, trong `EditInterfaceSettings` component

**Logic:**

Thêm state và effect vào `EditInterfaceSettings`:

```tsx
const [dirtySections, setDirtySections] = useState<Set<EditSection>>(new Set())

// Reset khi bundle được lưu xong (dirty: true → false)
const prevDirty = useRef(dirty)
useEffect(() => {
  if (prevDirty.current === true && dirty === false) {
    setDirtySections(new Set())
  }
  prevDirty.current = dirty
}, [dirty])

// Wrap onChange để ghi nhận section đang dirty
const handleChange = (updater: (current: BuilderPageBundle) => BuilderPageBundle) => {
  setDirtySections((prev) => new Set([...prev, section]))
  onChange(updater)
}
```

Sau đó thay tất cả `onChange(...)` call bên trong component thành `handleChange(...)`.

**Render indicator trên nav button:**

```tsx
<button ...>
  <span className="flex items-center justify-between w-full">
    {sectionLabels[key]}
    {dirtySections.has(key) && (
      <span className="h-2 w-2 rounded-full bg-amber-400 flex-shrink-0" />
    )}
  </span>
</button>
```

**Acceptance:**
- [ ] Thay đổi bất kỳ field nào trong tab "Dữ liệu" → dot amber xuất hiện trên nút "Dữ liệu"
- [ ] Thay đổi ở tab "Hiển thị" → dot amber trên "Hiển thị", tab "Dữ liệu" KHÔNG có dot nếu không đổi
- [ ] Bấm "Lưu nháp" → tất cả dot biến mất
- [ ] Chuyển qua lại giữa tab không xóa dot
- [ ] Tab "Tổng quan" nếu không chỉnh → không có dot dù dirty = true từ tab khác

---

### IMP-C — Logic Connector wizard step indicator

**File:** `CustomBuilderPage.tsx`, trong `LogicConnectorBuilder` component, bên trong block `selectedRule &&` (line ~1010)

**Thêm vào sau subtitle (sau line 1015, trước grid line 1033):**

```tsx
<div className="mt-3 flex items-center gap-1 text-xs text-slate-500">
  {(["1. Trigger", "2. Source", "3. Operation", "4. Target"] as const).map((step, index) => (
    <span key={step} className="flex items-center gap-1">
      {index > 0 && <span className="text-slate-300">→</span>}
      <span className="rounded bg-slate-100 px-2 py-0.5 font-medium text-slate-700">{step}</span>
    </span>
  ))}
  <span className="ml-2 text-slate-400">→ xem kết quả ở Review bên dưới</span>
</div>
```

**Acceptance:**
- [ ] Khi chọn bất kỳ rule nào trong connector wizard, hiển thị row: `1. Trigger → 2. Source → 3. Operation → 4. Target → xem kết quả ở Review bên dưới`
- [ ] Không thay đổi logic hay state của các select
- [ ] Các label trong step indicator khớp với Label của từng select bên dưới

---

## 4. Thứ tự triển khai

| # | Item | Độ ưu tiên | Dòng thay đổi |
|---|------|------------|---------------|
| 1 | IMP-A Sticky nav + aside | Cao — 2 dòng | 2 |
| 2 | IMP-C Wizard step indicator | Trung — visual only | ~10 |
| 3 | IMP-B Per-tab dirty dot | Thấp hơn — cần state mới | ~30 |

IMP-A và IMP-C độc lập hoàn toàn. IMP-B phức tạp hơn (cần useRef, useEffect, wrap onChange).

---

## 5. Out of scope

- Không thay đổi logic save/publish
- Không thay đổi responsive breakpoint hiện tại
- Không thêm animation hay transition
- Không sửa file nào ngoài `CustomBuilderPage.tsx`
- Inventory effect và AI copilot vẫn là placeholder (không implement)

---

## 6. Acceptance criteria tổng hợp

- [ ] Sidebar nav và aside sticky khi cuộn trên màn xl
- [ ] Dot amber xuất hiện đúng tab khi chỉnh, biến mất khi lưu
- [ ] Step indicator hiện trong connector wizard mỗi khi chọn rule
- [ ] `npx tsc --noEmit` — zero errors
- [ ] `npm run lint` — zero warnings
- [ ] Không regression: save, publish, validation, tab switching vẫn hoạt động đúng
