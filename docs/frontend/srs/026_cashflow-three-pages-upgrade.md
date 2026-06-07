# SRS-021 — Upgrade 3 giao diện Dòng tiền (Transactions · Debt · Ledger)

**Ngày:** 2026-06-06
**Tác giả:** SRS_WRITER (auto)
**Trạng thái:** Draft

---

## 1. Bối cảnh

Module `cashflow` có 3 trang:

| Route | Component | Tên hiển thị |
|-------|-----------|-------------|
| `/cashflow/transactions` | `TransactionsPage.tsx` | Giao dịch thu chi |
| `/cashflow/debt` | `DebtPage.tsx` | Sổ nợ đối tác |
| `/cashflow/ledger` | `LedgerPage.tsx` | Sổ cái tài chính |

Sau đợt nâng cấp các trang đặt hàng (SRS-018, SRS-019, SRS-020) đã có sẵn design pattern rõ ràng (pill-tabs toolbar, `DATA_TABLE_SHELL_CLASS`, `font-semibold` title, shadcn `<Button>` pagination). Ba trang cashflow hiện **chưa theo pattern đó** và có một số lỗi nghiêm trọng hơn (sử dụng mock data, thiếu filter).

---

## 2. Phân tích hiện trạng

### 2.1 TransactionsPage — Giao dịch thu chi

| ID | Khu vực | Vấn đề |
|----|---------|--------|
| T1 | Toolbar | Thiếu date range (`dateFrom` / `dateTo`) — API `getCashTransactionsList` đã hỗ trợ 2 param này |
| T2 | Toolbar | Dùng shadcn `<Select>` dropdown cho status & type filter — **inconsistent** với pill-tabs pattern đã dùng ở WholesalePage/OrderToolbar |
| T3 | Table | `StatusBadge` dùng cùng màu xám (`border-slate-200 bg-slate-50 text-slate-700`) cho **tất cả** trạng thái — không có visual differentiation |
| T4 | Stat cards | `totalIncome / totalExpense / balance` tính trên **trang hiện tại** (tối đa 20 dòng), footnote ghi rõ nhưng vị trí đặt ngay cạnh title gây hiểu nhầm |
| T5 | Stat cards | `min-w-[200px]` — non-canonical Tailwind (canonical: `min-w-50`) |
| T6 | Page title | `font-black uppercase` — inconsistent với redesigned pages dùng `font-semibold` |
| T7 | Pagination | Dùng raw `<button>` thay vì shadcn `<Button>` (WholesalePage dùng `<Button variant="outline" size="sm">`) |
| T8 | Delete | `window.confirm(...)` — native browser dialog, inconsistent với toàn codebase |
| T9 | Form | `TransactionFormDialog` tự tạo `transactionCode: TRANS-${timestamp}` — server nên generate, client không nên pre-fill |

### 2.2 DebtPage — Sổ nợ đối tác

| ID | Khu vực | Vấn đề |
|----|---------|--------|
| **D1** | **Data source** | **CRITICAL: `useState<Debt[]>(mockDebts)` — toàn bộ CRUD (create/edit/view) chạy trên local state giả. BE đã có `GET/POST/PATCH /api/v1/debts` (DebtsController.java).** |
| D2 | Table | Không có cột `dueDate` — dữ liệu có sẵn từ API, quan trọng để nhận biết khoản quá hạn |
| D3 | Pagination | Không có pagination — client filter `debts.filter(...)` trên toàn bộ state; khi migrate sang API phải thêm phân trang |
| D4 | Delete | `onDelete={(item) => toast.error('Yêu cầu xóa: ...')}` — hoàn toàn không làm gì; BE không có endpoint DELETE, cần bỏ nút Xóa hoặc đổi thành "Đánh dấu đã tất toán" (PATCH status → Cleared) |
| D5 | Toolbar | Thiếu date range (`dueDateFrom` / `dueDateTo`) — API hỗ trợ |
| D6 | Page title | `font-black uppercase` — inconsistent |
| D7 | Form | `DebtFormDialog.onSubmit: (data: any)` — mất type safety; form nhập tên đối tác plain text, không lookup từ customer/supplier list |

### 2.3 LedgerPage — Sổ cái tài chính

