# TECH SPEC 024 — Invoice History Upgrade (SRS-020)

**Ngày:** 2026-06-06
**SRS:** `docs/frontend/srs/020_invoice-history-upgrade.md`
**Superpowers:** writing-plans

---

## 0. CodeGraph preflight

Đã đọc trực tiếp các file nguồn liên quan trong session này:
- `WholesalePage.tsx` — page chính
- `OrderToolbar.tsx` — variant `retailHistory`
- `OrderTable.tsx` — cột hiện tại + props
- `OrderDetailDialog.tsx` — hardcode data + props
- `useRetailSalesHistoryListQuery.ts` — hook state
- `salesOrdersApi.ts` — types `SalesOrderDetailDto`
- `data-table-layout.ts` — `ORDER_TABLE_COL`

---

## 1. Phạm vi file

| # | File | Loại |
|---|------|------|
| S1 | `features/orders/hooks/useRetailSalesHistoryListQuery.ts` | Sửa |
| S2 | `features/orders/components/OrderToolbar.tsx` | Sửa |
| S3 | `features/orders/components/OrderTable.tsx` | Sửa |
| S4 | `features/orders/components/OrderDetailDialog.tsx` | Sửa |
| S5 | `features/orders/pages/WholesalePage.tsx` | Sửa |

---

## 2. Implementation slices

### Slice S1 — Hook: thêm `statusFilter` + `paymentStatusFilter` client-side

File: `useRetailSalesHistoryListQuery.ts`

Thêm 2 state mới:
```ts
const [statusFilter, setStatusFilter] = useState<"all" | "Delivered" | "Cancelled">("all")
const [paymentStatusFilter, setPaymentStatusFilter] = useState<"all" | "Paid" | "Unpaid" | "Partial">("all")
```

Thêm `filteredOrders` bằng `useMemo` SAU khi `orders` được tính:
```ts
const filteredOrders = useMemo(
  () =>
    orders
      .filter((o) => statusFilter === "all" || o.status === statusFilter)
      .filter((o) => paymentStatusFilter === "all" || o.paymentStatus === paymentStatusFilter),
  [orders, statusFilter, paymentStatusFilter],
)
```

Return object — thêm:
```ts
return {
  ...existing,
  orders: filteredOrders,        // thay orders gốc bằng filteredOrders
  statusFilter,
  setStatusFilter,
  paymentStatusFilter,
  setPaymentStatusFilter,
}
```

> `total` giữ nguyên từ API (không filter total count — đây là client-side filter).

---

### Slice S2 — Toolbar: refactor variant `retailHistory`

File: `OrderToolbar.tsx`

**Thêm imports:** `cn` từ `@/lib/utils`.

**Thêm props vào `OrderToolbarProps`:**
```ts
statusFilter?: string
onStatusFilterChange?: (val: string) => void
paymentStatusFilter?: string
onPaymentStatusFilterChange?: (val: string) => void
sort?: string
onSortChange?: (val: string) => void
sortWhitelist?: readonly string[]
getSortLabel?: (s: string) => string
```

**Thêm constants trong file (trước function):**
```ts
const RETAIL_HISTORY_STATUS_FILTERS = [
  { value: "all",       label: "Tất cả" },
  { value: "Delivered", label: "Hoàn thành" },
  { value: "Cancelled", label: "Đã huỷ" },
] as const

const RETAIL_HISTORY_PAYMENT_FILTERS = [
  { value: "all",     label: "Tất cả" },
  { value: "Paid",    label: "Đã TT" },
  { value: "Unpaid",  label: "Chưa TT" },
  { value: "Partial", label: "Một phần" },
] as const
```

**Sửa toàn bộ branch `variant === "retailHistory"`:**

