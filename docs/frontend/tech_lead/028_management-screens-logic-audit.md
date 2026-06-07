# TECH SPEC 027 — Chuẩn hoá logic giao diện quản lý (SRS-023)

**Ngày:** 2026-06-07
**Tác giả:** TECH_SPEC_WRITER (auto)
**SRS tham chiếu:** `docs/frontend/srs/023_management-screens-logic-audit.md`
**Trạng thái:** READY_FOR_CODING

---

## 0. Owner Decisions áp dụng

Theo mặc định đề xuất trong SRS §7 — không cần phê duyệt thêm:

| OD | Quyết định áp dụng |
|----|-------------------|
| OD-1 | KPI chưa có summary API → đổi nhãn "trang hiện tại" (Slice 1b); ghi nợ kỹ thuật cần BE endpoint |
| OD-2 | Phân trang theo từng loại — infinite scroll giữ nguyên; PAGE_SIZE chuẩn hoá 20 |
| OD-3 | Cuốn chiếu: Phase 1 (🔴) → Phase 2 (🟠) → Phase 3 (🟡) |
| OD-4 | Tạo shared: `StatusBadge`, `toastApiError` |
| OD-5 | Ẩn nút giả (không "Sắp có") |
| OD-6 | `Pending` tách 2 nhãn: kho/duyệt = "Chờ duyệt"; tài chính/đơn hàng = "Chờ xử lý" |

---

## 1. Phạm vi & file bị ảnh hưởng

### Phase 1 — 🔴 Critical (R1, R2)

| Slice | File | Loại thay đổi |
|-------|------|--------------|
| 1a | `features/orders/pages/WholesalePage.tsx` | Sửa toolbar ẩn khi loading |
| 1b | `features/cashflow/pages/TransactionsPage.tsx` | Sửa bulk delete break + đổi nhãn KPI |
| 1c | `features/cashflow/pages/DebtPage.tsx` | Đổi nhãn KPI |

### Phase 2 — 🟠 UX/Bảo trì (R4, R6, R7, R8, R9)

| Slice | File | Loại thay đổi |
|-------|------|--------------|
| 2a (**mới**) | `components/shared/StatusBadge.tsx` | Tạo mới — shared component |
| 2a | `features/orders/components/OrderTable.tsx` | Xoá local StatusBadge, dùng shared |
| 2a | `features/cashflow/components/TransactionTable.tsx` | Xoá local StatusBadge, dùng shared |
| 2a | `features/cashflow/components/DebtTable.tsx` | Xoá local StatusBadge, dùng shared |
| 2a | `features/product-management/components/ProductTable.tsx` | Xoá inline Badge, dùng shared |
| 2a | `features/product-management/components/CategoryTable.tsx` | Xoá inline Badge, dùng shared; sửa "Ngưng"→"Ngừng" |
| 2a | `features/product-management/components/CustomerTable.tsx` | Xoá inline Badge, dùng shared |
| 2a | `features/product-management/components/SupplierTable.tsx` | Xoá inline Badge, dùng shared |
| 2b (**mới**) | `lib/api/toastApiError.ts` | Tạo mới — shared helper |
| 2b | `features/product-management/pages/ProductsPage.tsx` | Dùng helper chung |
| 2b | `features/product-management/pages/CategoriesPage.tsx` | Dùng helper chung |
| 2b | `features/approvals/pages/PendingApprovalsPage.tsx` | Dùng helper chung |
| 2b | `features/approvals/pages/ApprovalHistoryPage.tsx` | Dùng helper chung |
| 2b | `features/orders/hooks/useSalesOrdersListQuery.ts` | Dùng helper chung |
| 2c | `features/cashflow/pages/TransactionsPage.tsx` | Xoá nút Xuất Excel |
| 2c | `features/cashflow/pages/DebtPage.tsx` | Xoá nút Xuất Excel |
| 2c | `features/product-management/pages/ProductsPage.tsx` | Xoá nút Sửa hàng loạt |
| 2d | `features/approvals/pages/PendingApprovalsPage.tsx` | PAGE_SIZE 50→20 |
| 2e | `features/product-management/pages/ProductsPage.tsx` | Import layout constants |
| 2e | `features/cashflow/pages/TransactionsPage.tsx` | Import layout constants |
| 2e | `features/cashflow/pages/DebtPage.tsx` | Import layout constants |
| 2e | `features/product-management/pages/CategoriesPage.tsx` | Import layout constants |
| 2e | `features/approvals/pages/PendingApprovalsPage.tsx` | Import layout constants |