| ID | Khu vực | Vấn đề |
|----|---------|--------|
| L1 | Layout | `space-y-4 md:space-y-6` trên wrapper — inconsistent với pattern `flex flex-col gap-4 md:gap-5` của các trang khác |
| L2 | Toolbar | `LedgerToolbar` có `mb-4` **bên trong** bản thân component — spacing phải thuộc về parent container, không phải child component |
| L3 | Table | Không có summary totals row (tổng PS Nợ / PS Có cho kỳ đang lọc) |
| L4 | Page title | `font-semibold` ✓ đã đúng — nhưng toolbar layout vẫn dùng `h-11` cho inputs (canonical là `h-10`) |

---

## 3. Mục tiêu

1. **DebtPage**: Migrate từ mock data sang real API (`/api/v1/debts`).
2. **TransactionsPage**: Thêm date range filter + chuyển sang pill-tabs + sửa StatusBadge màu + đồng nhất layout.
3. **LedgerPage**: Sửa layout/spacing inconsistencies + xóa `mb-4` khỏi toolbar component.
4. Đồng nhất page title style (`font-semibold tracking-tight`, bỏ `uppercase font-black`) và pagination component (`<Button variant="outline" size="sm">`).

---

## 4. Phạm vi thay đổi

### Ngoài phạm vi

- Thêm detail dialog cho `LedgerEntry` (click vào row → navigate sang transaction) — có thể làm sau.
- Autocomplete partner name trong `DebtFormDialog` từ customer/supplier list — phức tạp, để riêng.
- Tính toán stat tổng toàn bộ (không phải per-page) cho TransactionsPage — cần BE endpoint mới.
- In chứng từ / In sao kê — các nút đó hiện chưa implement.

---

## 5. Yêu cầu chi tiết

### 5.1 Slice T — TransactionsPage

#### T-S1: Thêm date range filter vào `TransactionToolbar`

- Thêm props: `dateFrom?: string`, `onDateFromChange?: (v: string) => void`, `dateTo?: string`, `onDateToChange?: (v: string) => void`
- Render 2 `<Input type="date">` style giống `OrderToolbar` (variant `retailHistory`): `h-10 w-full sm:w-40 border-slate-200 rounded-md`
- Wire lên `TransactionsPage`: đặt state `dateFrom/dateTo`, đưa vào `filters` object truyền tới `getCashTransactionsList`
- Reset page về 1 khi thay đổi date

#### T-S2: Chuyển status + type filter sang pill-tabs

- Bỏ hai `<Select>` cho status / type trong toolbar
- Thêm 2 hàng pill tabs:
  - **Loại giao dịch**: `Tất cả` / `Thu tiền` / `Chi tiền` (value: `all / Income / Expense`)
  - **Trạng thái**: `Tất cả` / `Hoàn thành` / `Chờ xử lý` / `Đã huỷ` (value: `all / Completed / Pending / Cancelled`)
- Active pill: `bg-slate-900 text-white border-slate-900`; inactive: `bg-white text-slate-600 border-slate-200 hover:border-slate-400`

#### T-S3: Sửa `StatusBadge` trong `TransactionTable`

```tsx
// Trước: tất cả cùng class xám
// Sau:
if (status === "Completed") → bg-green-50 text-green-700 border-none
if (status === "Pending")   → bg-amber-50 text-amber-700 border-none
// default (Cancelled)      → bg-red-50 text-red-700 border-none
```

#### T-S4: Sửa layout & typography nhỏ

- Page title: bỏ `uppercase`, đổi `font-black` → `font-semibold tracking-tight`
- `StatCard`: `min-w-[200px]` → `min-w-50`
- Footnote stat cards: giữ nguyên text giải thích "Thống kê theo trang hiện tại" nhưng di chuyển vào tooltip hoặc ký hiệu `(i)` nhỏ thay vì paragraph dưới cards
- Pagination: đổi `<button>` thuần → `<Button variant="outline" size="sm">` từ shadcn
- Delete: đổi `window.confirm(...)` → shadcn `<Dialog>` confirm hoặc dùng `toast` với action button ("Xác nhận xóa") — **scope nhỏ**: dùng cách đơn giản nhất là `toast` với confirm action

