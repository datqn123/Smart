# Dashboard Color Accents Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Thêm điểm nhấn màu theo nhóm chỉ số (semantic hue) vào DashboardPage — icon chips, status pills, tags màu, chart đậm hơn — theo spec `frontend/mini-erp/.agents/designs/2026-06-12-dashboard-color-accents-design.md`.

**Architecture:** Chỉ sửa 1 file `src/features/dashboard/pages/DashboardPage.tsx` — đổi class Tailwind + thêm 2 icon import, không đổi layout/logic/data. Mỗi task là một khu vực UI độc lập, verify bằng `npx tsc --noEmit` và commit riêng.

**Tech Stack:** React 19 + TypeScript + Tailwind CSS v4 + lucide-react + Recharts.

**Working directory:** `frontend/mini-erp`

**Quy ước chung:**

- Codebase KHÔNG dùng semicolon, KHÔNG chạy Prettier.
- Mỗi old/new pair bên dưới là exact-match (kể cả indentation) — dùng Edit tool với chuỗi đúng nguyên văn.
- Icon lucide kế thừa màu qua `currentColor`, nên đặt `text-{hue}-600` trên div chip là icon tự ăn màu.

---

### Task 1: Icon chip cho 3 card tài chính

**Files:**

- Modify: `frontend/mini-erp/src/features/dashboard/pages/DashboardPage.tsx`

- [ ] **Step 1.1: Thêm import `Banknote`, `Receipt`**

Old:

```tsx
  ArrowUpLeft,
  Crown,
} from "lucide-react"
```

New:

```tsx
  ArrowUpLeft,
  Crown,
  Banknote,
  Receipt,
} from "lucide-react"
```

- [ ] **Step 1.2: Card "Doanh thu hôm nay" — chip indigo**

Old:

```tsx
            <div className="bg-white rounded-lg border border-slate-200 shadow-xs p-5">
              <p className="text-[13px] font-medium text-slate-500">Doanh thu hôm nay</p>
              <div className="h-9 mt-2 flex items-center">
```

New:

```tsx
            <div className="bg-white rounded-lg border border-slate-200 shadow-xs p-5">
              <div className="flex items-start justify-between">
                <p className="text-[13px] font-medium text-slate-500">Doanh thu hôm nay</p>
                <div className="h-8 w-8 rounded-md bg-indigo-50 text-indigo-600 flex items-center justify-center">
                  <Banknote className="h-4 w-4" />
                </div>
              </div>
              <div className="h-9 mt-2 flex items-center">
```

- [ ] **Step 1.3: Card "Số đơn hôm nay" — chip sky**

Old:

```tsx
            <div className="bg-white rounded-lg border border-slate-200 shadow-xs p-5">
              <p className="text-[13px] font-medium text-slate-500">Số đơn hôm nay</p>
              <div className="h-9 mt-2 flex items-center">
```

New:

```tsx
            <div className="bg-white rounded-lg border border-slate-200 shadow-xs p-5">
              <div className="flex items-start justify-between">
                <p className="text-[13px] font-medium text-slate-500">Số đơn hôm nay</p>
                <div className="h-8 w-8 rounded-md bg-sky-50 text-sky-600 flex items-center justify-center">
                  <ShoppingCart className="h-4 w-4" />
                </div>
              </div>
              <div className="h-9 mt-2 flex items-center">
```

- [ ] **Step 1.4: Card "Giá trị đơn TB" — chip emerald**

Old:

```tsx
            <div className="bg-white rounded-lg border border-slate-200 shadow-xs p-5">
              <p className="text-[13px] font-medium text-slate-500">Giá trị đơn TB</p>
              <div className="h-9 mt-2 flex items-center">
```

New:

```tsx
            <div className="bg-white rounded-lg border border-slate-200 shadow-xs p-5">
              <div className="flex items-start justify-between">
                <p className="text-[13px] font-medium text-slate-500">Giá trị đơn TB</p>
                <div className="h-8 w-8 rounded-md bg-emerald-50 text-emerald-600 flex items-center justify-center">
                  <Receipt className="h-4 w-4" />
                </div>
              </div>
              <div className="h-9 mt-2 flex items-center">
```

- [ ] **Step 1.5: Verify**

Run (trong `frontend/mini-erp`): `npx tsc --noEmit`
Expected: exit 0, không lỗi.

- [ ] **Step 1.6: Commit**

```bash
git add src/features/dashboard/pages/DashboardPage.tsx
git commit -m "feat(dashboard): add hue icon chips to financial cards"
```

---

### Task 2: Icon chip cho 4 card KPI

**Files:**

- Modify: `frontend/mini-erp/src/features/dashboard/pages/DashboardPage.tsx`

- [ ] **Step 2.1: Thêm field `chip` vào type của mảng `kpis`**

Old:

```tsx
    subWarn: boolean
    icon: React.ElementType
    onClick: () => void
```

New:

```tsx
    subWarn: boolean
    icon: React.ElementType
    chip: string
    onClick: () => void
```

- [ ] **Step 2.2: KPI "Tổng mặt hàng" — amber**

Old:

```tsx
      subWarn: (invData?.lowStockCount ?? 0) > 0,
      icon: Package,
      onClick: () => navigate("/inventory/stock"),
```

New:

```tsx
      subWarn: (invData?.lowStockCount ?? 0) > 0,
      icon: Package,
      chip: "bg-amber-50 text-amber-600",
      onClick: () => navigate("/inventory/stock"),
```

- [ ] **Step 2.3: KPI "Đơn chờ xử lý" — sky**

Old:

```tsx
      subWarn: false,
      icon: ShoppingCart,
      onClick: () => navigate("/orders/wholesale"),
```

New:

```tsx
      subWarn: false,
      icon: ShoppingCart,
      chip: "bg-sky-50 text-sky-600",
      onClick: () => navigate("/orders/wholesale"),
```

- [ ] **Step 2.4: KPI "Cần phê duyệt" — violet**

Old:

```tsx
      subWarn: (approvalData?.summary.totalPending ?? 0) > 0,
      icon: ClipboardCheck,
      onClick: () => navigate("/approvals/pending"),
```

New:

```tsx
      subWarn: (approvalData?.summary.totalPending ?? 0) > 0,
      icon: ClipboardCheck,
      chip: "bg-violet-50 text-violet-600",
      onClick: () => navigate("/approvals/pending"),
```

- [ ] **Step 2.5: KPI "Giá trị kho" — emerald**

Old:

```tsx
      subWarn: (invData?.expiringSoonCount ?? 0) > 0,
      icon: TrendingUp,
      onClick: () => navigate("/inventory/stock"),
```

New:

```tsx
      subWarn: (invData?.expiringSoonCount ?? 0) > 0,
      icon: TrendingUp,
      chip: "bg-emerald-50 text-emerald-600",
      onClick: () => navigate("/inventory/stock"),
```

- [ ] **Step 2.6: Render — label trái, chip phải (bỏ icon trần cạnh label)**

Old:

```tsx
              <div className="flex items-center gap-2">
                <kpi.icon className="h-4 w-4 text-slate-400" />
                <p className="text-[13px] font-medium text-slate-500">{kpi.title}</p>
              </div>
```

New:

```tsx
              <div className="flex items-start justify-between">
                <p className="text-[13px] font-medium text-slate-500">{kpi.title}</p>
                <div className={`h-8 w-8 rounded-md flex items-center justify-center shrink-0 ${kpi.chip}`}>
                  <kpi.icon className="h-4 w-4" />
                </div>
              </div>
```

- [ ] **Step 2.7: Verify**

Run (trong `frontend/mini-erp`): `npx tsc --noEmit`
Expected: exit 0.

- [ ] **Step 2.8: Commit**

```bash
git add src/features/dashboard/pages/DashboardPage.tsx
git commit -m "feat(dashboard): add hue icon chips to KPI cards"
```

---

### Task 3: Chart đậm hơn + toggle indigo

**Files:**

- Modify: `frontend/mini-erp/src/features/dashboard/pages/DashboardPage.tsx`

- [ ] **Step 3.1: Gradient fill 0.08 → 0.15**

Old:

```tsx
                          <stop offset="5%" stopColor="#4f46e5" stopOpacity={0.08} />
```

New:

```tsx
                          <stop offset="5%" stopColor="#4f46e5" stopOpacity={0.15} />
```

- [ ] **Step 3.2: Line 1.5 → 2**

Old:

```tsx
                        stroke="#4f46e5"
                        strokeWidth={1.5}
```

New:

```tsx
                        stroke="#4f46e5"
                        strokeWidth={2}
```

- [ ] **Step 3.3: Toggle active text indigo**

Old:

```tsx
                          ? "bg-white border border-slate-200 shadow-xs text-slate-900"
```

New:

```tsx
                          ? "bg-white border border-slate-200 shadow-xs text-indigo-600"
```

- [ ] **Step 3.4: Verify**

Run (trong `frontend/mini-erp`): `npx tsc --noEmit`
Expected: exit 0.

- [ ] **Step 3.5: Commit**

```bash
git add src/features/dashboard/pages/DashboardPage.tsx
git commit -m "feat(dashboard): strengthen chart fill and indigo active toggle"
```

---

### Task 4: Status pill + tag kênh trong Đơn hàng gần đây

**Files:**

- Modify: `frontend/mini-erp/src/features/dashboard/pages/DashboardPage.tsx`

- [ ] **Step 4.1: Thay `statusDot` bằng `statusBadge`**

