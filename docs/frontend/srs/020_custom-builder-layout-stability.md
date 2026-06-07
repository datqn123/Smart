# SRS-015 — Custom Builder: Layout Stability, Width Expansion & SelectTrigger Overflow

## 1. Overview

Sau khi quan sát trực tiếp giao diện Custom Builder Settings, phát hiện 2 nhóm vấn đề làm component hiển thị không rõ ràng và dịch chuyển khi thao tác:

1. **Container `max-w-7xl` quá hẹp trong Edit mode** — nhiều grid lồng nhau bị thiếu không gian, xuống dòng không đúng chỗ
2. **SelectTrigger `w-fit` tràn và dịch layout trong grid** — ShadCN SelectTrigger dùng class `w-fit` mặc định; trong grid cell có kích thước cố định (px), trigger tự giãn theo nội dung, vượt qua ranh giới cell và đẩy các element kế bên

**Phạm vi:** frontend-only, `CustomBuilderPage.tsx` only  
**Không đụng:** backend, ai_python, mockAdapter, ShadCN component source, các feature khác

---

## 2. Root cause analysis

### Root cause 1 — `max-w-7xl` áp dụng toàn cục

```tsx
// CustomBuilderPage.tsx line 2494–2496
<div className="h-full overflow-y-auto bg-slate-50 p-4 md:p-6">
  <div className="mx-auto max-w-7xl">   ← áp dụng cho list + create + edit
```

`max-w-7xl` = 1280px. Trong edit mode, sau khi trừ sidebar (~256px) + padding (48px × 2):
- Effective content width ≈ **1184px** trên màn 1440px
- Nhiều grid 5-col bên trong bị hẹp, các cột fixed-px (160px, 180px, 150px, 140px) chiếm tỉ lệ quá lớn

### Root cause 2 — SelectTrigger `w-fit` trong grid cell

```tsx
// select.tsx (ShadCN source) — KHÔNG sửa file này
className={cn("flex w-fit items-center justify-between gap-2 ...", className)}
```

`w-fit` = trigger co giãn theo text content. Trong grid cell:
- Khi option dài (VD "Có dữ liệu" > "Bằng") → trigger rộng hơn cell → tràn
- Khi thay đổi option → width trigger thay đổi → **layout shift**
- Fix đúng: override bằng `w-full` tại container, không sửa ShadCN source

Pattern đã áp dụng thành công ở Connector wizard (line 1033):
```tsx
className="... [&_[data-slot=select-trigger]]:w-full"
```

---

## 3. Bugs cần sửa

### BUG-A — Container `max-w-7xl` làm hẹp Edit mode

**File:** `CustomBuilderPage.tsx` line 2496  
**Hiện tại:**
```tsx
<div className="mx-auto max-w-7xl">
```

**Vấn đề:**
- List mode: phù hợp — bảng danh sách không cần full width
- Create mode: phù hợp — wizard narrow form
- **Edit mode: không phù hợp** — 6 tab với grid lồng nhau cần không gian rộng hơn

**Yêu cầu:**
```tsx
// Thay bằng class có điều kiện theo mode
<div className={mode === "edit" ? "w-full" : "mx-auto max-w-7xl"}>
```

Kết quả: edit mode fill toàn bộ width available; list và create không đổi.

---

### BUG-B — SelectTrigger tràn trong Conditional Logic row

**File:** `CustomBuilderPage.tsx` line 600  
**Hiện tại:**
```tsx
<div className="flex flex-col gap-3 lg:grid lg:grid-cols-[1fr_160px_1fr_140px_auto] lg:items-end">
```

**Vấn đề:**
- Column "Toán tử" = 160px, "Hành động" = 140px (fixed px)
- SelectTrigger bên trong dùng `w-fit` → tràn cell khi text dài
- Thay đổi "Bằng" ↔ "Có dữ liệu" gây layout shift

**Yêu cầu:**
```tsx
<div className="flex flex-col gap-3 lg:grid lg:grid-cols-[1fr_160px_1fr_140px_auto] lg:items-end [&_[data-slot=select-trigger]]:w-full">
```

---

### BUG-C — SelectTrigger tràn trong Default Sort row