```tsx
if (variant === "retailHistory") {
  return (
    <div className="bg-white p-4 border border-slate-200 rounded-lg shrink-0 shadow-sm flex flex-col gap-3">
      {/* Dòng 1: search + date range */}
      <div className="flex flex-col lg:flex-row gap-3 w-full flex-wrap">
        <div className="relative flex-1 min-w-[200px] group">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 group-focus-within:text-blue-600 transition-colors" />
          <Input
            placeholder="Tìm theo mã đơn hoặc tên KH..."
            value={searchStr}
            onChange={(e) => onSearch(e.target.value)}
            className="pl-10 h-10 border-slate-200 focus:border-slate-400 focus:ring-slate-100 transition-all rounded-md"
          />
        </div>
        <div className="flex flex-col sm:flex-row gap-2 sm:items-center">
          <Input
            type="date"
            value={dateFrom}
            onChange={(e) => onDateFromChange?.(e.target.value)}
            className="h-10 w-full sm:w-[156px] border-slate-200 rounded-md"
          />
          <span className="text-slate-400 text-sm hidden sm:block">–</span>
          <Input
            type="date"
            value={dateTo}
            onChange={(e) => onDateToChange?.(e.target.value)}
            className="h-10 w-full sm:w-[156px] border-slate-200 rounded-md"
          />
        </div>
      </div>

      {/* Dòng 2: status pill tabs */}
      <div className="flex items-center gap-1.5 flex-wrap">
        {RETAIL_HISTORY_STATUS_FILTERS.map((f) => (
          <button
            key={f.value}
            type="button"
            onClick={() => onStatusFilterChange?.(f.value)}
            className={cn(
              "h-8 px-3 rounded-full text-sm font-medium transition-colors border shrink-0",
              (statusFilter ?? "all") === f.value
                ? "bg-slate-900 text-white border-slate-900"
                : "bg-white text-slate-600 border-slate-200 hover:border-slate-400 hover:text-slate-900",
            )}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Dòng 3: payment pill tabs + sort */}
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-1.5 flex-wrap">
          {RETAIL_HISTORY_PAYMENT_FILTERS.map((f) => (
            <button
              key={f.value}
              type="button"
              onClick={() => onPaymentStatusFilterChange?.(f.value)}
              className={cn(
                "h-8 px-3 rounded-full text-sm font-medium transition-colors border shrink-0",
                (paymentStatusFilter ?? "all") === f.value
                  ? "bg-slate-900 text-white border-slate-900"
                  : "bg-white text-slate-600 border-slate-200 hover:border-slate-400 hover:text-slate-900",
              )}
            >
              {f.label}
            </button>
          ))}
        </div>
        {sortWhitelist && sort && onSortChange && (
          <select
            value={sort}
            onChange={(e) => onSortChange(e.target.value)}
            className="h-8 px-2 border border-slate-200 bg-white rounded-md text-sm text-slate-900 min-w-[200px]"
          >
            {sortWhitelist.map((s) => (
              <option key={s} value={s}>
                {getSortLabel?.(s) ?? s}
              </option>
            ))}
          </select>
        )}
      </div>
    </div>
  )
}
```

---

### Slice S3 — Table: paymentStatus column + status column + bỏ TypeBadge

File: `OrderTable.tsx`

**3a. Thêm `paymentStatusFilter` và `hideTypeBadge` prop (optional):**
```ts
interface OrderTableProps {
  // ...existing...
  /** SRS-020: hiện cột trạng thái (không truyền hideStatusColumn nữa từ WholesalePage). */
  hideStatusColumn?: boolean
  /** SRS-020: ẩn TypeBadge trên dòng khách hàng (endpoint chỉ trả 1 loại). */
  hideTypeBadge?: boolean
}
```

**3b. Sửa `colCount` để tính đúng:**
```ts
const colCount =
  (showCheckbox ? 1 : 0) +
  4 + // code, customer, date, total
  1 + // paymentStatus (luôn có)
  (hideStatusColumn ? 0 : 1) +
  1 // actions
```