### Phase 3 — 🟡 Bảo trì (R8 footer, R11 misc) — Deferred

Tách thành task riêng sau khi Phase 1+2 ổn định. Không đưa vào handoff này.

---

## 2. Thiết kế chi tiết — Phase 1

### Slice 1a — WholesalePage: toolbar luôn hiển thị

**Vấn đề:** `OrderToolbar` nằm bên trong nhánh success → ẩn khi `isListPending || isListError`.

**File:** `frontend/mini-erp/src/features/orders/pages/WholesalePage.tsx`

**Trước (dòng 80-110):**
```tsx
<div className={DATA_TABLE_SHELL_CLASS}>
  {isListPending ? (
    <div ...>Đang tải...</div>
  ) : isListError ? (
    <div ...>Không tải được...</div>
  ) : (
    <>
      <OrderToolbar ... />
      <div className={DATA_TABLE_SCROLL_CLASS}>
        <OrderTable ... />
      </div>
      {/* footer */}
    </>
  )}
</div>
```

**Sau:**
```tsx
<div className={DATA_TABLE_SHELL_CLASS}>
  <OrderToolbar ... />            {/* ← luôn render */}
  {isListPending ? (
    <div className="p-8 text-center text-slate-500 flex-1" role="status">
      Đang tải lịch sử hóa đơn...
    </div>
  ) : isListError ? (
    <div className="p-8 text-center text-red-600 flex-1" role="alert">
      Không tải được lịch sử hóa đơn.
    </div>
  ) : (
    <>
      <div className={DATA_TABLE_SCROLL_CLASS}>
        <OrderTable ... />
      </div>
      {/* footer phân trang */}
    </>
  )}
</div>
```

> Không thay đổi props hay logic filter — chỉ thay đổi vị trí render trong cây JSX.

---

### Slice 1b — TransactionsPage: sửa bulk delete break + nhãn KPI

#### 1b-i: Sửa `deleteByIds` — thay `break` bằng `continue`

**File:** `frontend/mini-erp/src/features/cashflow/pages/TransactionsPage.tsx:216-244`

```ts
// TRƯỚC
const deleteByIds = async (ids: number[]) => {
  const successfulIds: number[] = []
  for (const id of ids) {
    try {
      await deleteCashTransaction(id)
      successfulIds.push(id)
      queryClient.removeQueries(...)
    } catch (e) {
      if (e instanceof ApiRequestError) toast.error(...)
      else toast.error(...)
      break  // ← BUG: dừng giữa chừng, item sau không được xử lý
    }
  }
  if (successfulIds.length > 0) { ... }
}

// SAU
const deleteByIds = async (ids: number[]) => {
  const successfulIds: number[] = []
  const failedCount = { n: 0 }
  for (const id of ids) {
    try {
      await deleteCashTransaction(id)
      successfulIds.push(id)
      queryClient.removeQueries({ queryKey: [...CASH_TRANSACTION_DETAIL_QUERY_KEY, id] })
    } catch (e) {
      failedCount.n++
      toastApiError(e, "Không xóa được giao dịch")
      // tiếp tục với item tiếp theo
    }
  }
  if (successfulIds.length > 0) {
    await queryClient.invalidateQueries({ queryKey: [...CASH_TRANSACTIONS_LIST_QUERY_KEY] })
    const msg = failedCount.n > 0
      ? `Đã xóa ${successfulIds.length} giao dịch, thất bại ${failedCount.n}`
      : successfulIds.length === 1 ? "Đã xóa giao dịch" : `Đã xóa ${successfulIds.length} giao dịch`
    toast.success(msg)
    const removed = new Set(successfulIds)
    setSelectedIds((prev) => prev.filter((id) => !removed.has(id)))
    if (selectedItem && removed.has(selectedItem.id)) {
      setSelectedItem(null)
      setIsDetailOpen(false)
      setIsFormOpen(false)
    }
  }
}
```