**File:** `CustomBuilderPage.tsx` line 2151  
**Hiện tại:**
```tsx
<div className="mt-3 grid items-end gap-3 sm:grid-cols-[1fr_150px]">
```

**Vấn đề:**
- Column "Hướng" = 150px (fixed px)
- SelectTrigger "Tăng dần"/"Giảm dần" tràn 150px cell

**Yêu cầu:**
```tsx
<div className="mt-3 grid items-end gap-3 sm:grid-cols-[1fr_150px] [&_[data-slot=select-trigger]]:w-full">
```

---

### BUG-D — SelectTrigger tràn trong Field Builder rows (Create wizard + Edit data tab)

Hai vị trí dùng cùng pattern — field builder với column "Kiểu" = 180px:

**Vị trí 1 — Create wizard, line 1540:**
```tsx
<div className="grid gap-3 rounded-md border border-slate-200 p-3 lg:grid-cols-[1fr_1fr_180px_120px_120px]">
```

**Vị trí 2 — Edit data tab, line 1998:**
```tsx
<div className="grid gap-3 rounded-md border border-slate-200 p-3 md:grid-cols-[1fr_1fr_180px_120px]">
```

**Vấn đề:** Column "Kiểu" / "Kiểu dữ liệu" = 180px. SelectTrigger cho field type (VD "Số nguyên", "Tham chiếu đến entity") có thể tràn cell.

**Yêu cầu:** Thêm `[&_[data-slot=select-trigger]]:w-full` vào cả 2 container div.

---

### BUG-E — SelectTrigger tràn trong Column Settings row (Display tab)

**File:** `CustomBuilderPage.tsx` line 2106  
**Hiện tại:**
```tsx
<div className="mt-3 grid gap-3 md:grid-cols-[140px_1fr_1fr]">
```

**Vấn đề:**
- Column đầu = 140px (fixed px) chứa Input "Width" (OK)
- Column 2 và 3 = `1fr` chứa SelectTrigger "Align" và "Format"
- Dù `1fr` linh hoạt, SelectTrigger `w-fit` vẫn không fill hết cell → misalignment visual với Input bên trên

**Yêu cầu:** Thêm `[&_[data-slot=select-trigger]]:w-full` vào container div.

---

## 4. Thứ tự triển khai

| # | Bug | Độ ưu tiên | Số dòng thay đổi |
|---|-----|------------|------------------|
| 1 | BUG-B Conditional logic | Cao — gây layout shift rõ nhất | 1 |
| 2 | BUG-C Default sort | Cao — fixed 150px cell | 1 |
| 3 | BUG-D Field builder ×2 | Trung — 180px column | 2 |
| 4 | BUG-E Column settings | Trung — 1fr nhưng visual misalign | 1 |
| 5 | BUG-A Container width | Cao — ảnh hưởng toàn bộ edit mode | 1 |

Tất cả 5 fix **độc lập**, không phụ thuộc thứ tự, không thay đổi logic.

---

## 5. Out of scope

- Không sửa `select.tsx` (ShadCN source)
- Không thay đổi responsive breakpoints
- Không sửa pages khác ngoài `CustomBuilderPage.tsx`
- Không thêm import mới
- Không thay đổi data flow, mock adapter, hoặc state

---

## 6. Acceptance criteria

- [ ] Edit mode sử dụng full available width (không có khoảng trắng 2 bên do `max-w-7xl`)
- [ ] List mode và Create mode vẫn dùng `max-w-7xl` — không thay đổi layout
- [ ] Thay đổi option trong bất kỳ Select nào trong Conditional Logic row: không có layout shift
- [ ] Thay đổi option trong Default Sort row: SelectTrigger fill đúng 150px cell
- [ ] SelectTrigger trong Field Builder row fill đúng 180px cell
- [ ] SelectTrigger trong Column Settings row fill đúng 1fr cell
- [ ] Tất cả SelectTrigger hiển thị text đầy đủ và có border rõ ràng
- [ ] Zero TypeScript errors / ESLint warnings sau khi fix
- [ ] Không có regression ở tab Permissions, Workflow, Advanced