Old:

```tsx
/** Màu chấm trạng thái cho style dot + text (Linear-style). */
function statusDot(s: string) {
  if (s === "Pending") return "bg-amber-500"
  if (s === "Processing") return "bg-indigo-500"
  if (s === "Shipped" || s === "Partial") return "bg-blue-500"
  if (s === "Delivered" || s === "Completed") return "bg-emerald-500"
  if (s === "Cancelled") return "bg-red-500"
  return "bg-slate-400"
}
```

New:

```tsx
/** Cặp class nền + chữ cho pill trạng thái (tint 50/700). */
function statusBadge(s: string) {
  if (s === "Pending") return "bg-amber-50 text-amber-700"
  if (s === "Processing") return "bg-indigo-50 text-indigo-700"
  if (s === "Shipped" || s === "Partial") return "bg-sky-50 text-sky-700"
  if (s === "Delivered" || s === "Completed") return "bg-emerald-50 text-emerald-700"
  if (s === "Cancelled") return "bg-red-50 text-red-700"
  return "bg-slate-100 text-slate-600"
}
```

- [ ] **Step 4.2: Thêm `channelTag` ngay sau `channelLabel`**

Old:

```tsx
function channelLabel(c: string) {
  if (c === "Retail") return "Lẻ"
  if (c === "Wholesale") return "Sỉ"
  return "Trả hàng"
}
```

New:

```tsx
function channelLabel(c: string) {
  if (c === "Retail") return "Lẻ"
  if (c === "Wholesale") return "Sỉ"
  return "Trả hàng"
}

/** Tint tag kênh — khớp màu channel bars (Lẻ indigo, Sỉ emerald). */
function channelTag(c: string) {
  if (c === "Retail") return "bg-indigo-50 text-indigo-700"
  if (c === "Wholesale") return "bg-emerald-50 text-emerald-700"
  return "bg-red-50 text-red-700"
}
```

- [ ] **Step 4.3: Render status pill (bỏ dot)**

Old:

```tsx
                      <span className="inline-flex items-center gap-1.5 text-xs text-slate-600">
                        <span className={`h-1.5 w-1.5 rounded-full ${statusDot(order.status)}`} />
                        {statusLabel(order.status)}
                      </span>
```

New:

```tsx
                      <span
                        className={`inline-flex items-center text-xs font-medium px-2 py-0.5 rounded-full ${statusBadge(order.status)}`}
                      >
                        {statusLabel(order.status)}
                      </span>
```

- [ ] **Step 4.4: Render tag kênh màu**

LƯU Ý: span gần giống tồn tại ở khối "Cần phê duyệt" (chứa `{item.type}`) — old_string dưới đây phải gồm cả dòng `{channelLabel(...)}` để match đúng chỗ.

Old:

```tsx
                        <span className="text-[10px] text-slate-500 bg-slate-100 rounded px-1.5 shrink-0">
                          {channelLabel(order.orderChannel)}
                        </span>
```

New:

```tsx
                        <span
                          className={`text-[10px] font-medium rounded px-1.5 shrink-0 ${channelTag(order.orderChannel)}`}
                        >
                          {channelLabel(order.orderChannel)}
                        </span>
```

- [ ] **Step 4.5: Verify**

Run (trong `frontend/mini-erp`): `npx tsc --noEmit`
Expected: exit 0 (nếu còn tham chiếu `statusDot` sẽ báo lỗi — kiểm tra Step 4.3 đã chạy).

- [ ] **Step 4.6: Commit**

```bash
git add src/features/dashboard/pages/DashboardPage.tsx
git commit -m "feat(dashboard): soft status pills and channel tags"
```

---

### Task 5: Tag phê duyệt + icon header màu + crown vàng

**Files:**

- Modify: `frontend/mini-erp/src/features/dashboard/pages/DashboardPage.tsx`

- [ ] **Step 5.1: Tag loại phiếu "Cần phê duyệt" → violet**

Old:

```tsx
                        <span className="text-[10px] text-slate-500 bg-slate-100 rounded px-1.5 shrink-0">
                          {item.type}
                        </span>
```

New:

```tsx
                        <span className="text-[10px] font-medium text-violet-700 bg-violet-50 rounded px-1.5 shrink-0">
                          {item.type}
                        </span>
```

- [ ] **Step 5.2: Icon `Users` header → teal**

Old:

```tsx
                <Users className="h-4 w-4 text-slate-400" />
```

New:

```tsx
                <Users className="h-4 w-4 text-teal-500" />
```

- [ ] **Step 5.3: Icon `Wallet` header → emerald**

Old:

```tsx
                  <Wallet className="h-4 w-4 text-slate-400" />
```

New:

```tsx
                  <Wallet className="h-4 w-4 text-emerald-500" />
```