#### 1b-ii: Đổi nhãn thẻ KPI page-scoped

**File:** `frontend/mini-erp/src/features/cashflow/pages/TransactionsPage.tsx:355-374`

Thay label trong 3 `StatCard`:
- `"Tổng thu"` → `"Thu (trang này)"`
- `"Tổng chi"` → `"Chi (trang này)"`
- `"Số dư"` → `"Chênh lệch (trang này)"`

Xoá icon `Info` + tooltip (`:367-372`) vì nhãn đã tự mô tả phạm vi. Thêm comment code ghi nợ kỹ thuật:
```ts
// TODO: replace with summary API endpoint when available (SRS-023/OD-1)
```

---

### Slice 1c — DebtPage: đổi nhãn KPI page-scoped

**File:** `frontend/mini-erp/src/features/cashflow/pages/DebtPage.tsx:89-91, 201-221`

Thay label 3 `StatCard`:
- `"Nợ phải thu"` → `"Phải thu (trang này)"`
- `"Nợ phải trả"` → `"Phải trả (trang này)"`
- `"Quá hạn"` → `"Quá hạn (trang này)"`

Thêm comment ghi nợ kỹ thuật tương tự.

---

## 3. Thiết kế chi tiết — Phase 2

### Slice 2a — Shared StatusBadge

**Tạo file mới:** `frontend/mini-erp/src/components/shared/StatusBadge.tsx`