#### T-S5: `TransactionFormDialog` — bỏ pre-fill transactionCode

- Bỏ `transactionCode: TRANS-${...}` khỏi defaultValues (BE sẽ generate)
- Không hiển thị field `transactionCode` trong form create (chỉ hiển thị ở edit mode dưới dạng read-only nếu cần)

---

### 5.2 Slice D — DebtPage (CRITICAL)

#### D-S1: Tạo `debtsApi.ts`

```typescript
// frontend/mini-erp/src/features/cashflow/api/debtsApi.ts
export const DEBTS_LIST_QUERY_KEY = ["debts", "list"] as const
export const DEBT_DETAIL_QUERY_KEY = ["debts", "detail"] as const

export type DebtListPageDto = {
  items: PartnerDebtItemDto[]
  page: number
  limit: number
  total: number
}

export type PartnerDebtItemDto = {
  id: number
  debtCode: string
  partnerType: "Customer" | "Supplier"
  customerId: number | null
  supplierId: number | null
  partnerName: string
  totalAmount: number
  paidAmount: number
  remainingAmount: number
  dueDate: string | null
  status: "InDebt" | "Cleared"
  notes: string | null
  createdAt: string
  updatedAt: string
}

export type GetDebtsListParams = {
  partnerType?: "Customer" | "Supplier"
  status?: "InDebt" | "Cleared"
  dueDateFrom?: string
  dueDateTo?: string
  search?: string
  page?: number
  limit?: number
}

export type DebtCreateBody = {
  partnerType: "Customer" | "Supplier"
  customerId?: number | null
  supplierId?: number | null
  totalAmount: number
  paidAmount?: number
  dueDate?: string | null
  notes?: string | null
}

export function getDebtsList(params: GetDebtsListParams = {}) { ... }
export function postDebt(body: DebtCreateBody) { ... }
export function getDebtById(id: number) { ... }
export function patchDebt(id: number, body: Record<string, unknown>) { ... }
```

**Lưu ý phân quyền**: `DebtsController` yêu cầu `FinanceLedgerAccessPolicy.assertCanViewFinanceLedger` → chỉ Admin mới truy cập được. `DebtPage` cần thêm guard tương tự `LedgerPage` (kiểm tra `role === "Admin"`, hiển thị thông báo nếu không đủ quyền).

#### D-S2: Tạo `useDebtsListQuery.ts`

```typescript
// frontend/mini-erp/src/features/cashflow/hooks/useDebtsListQuery.ts
export function useDebtsListQuery() {
  // Tương tự useRetailSalesHistoryListQuery:
  // - search debounce 400ms
  // - dateFrom/dateTo
  // - statusFilter: "all" | "InDebt" | "Cleared"
  // - partnerTypeFilter: "all" | "Customer" | "Supplier"
  // - page, PAGE_SIZE = 20
  // Returns: { debts, search, setSearch, ..., isListPending, isListError, total, totalPages }
}
```

#### D-S3: Migrate `DebtPage` sang real API

- Thay `useState<Debt[]>(mockDebts)` bằng `useDebtsListQuery()`
- `handleFormSubmit` gọi `postDebt(...)` (create) hoặc `patchDebt(id, ...)` (edit) thay vì setState
- Invalidate query key sau mỗi mutation thành công
- Thêm `isListPending` / `isListError` states (loading skeleton + error message)
- **Xóa nút "Xóa" khỏi toolbar** vì BE không có DELETE endpoint — `DebtsController` chỉ có GET/POST/PATCH

#### D-S4: Thêm cột `dueDate` vào `DebtTable`

- Thêm header `Hạn tất toán` (width `w-[120px]`)
- Cell: `{item.dueDate ? new Date(item.dueDate).toLocaleDateString('vi-VN') : '—'}`
- Nếu `dueDate < today && status !== "Cleared"`: thêm class `text-rose-600 font-semibold` để highlight quá hạn
- Cập nhật `colCount` trong bảng

#### D-S5: Thêm date range vào `DebtToolbar`

- Thêm props `dueDateFrom?`, `dueDateTo?`, `onDueDateFromChange?`, `onDueDateToChange?`
- Render 2 `<Input type="date">` style chuẩn (label nhỏ: "Hạn từ" / "Đến")
- Bỏ nút "Xóa" khỏi toolbar action buttons