- [ ] **Step 5.4: Crown rank #1 → amber**

Old:

```tsx
                      <div
                        className={`h-7 w-7 rounded-full bg-slate-100 flex items-center justify-center text-xs font-medium shrink-0 ${
                          idx === 0 ? "text-slate-900" : "text-slate-500"
                        }`}
                      >
```

New:

```tsx
                      <div
                        className={`h-7 w-7 rounded-full flex items-center justify-center text-xs font-medium shrink-0 ${
                          idx === 0 ? "bg-amber-50 text-amber-600" : "bg-slate-100 text-slate-500"
                        }`}
                      >
```

- [ ] **Step 5.5: Verify**

Run (trong `frontend/mini-erp`): `npx tsc --noEmit`
Expected: exit 0.

- [ ] **Step 5.6: Commit**

```bash
git add src/features/dashboard/pages/DashboardPage.tsx
git commit -m "feat(dashboard): hue accents for approval tag, list headers, top rank"
```

---

### Task 6: Icon chip cho shortcuts

**Files:**

- Modify: `frontend/mini-erp/src/features/dashboard/pages/DashboardPage.tsx`

- [ ] **Step 6.1: Thêm field `chip` vào mảng `shortcuts`**

Old:

```tsx
  const shortcuts = [
    { label: "Bán lẻ (POS)", icon: ShoppingBag, to: "/orders/retail" },
    { label: "Nhập kho", icon: Warehouse, to: "/inventory/inbound" },
    { label: "Tồn kho", icon: Package, to: "/inventory/stock" },
    { label: "Báo cáo", icon: BarChart3, to: "/analytics/revenue" },
  ]
```

New:

```tsx
  const shortcuts = [
    { label: "Bán lẻ (POS)", icon: ShoppingBag, to: "/orders/retail", chip: "bg-sky-50 text-sky-600" },
    { label: "Nhập kho", icon: Warehouse, to: "/inventory/inbound", chip: "bg-violet-50 text-violet-600" },
    { label: "Tồn kho", icon: Package, to: "/inventory/stock", chip: "bg-amber-50 text-amber-600" },
    { label: "Báo cáo", icon: BarChart3, to: "/analytics/revenue", chip: "bg-indigo-50 text-indigo-600" },
  ]
```

- [ ] **Step 6.2: Render icon chip `h-9 w-9`**

Old:

```tsx
                <s.icon className="h-5 w-5 text-slate-600 shrink-0" />
```

New:

```tsx
                <div className={`h-9 w-9 rounded-md flex items-center justify-center shrink-0 ${s.chip}`}>
                  <s.icon className="h-[18px] w-[18px]" />
                </div>
```

- [ ] **Step 6.3: Verify**

Run (trong `frontend/mini-erp`): `npx tsc --noEmit`
Expected: exit 0.

- [ ] **Step 6.4: Commit**

```bash
git add src/features/dashboard/pages/DashboardPage.tsx
git commit -m "feat(dashboard): hue icon chips for quick shortcuts"
```

---

### Task 7: Verify tổng + build

**Files:** không sửa file.

- [ ] **Step 7.1: Type-check + production build**

Run (trong `frontend/mini-erp`): `npx tsc --noEmit && npm run build`
Expected: cả hai pass (build có warning chunk-size pre-existing — chấp nhận).

- [ ] **Step 7.2: Xác nhận không còn tham chiếu cũ**

Run (trong `frontend/mini-erp`): `npx tsc --noEmit` đã bao phủ; thêm grep xác nhận:

```bash
grep -n "statusDot\|text-slate-400\" />" src/features/dashboard/pages/DashboardPage.tsx
```

Expected: không còn `statusDot`; `text-slate-400" />` chỉ được phép xuất hiện 0 lần (Users/Wallet đã đổi màu, KPI icon trần đã bỏ).

- [ ] **Step 7.3: Manual QA checklist (cần mắt người — báo user chạy `npm run dev`)**

- 3 card tài chính: chip indigo/sky/emerald góc phải, số + trend không đổi, skeleton loading vẫn đúng hàng.
- 4 KPI: chip amber/sky/violet/emerald, hover vẫn đổi border, click điều hướng đúng.
- Chart: fill đậm hơn nhẹ, line dày 2px, tab active chữ indigo.
- Đơn hàng gần đây: pill trạng thái đúng map màu, tag Lẻ indigo / Sỉ emerald.
- Cần phê duyệt: tag loại phiếu violet, badge đỏ giữ nguyên.
- Top khách hàng: Users teal, crown vàng nền amber-50, rank 2-5 xám.
- Dòng tiền: Wallet emerald.
- Shortcuts: 4 chip sky/violet/amber/indigo.
- Role không tài chính (vd Staff): 3 card tài chính + chart ẩn, 3 KPI còn lại chip đúng màu.