```tsx
import { Badge } from "@/components/ui/badge"

type StatusConfig = {
  label: string
  bg: string
  text: string
  border: string
  dot: string
}

// Chuẩn màu toàn project:
// Tích cực / hoàn thành  → emerald
// Chờ / pending          → amber
// Đang xử lý / in-flight → blue
// Cảnh báo nhẹ           → orange
// Huỷ / lỗi / từ chối   → rose
// Không xác định / nháp → slate

const STATUS_CONFIG: Record<string, StatusConfig> = {
  // ── Chung ──────────────────────────────────────────────────
  Active:    { label: "Hoạt động", bg: "bg-emerald-100", text: "text-emerald-700", border: "border-emerald-200", dot: "bg-emerald-500" },
  Inactive:  { label: "Ngừng",     bg: "bg-slate-100",   text: "text-slate-500",   border: "border-slate-200",   dot: "bg-slate-400" },

  // ── Phiếu kho ─────────────────────────────────────────────
  Draft:     { label: "Nháp",      bg: "bg-slate-100",   text: "text-slate-600",   border: "border-slate-300",   dot: "bg-slate-400" },
  Pending:   { label: "Chờ duyệt", bg: "bg-amber-100",   text: "text-amber-700",   border: "border-amber-200",   dot: "bg-amber-400" },
  Approved:  { label: "Đã duyệt",  bg: "bg-emerald-100", text: "text-emerald-700", border: "border-emerald-200", dot: "bg-emerald-500" },
  Rejected:  { label: "Từ chối",   bg: "bg-rose-100",    text: "text-rose-600",    border: "border-rose-200",    dot: "bg-rose-400" },

  // ── Phiếu xuất kho ────────────────────────────────────────
  WaitingDispatch: { label: "Chờ xuất kho",  bg: "bg-amber-100",   text: "text-amber-700",   border: "border-amber-200",   dot: "bg-amber-400" },
  Delivering:      { label: "Đang xuất kho", bg: "bg-blue-50",     text: "text-blue-600",    border: "border-blue-200",    dot: "bg-blue-400" },
  Delivered:       { label: "Đã giao hàng",  bg: "bg-emerald-100", text: "text-emerald-700", border: "border-emerald-200", dot: "bg-emerald-500" },
  Full:            { label: "Đã xuất đủ",    bg: "bg-emerald-100", text: "text-emerald-700", border: "border-emerald-200", dot: "bg-emerald-500" },
  Partial:         { label: "Xuất một phần", bg: "bg-amber-100",   text: "text-amber-700",   border: "border-amber-200",   dot: "bg-amber-400" },
  Cancelled:       { label: "Đã hủy",        bg: "bg-rose-100",    text: "text-rose-600",    border: "border-rose-200",    dot: "bg-rose-400" },

  // ── Kiểm kê ───────────────────────────────────────────────
  "In Progress":            { label: "Đang kiểm",       bg: "bg-blue-50",     text: "text-blue-600",    border: "border-blue-200",    dot: "bg-blue-400" },
  "Pending Owner Approval": { label: "Chờ duyệt Owner", bg: "bg-amber-100",   text: "text-amber-700",   border: "border-amber-200",   dot: "bg-amber-400" },
  Completed:                { label: "Hoàn thành",      bg: "bg-emerald-100", text: "text-emerald-700", border: "border-emerald-200", dot: "bg-emerald-500" },
  "Re-check":               { label: "Kiểm lại",        bg: "bg-orange-50",   text: "text-orange-600",  border: "border-orange-200",  dot: "bg-orange-400" },

  // ── Tồn kho ───────────────────────────────────────────────
  "in-stock":      { label: "Còn hàng",    bg: "bg-emerald-100", text: "text-emerald-700", border: "border-emerald-200", dot: "bg-emerald-500" },
  "low-stock":     { label: "Sắp hết",     bg: "bg-amber-100",   text: "text-amber-700",   border: "border-amber-200",   dot: "bg-amber-400" },
  "out-of-stock":  { label: "Hết hàng",    bg: "bg-rose-100",    text: "text-rose-600",    border: "border-rose-200",    dot: "bg-rose-400" },
  "expiring-soon": { label: "Sắp hết hạn", bg: "bg-orange-50",   text: "text-orange-600",  border: "border-orange-200",  dot: "bg-orange-400" },

  // ── Đơn hàng (OD-6: Pending ngữ cảnh order = "Chờ xử lý") ─
  Processing: { label: "Đang xử lý",   bg: "bg-indigo-50",   text: "text-indigo-600",  border: "border-indigo-200",  dot: "bg-indigo-400" },
  Shipped:    { label: "Đang giao",     bg: "bg-blue-50",     text: "text-blue-600",    border: "border-blue-200",    dot: "bg-blue-400" },
  // "Completed" đã có ở trên
  // "Cancelled" đã có ở trên

  // ── Giao dịch tài chính (OD-6: Pending ngữ cảnh finance = "Chờ xử lý") ─
  // Dùng prop variant để phân biệt (xem bên dưới)

  // ── Sổ nợ ─────────────────────────────────────────────────
  Cleared:   { label: "Đã tất toán", bg: "bg-emerald-100", text: "text-emerald-700", border: "border-emerald-200", dot: "bg-emerald-500" },
  Overdue:   { label: "Quá hạn",     bg: "bg-rose-100",    text: "text-rose-600",    border: "border-rose-200",    dot: "bg-rose-400" },
  Active_debt: { label: "Còn nợ",    bg: "bg-amber-100",   text: "text-amber-700",   border: "border-amber-200",   dot: "bg-amber-400" },
}

// Nhãn Pending theo ngữ cảnh (OD-6)
const PENDING_LABEL: Record<string, string> = {
  finance: "Chờ xử lý",
  order:   "Chờ xử lý",
  default: "Chờ duyệt",
}

interface StatusBadgeProps {
  status: string
  /** Ngữ cảnh để phân biệt nhãn "Pending": "finance" | "order" | "warehouse" | "audit" */
  context?: "finance" | "order" | "warehouse" | "audit"
  /** Phiếu xuất: Partial kèm cảnh báo thiếu tồn → nhãn riêng */
  shortageWarning?: boolean
}

export function StatusBadge({ status, context, shortageWarning }: StatusBadgeProps) {
  let cfg = STATUS_CONFIG[status]

  // Pending với nhãn theo ngữ cảnh (OD-6)
  if (status === "Pending" && context) {
    const label = context === "finance" || context === "order"
      ? PENDING_LABEL.finance
      : PENDING_LABEL.default
    cfg = { ...STATUS_CONFIG["Pending"]!, label }
  }

  // Phiếu xuất thiếu hàng
  if (status === "Partial" && shortageWarning) {
    cfg = { label: "Thiếu hàng cần xử lý", bg: "bg-rose-100", text: "text-rose-600", border: "border-rose-200", dot: "bg-rose-400" }
  }

  if (!cfg) {
    cfg = { label: status, bg: "bg-slate-100", text: "text-slate-600", border: "border-slate-200", dot: "bg-slate-400" }
  }

  return (
    <Badge className={`${cfg.bg} ${cfg.text} ${cfg.border} font-semibold text-xs border shadow-none gap-1.5`}>
      <span className={`w-1.5 h-1.5 rounded-full inline-block shrink-0 ${cfg.dot}`} />
      {cfg.label}
    </Badge>
  )
}
```