**3c. Thêm `PaymentBadge` component:**
```tsx
function PaymentBadge({ status }: { status: string }) {
  if (status === "Paid")
    return <Badge className="bg-green-50 text-green-700 text-xs border-none font-normal">Đã TT</Badge>
  if (status === "Partial")
    return <Badge className="bg-amber-50 text-amber-700 text-xs border-none font-normal">Một phần</Badge>
  return <Badge className="bg-red-50 text-red-700 text-xs border-none font-normal">Chưa TT</Badge>
}
```

**3d. Header row — thêm cột "Thanh toán" sau "Thành tiền", trước status:**
```tsx
<TableHead className={cn(ORDER_TABLE_COL.payment, TABLE_HEAD_CLASS, "px-4")}>Thanh toán</TableHead>
```

**3e. Sửa dòng customer cell — thêm prop `hideTypeBadge`:**
```tsx
<TableCell className={cn(ORDER_TABLE_COL.customer, "px-4 min-w-0")}>
  <div className="flex min-w-0 flex-col gap-1">
    <span className={cn(TABLE_CELL_PRIMARY_CLASS, "block min-w-0 truncate")}>{item.customerName}</span>
    <div className="flex gap-1 items-center">
      {!hideTypeBadge && <TypeBadge type={item.type} />}
      <span className={cn(TABLE_CELL_MONO_CLASS, "text-[10px] text-slate-400")}>
        {!hideTypeBadge && "• "}{item.itemsCount} mặt hàng
      </span>
    </div>
  </div>
</TableCell>
```

**3f. Data rows — thêm PaymentBadge cell sau total:**
```tsx
<TableCell className={cn(ORDER_TABLE_COL.payment, "px-4")}>
  <PaymentBadge status={item.paymentStatus} />
</TableCell>
```

---

### Slice S4 — OrderDetailDialog: fix hardcode + thêm `detailDto` prop

File: `OrderDetailDialog.tsx`

**4a. Import thêm type + icon:**
```ts
import type { SalesOrderDetailDto } from "../api/salesOrdersApi"
import { Tag, Store } from "lucide-react"
```

**4b. Thêm prop:**
```ts
interface OrderDetailDialogProps {
  // ...existing...
  /** SRS-020: DTO đầy đủ để hiển thị shippingAddress, cancelledAt, voucherCode, posShiftRef. */
  detailDto?: SalesOrderDetailDto
}
```

**4c. Sửa ô "Địa điểm giao hàng"** (hiện hardcode):
```tsx
// Thay toàn bộ nội dung div:
{detailDto?.shippingAddress?.trim() || "Tại cửa hàng (POS)"}
```

**4d. Đổi ô "Phương thức thanh toán" → "Trạng thái thanh toán"**:
```tsx
// Label:
<Label>...<CreditCard size={12} /> Trạng thái thanh toán</Label>
// Value:
{{
  Paid: "Đã thanh toán",
  Unpaid: "Chưa thanh toán",
  Partial: "Thanh toán một phần",
}[order.paymentStatus] ?? order.paymentStatus}
```

**4e. Sửa Progress tracker — wrap thành conditional:**
```tsx
{order.status === "Cancelled" ? (
  <div className="flex items-center gap-3 bg-red-50 border border-red-100 rounded-xl p-4 mb-12">
    <XCircle size={20} className="text-red-500 shrink-0" />
    <div>
      <p className="font-semibold text-sm text-red-700">Đơn hàng đã bị huỷ</p>
      {detailDto?.cancelledAt && (
        <p className="text-xs text-red-500 mt-0.5">
          Thời điểm huỷ: {formatDate(detailDto.cancelledAt)}
        </p>
      )}
    </div>
  </div>
) : (
  <div className="mb-12 pt-4">
    {/* progress tracker hiện tại giữ nguyên */}
  </div>
)}
```