#### D-S6: Sửa typography & pagination

- Page title: `font-black uppercase` → `font-semibold tracking-tight`
- Thêm pagination section (tương tự `WholesalePage`) bên dưới table
- `DebtFormDialog.onSubmit`: đổi `any` → `Record<string, unknown>`

---

### 5.3 Slice L — LedgerPage

#### L-S1: Sửa layout `LedgerPage`

```tsx
// Trước:
<div className="... space-y-4 md:space-y-6 h-full flex flex-col">

// Sau:
<div className="p-4 md:p-6 lg:p-8 flex flex-col h-full min-h-0 gap-4 md:gap-5 overflow-hidden">
```

#### L-S2: Xóa `mb-4` khỏi `LedgerToolbar`

```tsx
// Trước (dòng 1 của return):
<div className="flex flex-col gap-4 bg-white p-4 border border-slate-200 rounded-lg shrink-0 shadow-sm mb-4">

// Sau (bỏ mb-4):
<div className="flex flex-col gap-4 bg-white p-4 border border-slate-200 rounded-lg shrink-0 shadow-sm">
```

#### L-S3: Summary totals row trong `LedgerTable`

- Sau `</TableBody>` thêm `<TableFooter>` với 1 row:
  - Cột `Số tiền`: tổng (màu tùy theo dương/âm)
  - Cột `PS Nợ`: tổng debit (text-rose-600)
  - Cột `PS Có`: tổng credit (text-emerald-600)
  - Cột `Số dư`: `items[items.length - 1]?.balance ?? 0` (số dư cuối kỳ, in đậm)
  - Các cột còn lại: empty
- Chỉ render khi `data.length > 0`

---

## 6. Câu hỏi đã giải quyết

### Q1: DebtPage — quyền truy cập ✅
**Đọc `FinanceLedgerAccessPolicy.java`:** Có 2 phương thức tách biệt:
- `assertCanViewFinanceLedger(jwt, msg)` — chỉ cần JWT claim `can_view_finance = true` (không yêu cầu Admin)
- `assertFinanceLedgerAdminOnly(jwt, msg)` — cần `can_view_finance` **và** `role = Admin`

`DebtsController` dùng `assertCanViewFinanceLedger` (không phải Admin-only).
`FinanceLedgerController` dùng `assertFinanceLedgerAdminOnly` (Admin-only).

**Kết luận:** `DebtPage` KHÔNG cần admin guard panel. Sidebar không có `adminOnly` là đúng. Nếu user thiếu `can_view_finance`, BE trả 403 và FE sẽ toast error bình thường qua error handling của query.

### Q2: TransactionsPage — thay window.confirm ✅
Dùng **option (a)**: Sonner toast với `action: { label: "Xác nhận xóa", onClick: () => void deleteByIds(ids) }`.
Không cần thêm state, không cần AlertDialog component mới. Chuỗi xử lý: user click "Xóa" → toast("Xác nhận xóa X giao dịch?", { action: { label: "Xóa", onClick } }) → nếu confirm thì gọi `deleteByIds`.

---

## 7. Ma trận ưu tiên

| Slice | ID | Mô tả | Ưu tiên |
|-------|----|-------|---------|
| D | D-S1 | Tạo `debtsApi.ts` | **P0** |
| D | D-S2 | Hook `useDebtsListQuery` | **P0** |
| D | D-S3 | Migrate `DebtPage` → real API | **P0** |
| T | T-S1 | Date range filter TransactionToolbar | P1 |
| T | T-S2 | Pill tabs cho status/type | P1 |
| T | T-S3 | StatusBadge màu | P1 |
| D | D-S4 | Cột dueDate DebtTable | P1 |
| D | D-S5 | Date range DebtToolbar | P1 |
| L | L-S1 | Layout fix LedgerPage | P1 |
| L | L-S2 | Xóa mb-4 LedgerToolbar | P1 |
| T | T-S4 | Layout & typography nhỏ | P2 |
| T | T-S5 | Bỏ pre-fill transactionCode | P2 |
| D | D-S6 | Typography + pagination DebtPage | P2 |
| L | L-S3 | Summary totals row LedgerTable | P2 |