**Các thay đổi trong bảng (pattern giống nhau cho tất cả):**

```tsx
// XOÁ: local StatusBadge function definition
// THÊM import:
import { StatusBadge } from "@/components/shared/StatusBadge"

// OrderTable — thêm prop context:
<StatusBadge status={item.status} context="order" />

// TransactionTable:
<StatusBadge status={item.status} context="finance" />

// DebtTable — status "Active" → dùng key "Active_debt":
<StatusBadge status={item.status === "Active" ? "Active_debt" : item.status} />

// ProductTable / CategoryTable / CustomerTable / SupplierTable:
<StatusBadge status={item.status} />
// (Active/Inactive mapping tự động từ config)
```

> **Lưu ý CategoryTable:** xoá bản inline badge và xoá lỗi typo "Ngưng" — `STATUS_CONFIG.Inactive` dùng "Ngừng" (đúng chuẩn).

**File inventory/components/StatusBadge.tsx:** giữ nguyên nhưng re-export từ shared để không break import cũ:
```ts
// inventory/components/StatusBadge.tsx — chỉ re-export, không xoá file
export { StatusBadge } from "@/components/shared/StatusBadge"
```

---

### Slice 2b — Shared `toastApiError`

**Tạo file mới:** `frontend/mini-erp/src/lib/api/toastApiError.ts`

```ts
import { toast } from "sonner"
import { ApiRequestError } from "./http"

/** Hiển thị toast lỗi từ bất kỳ exception nào, ưu tiên message từ API. */
export function toastApiError(e: unknown, fallback = "Đã xảy ra lỗi"): void {
  if (e instanceof ApiRequestError) {
    toast.error(e.body?.message ?? e.message)
  } else {
    toast.error(e instanceof Error ? e.message : fallback)
  }
}

/**
 * Toast lỗi cho mutation có API envelope (400/403/409 + details).
 * - 400 + details có key → im lặng (form tự setError).
 * - 409 → hiện message server.
 * - 403 / 400 không details → hiện message server.
 * - Còn lại → toastApiError.
 */
export function toastMutationEnvelope(e: unknown): void {
  if (!(e instanceof ApiRequestError)) {
    toastApiError(e)
    return
  }
  const { status, body } = e
  const detailKeys = body?.details ? Object.keys(body.details) : []
  if (status === 400 && detailKeys.length > 0) return
  if (status === 409 || status === 403) {
    toast.error(body?.message ?? e.message)
    return
  }
  if (status === 400) {
    toast.error(body?.message ?? e.message)
    return
  }
  toastApiError(e)
}
```

**Thay thế trong các file (xoá local `errToast`, dùng import):**