**4f. Thêm voucher + POS section vào grid "Thông tin vận hành"** (chỉ render nếu có data):
```tsx
{detailDto?.voucherCode && (
  <div className="space-y-2">
    <Label className="..."><Tag size={12} /> Voucher áp dụng</Label>
    <div className="h-14 bg-slate-50 border border-slate-100 rounded-2xl flex items-center px-5 font-bold text-slate-900 shadow-sm font-mono">
      {detailDto.voucherCode}
    </div>
  </div>
)}
{detailDto?.posShiftRef && (
  <div className="space-y-2">
    <Label className="..."><Store size={12} /> Ca POS</Label>
    <div className="h-14 bg-slate-50 border border-slate-100 rounded-2xl flex items-center px-5 font-bold text-slate-900 shadow-sm font-mono text-sm">
      {detailDto.posShiftRef}
    </div>
  </div>
)}
```

---

### Slice S5 — WholesalePage: tích hợp filter + dọn layout

File: `WholesalePage.tsx`

**5a. Cập nhật destructure từ hook:**
```ts
const {
  orders,          // đã là filteredOrders
  ...existing,
  statusFilter,
  setStatusFilter,
  paymentStatusFilter,
  setPaymentStatusFilter,
  sort,
  setSort,
  sortWhitelist,
} = useRetailSalesHistoryListQuery()
```

**5b. Xoá block sort `<select>` inline** (dòng 76–91 hiện tại — cả `<div className="flex ...">` bọc nó).

**5c. Cập nhật `<OrderToolbar>` call:**
```tsx
<OrderToolbar
  variant="retailHistory"
  searchStr={search}
  onSearch={setSearch}
  statusFilter="all"              // → statusFilter
  onStatusChange={() => {}}       // → xoá (thay bằng onStatusFilterChange)
  selectedIds={[]}
  onAction={() => {}}
  dateFrom={dateFrom}
  dateTo={dateTo}
  onDateFromChange={setDateFrom}
  onDateToChange={setDateTo}
  statusFilter={statusFilter}
  onStatusFilterChange={setStatusFilter}
  paymentStatusFilter={paymentStatusFilter}
  onPaymentStatusFilterChange={setPaymentStatusFilter}
  sort={sort}
  onSortChange={(v) => setSort(v as RetailHistoryListSort)}
  sortWhitelist={sortWhitelist}
  getSortLabel={getRetailHistoryListSortLabel}
/>
```

> Bỏ props cũ `statusFilter="all"` và `onStatusChange={() => {}}` ra khỏi call — thay bằng props mới bên trên.

**5d. Cập nhật `<OrderTable>` call:**
```tsx
<OrderTable
  data={orders}
  selectedIds={[]}
  onSelect={() => {}}
  onSelectAll={() => {}}
  onView={handleView}
  showCheckbox={false}
  hideTypeBadge       // thêm
  // bỏ hideStatusColumn → mặc định false, cột status hiện lại
/>
```

**5e. Cập nhật `<OrderDetailDialog>` call:**
```tsx
<OrderDetailDialog
  order={selectedOrder}
  isOpen={isDetailOpen}
  onClose={() => setIsDetailOpen(false)}
  readOnly
  detailLines={detailLines}
  detailDto={detailQuery.data ?? undefined}   // thêm
/>
```

---

## 3. Thứ tự implement

```
S1 (hook) → S2 (toolbar) → S3 (table) → S4 (dialog) → S5 (page)
```

S1 trước vì S5 destructure từ hook. S2–S4 độc lập với nhau, có thể song song. S5 sau cùng để wire tất cả.

---

## 4. Tiêu chí hoàn thành

- `npx tsc --noEmit` pass (0 errors)
- `ORDER_TABLE_COL.payment` đã có sẵn trong `data-table-layout.ts` (`w-[112px]`) — **không cần sửa**
- `SalesOrderDetailDto` import chỉ dùng `import type` (không circular)
- Không sửa `salesOrdersApi.ts`, `data-table-layout.ts`
- Không sửa `ReturnsPage`, `ApprovalHistoryPage`, `PendingApprovalsPage`