| File | Thay thế |
|------|---------|
| `ProductsPage.tsx:57-93` | Xoá `errToast` + `toastProductMutationEnvelope`; import `toastApiError`, `toastMutationEnvelope` |
| `CategoriesPage.tsx:39-79` | Xoá `errToast` + `toastCategoryMutationEnvelope`; import |
| `PendingApprovalsPage.tsx:38-44` | Xoá local `errToast`; import `toastApiError` |
| `ApprovalHistoryPage.tsx:23-29` | Xoá local `errToast`; import `toastApiError` |
| `useSalesOrdersListQuery.ts:18-24` | Xoá local `errToast`; import `toastApiError` |
| `TransactionsPage.tsx` (inline catches) | Thay `if (e instanceof ApiRequestError) toast.error(...) else ...` bằng `toastApiError(e, "...")` |
| `DebtPage.tsx` (inline catches) | Tương tự |
| `StockPage.tsx` (inline catches) | Tương tự |

> **Không thay đổi logic** — chỉ di chuyển code vào helper dùng chung. Hành vi toast y hệt.

---

### Slice 2c — Xoá nút giả

#### TransactionsPage — xoá "Xuất Excel"
**File:** `features/cashflow/pages/TransactionsPage.tsx`
- `handleToolbarAction` case `"export"`: xoá case hoàn toàn.
- Toolbar component `TransactionToolbar`: xoá nút/option "export" khỏi UI (nếu render từ config array, xoá phần tử; nếu hardcode JSX, xoá `<button>`).

#### DebtPage — xoá "Xuất Excel"
**File:** `features/cashflow/pages/DebtPage.tsx`
- `handleToolbarAction` case `"export"`: xoá case.
- `DebtToolbar`: xoá nút export.

#### ProductsPage — xoá "Chỉnh sửa hàng loạt"
**File:** `features/product-management/pages/ProductsPage.tsx:364-366`
- `handleToolbarAction` case `"edit"`: xoá case.
- `ProductToolbar`: xoá nút/tuỳ chọn bulk edit.

---

### Slice 2d — PAGE_SIZE chuẩn hoá

**File:** `features/approvals/pages/PendingApprovalsPage.tsx:33`
```ts
// TRƯỚC
const PAGE_SIZE = 50
// SAU
const PAGE_SIZE = 20
```

> Không thay đổi logic — chỉ thay hằng số.

---

### Slice 2e — Import layout constants

**Pattern áp dụng cho 5 file (ProductsPage, TransactionsPage, DebtPage, CategoriesPage, PendingApprovalsPage):**

```tsx
// THÊM import nếu chưa có:
import { DATA_TABLE_SHELL_CLASS, DATA_TABLE_SCROLL_CLASS } from "@/lib/data-table-layout"

// THAY THẾ chuỗi class copy tay:
// "flex-1 flex flex-col min-h-0 bg-white border border-slate-200/60 rounded-xl overflow-hidden shadow-md"
// → DATA_TABLE_SHELL_CLASS

// "flex-1 overflow-y-auto relative scroll-smooth [scrollbar-gutter:stable] min-h-0"
// → DATA_TABLE_SCROLL_CLASS
```

**Footer phân trang — chuẩn hoá 1 variant duy nhất (lấy pattern từ WholesalePage):**
```tsx
<div className="flex items-center justify-between flex-wrap gap-2 px-3 py-2 border-t border-slate-200 bg-slate-50/80 text-sm text-slate-600 min-h-11 shrink-0">
```
Thay variant `px-4 py-2 text-xs font-bold` ở TransactionsPage và DebtPage thành variant trên.

---

## 4. Horizontal analysis

| Rủi ro | File bị ảnh hưởng | Biện pháp |
|--------|------------------|-----------|
| `inventory/components/StatusBadge.tsx` bị import ở nhiều nơi — nếu xoá thì break | `DispatchTable.tsx`, `ReceiptTable.tsx`, `AuditSessionsTable.tsx`, `StockTable.tsx` | Re-export từ shared thay vì xoá file |
| `toastMutationEnvelope` mới có thể ẩn lỗi 400+details khác với bản cũ (CategoryPage có thêm logic join details) | `CategoriesPage.tsx` | Kiểm tra `body.details` join logic — nếu khác thì giữ nguyên `toastCategoryMutationEnvelope` local, chỉ thay `errToast` |
| WholesalePage toolbar hiển thị khi `isListError` → filter state còn nhưng không có data → có thể confuse | `WholesalePage.tsx` | Disable sort/filter input khi error không cần thiết — giữ enable để user thử filter khác |
| TransactionsPage `deleteByIds` loop: nếu BE retry làm double-delete thì cần idempotency | `TransactionsPage.tsx` | Không thêm retry — chỉ sửa break→continue; idempotency là vấn đề BE |
| Nhãn "Trang này" trên StatCard: user cũ đã quen đọc "Tổng thu" → có thể ngạc nhiên | `TransactionsPage`, `DebtPage` | Chấp nhận — nhãn cũ gây hiểu nhầm số liệu, đổi là bắt buộc |

---

## 5. Thứ tự triển khai (coding handoff)

```
Phase 1:
  [P1-1] Slice 2b — Tạo lib/api/toastApiError.ts  (dependency của nhiều slice khác)
  [P1-2] Slice 2a — Tạo components/shared/StatusBadge.tsx
  [P1-3] Slice 1a — WholesalePage toolbar fix
  [P1-4] Slice 1b — TransactionsPage bulk delete + nhãn KPI
  [P1-5] Slice 1c — DebtPage nhãn KPI

Phase 2:
  [P2-1] Slice 2a — Replace local StatusBadge trong 7 bảng (dùng shared)
  [P2-2] Slice 2b — Replace inline errToast trong 8 file (dùng helper)
  [P2-3] Slice 2c — Xoá 3 nút giả (Transactions, Debt, Products)
  [P2-4] Slice 2d — PAGE_SIZE PendingApprovals
  [P2-5] Slice 2e — Import layout constants 5 file
```

> Bắt buộc làm P1-1 và P1-2 **trước** vì các slice sau import từ chúng.

---

## 6. Định nghĩa hoàn thành (DoD)

- [ ] `lib/api/toastApiError.ts` tồn tại, export `toastApiError` + `toastMutationEnvelope`.
- [ ] `components/shared/StatusBadge.tsx` tồn tại, bao phủ tất cả status value trong §3a.
- [ ] `inventory/components/StatusBadge.tsx` re-export từ shared (không xoá file).
- [ ] WholesalePage: toolbar hiển thị khi đang tải và khi lỗi.
- [ ] TransactionsPage `deleteByIds`: không có `break` trong catch — toàn bộ id được xử lý.
- [ ] Nhãn KPI TransactionsPage và DebtPage chứa "(trang này)".
- [ ] Không còn local `StatusBadge` function trong OrderTable, TransactionTable, DebtTable.
- [ ] Không còn inline Badge ternary cho status trong ProductTable, CategoryTable, CustomerTable, SupplierTable.
- [ ] CategoryTable hiển thị "Ngừng" (không phải "Ngưng").
- [ ] Không còn local `errToast` trong ProductsPage, CategoriesPage, PendingApprovalsPage, ApprovalHistoryPage, useSalesOrdersListQuery.
- [ ] Không có nút "Xuất Excel" (Transactions, Debt) hay "Chỉnh sửa hàng loạt" (Products) trên UI.
- [ ] PendingApprovalsPage `PAGE_SIZE = 20`.
- [ ] 5 file dùng `DATA_TABLE_SHELL_CLASS` / `DATA_TABLE_SCROLL_CLASS` import từ `data-table-layout.ts`.
- [ ] TypeScript compile không có lỗi mới.

---

**Readiness:** `READY_FOR_CODING`

**CodeGraph:** status (855 files, sẵn sàng) + explore (StatusBadge, errToast, ConfirmDialog, DATA_TABLE_SHELL_CLASS).
**Superpowers:** writing-plans (exact files + bite-sized slices + no placeholders).
