# TECH_SPEC_023: Product Management Upgrade

**SRS:** `docs/frontend/srs/019_product-management-upgrade.md`
**Ngày:** 2026-06-06
**Readiness:** READY_FOR_CODING

---

## 1. Scope

Frontend-only. Không thay đổi BE, DB, API contracts.

Affected files:
- `frontend/mini-erp/src/lib/data-table-layout.ts`
- `frontend/mini-erp/src/features/product-management/components/SupplierToolbar.tsx`
- `frontend/mini-erp/src/features/product-management/components/CustomerToolbar.tsx`
- `frontend/mini-erp/src/features/product-management/components/SupplierTable.tsx`
- `frontend/mini-erp/src/features/product-management/components/CustomerTable.tsx`
- `frontend/mini-erp/src/features/product-management/pages/CustomersPage.tsx`
- `frontend/mini-erp/src/features/product-management/pages/ProductsPage.tsx`
- `frontend/mini-erp/src/features/product-management/pages/CategoriesPage.tsx` (check inline filter)

---

## 2. Horizontal Analysis

| Pattern reused | Source |
|---|---|
| Pill filter tabs `rounded-full` | `InboundPage.tsx`, `DispatchPage.tsx` (SRS-018) |
| `bulkDeleteMutation` + `isDeletingBulk` + `ConfirmDialog` | `SuppliersPage.tsx` |
| `columnRenderers satisfies Record<...>` | `SupplierTable.tsx` (existing pattern) |
| `canEditLoyaltyPoints = !isStaff` → Staff không xem giá vốn | `CustomersPage.tsx` |

**CategoryTable đã có tree indent** (level * 24px, expand/collapse) — SRS §3.1.2 ĐÃ IMPLEMENT, bỏ qua.

---

## 3. Implementation Slices

### Slice 1 — `data-table-layout.ts`: Thêm COL keys mới

**File:** `frontend/mini-erp/src/lib/data-table-layout.ts`

Thêm `receiptCount` vào `SUPPLIER_TABLE_COL`:
```ts
// Thêm sau `address`:
receiptCount: "w-[108px]",
```

Thêm `loyaltyPoints` và `totalSpent` vào `CUSTOMER_TABLE_COL`:
```ts
// Thêm sau `orders`:
loyaltyPoints: "w-[140px]",
totalSpent: "w-[148px]",
```

---

### Slice 2 — `SupplierToolbar.tsx`: Pill tabs

**Thay `<select>` bằng pill tabs. Pattern:** copy từ InboundPage RECEIPT_STATUS_FILTERS.

```tsx
// Xóa import không cần (không còn dùng <select>)
// Thêm cn từ @/lib/utils

const SUPPLIER_STATUS_FILTERS = [
  { value: "all",      label: "Tất cả" },
  { value: "Active",   label: "Đang hợp tác" },
  { value: "Inactive", label: "Ngừng hợp tác" },
] as const

// Trong JSX, thay <select>...</select> bằng:
<div className="flex items-center gap-1.5 flex-wrap">
  {SUPPLIER_STATUS_FILTERS.map((f) => (
    <button
      key={f.value}
      type="button"
      onClick={() => onStatusChange(f.value)}
      className={cn(
        "h-9 px-3 rounded-full text-sm font-medium transition-colors border shrink-0",
        statusFilter === f.value
          ? "bg-slate-900 text-white border-slate-900"
          : "bg-white text-slate-600 border-slate-200 hover:border-slate-400 hover:text-slate-900",
      )}
    >
      {f.label}
    </button>
  ))}
</div>
```

Layout: Row 1 = search + pill tabs + action buttons (tất cả inline), hoặc giữ cấu trúc flex hiện tại, chỉ thay `<select>`.

---

### Slice 3 — `CustomerToolbar.tsx`: Pill tabs

**Tương tự Slice 2.** Const name: `CUSTOMER_STATUS_FILTERS`.

```tsx
const CUSTOMER_STATUS_FILTERS = [
  { value: "all",      label: "Tất cả" },
  { value: "Active",   label: "Hoạt động" },
  { value: "Inactive", label: "Vô hiệu" },
] as const
```

---

### Slice 4 — `SupplierTable.tsx`: Thêm `receiptCount` column

`Supplier` type đã có `receiptCount?: number`. `SupplierListItemDto` đã trả về field này.

Thêm vào `columnRenderers`:
```tsx
receiptCount: {
  head: <TableHead className={cn(SUPPLIER_TABLE_COL.receiptCount, TABLE_HEAD_CLASS, "px-4 text-center")}>Phiếu nhập</TableHead>,
  cell: (item: Supplier) => (
    <TableCell className={cn(SUPPLIER_TABLE_COL.receiptCount, "px-4 text-center")}>
      <span className={cn(
        "inline-flex items-center justify-center min-w-[28px] h-6 px-2 rounded-full text-xs font-semibold",
        (item.receiptCount ?? 0) > 0
          ? "bg-blue-50 text-blue-700"
          : "bg-slate-100 text-slate-400",
      )}>
        {item.receiptCount ?? 0}
      </span>
    </TableCell>
  ),
},
```

Thêm `"receiptCount"` vào `DEFAULT_COLUMNS` và kiểu `columnRenderers`:
```ts
const DEFAULT_COLUMNS = ["supplierCode", "supplierName", "contactName", "receiptCount", "status"]
```

Xóa `"email"` và `"address"` khỏi DEFAULT (giảm bớt để thêm receiptCount không tràn). Chúng vẫn available qua column settings.

---

### Slice 5 — `CustomerTable.tsx`: Thêm `loyaltyPoints` + `totalSpent`

**Customer type:** `loyaltyPoints: number`, `totalSpent?: number`.

Thêm `loyaltyPoints` và `totalSpent` vào `defaultColumnKeys` và render:

```tsx
const defaultColumnKeys = [
  "customerCode", "customerName", "phone",
  "loyaltyPoints",  // THÊM MỚI
  "totalSpent",     // THÊM MỚI
  "orderCount", "status",
] as const
```

Tier badge helper (inline, không cần separate file):
```tsx
function loyaltyTier(pts: number): { label: string; cls: string } | null {
  if (pts <= 0) return null
  if (pts < 1000) return { label: "Đồng", cls: "bg-slate-100 text-slate-600" }
  if (pts < 5000) return { label: "Bạc", cls: "bg-yellow-50 text-yellow-700" }
  return { label: "Vàng", cls: "bg-orange-50 text-orange-700" }
}
```

Cell render cho `loyaltyPoints`:
```tsx
if (columnKey === "loyaltyPoints") {
  const tier = loyaltyTier(item.loyaltyPoints)
  return (
    <TableCell key={columnKey} className={cn(CUSTOMER_TABLE_COL.loyaltyPoints, TABLE_CELL_NUMBER_CLASS, "px-4")}>
      <div className="flex items-center gap-1.5">
        <span>{item.loyaltyPoints.toLocaleString("vi-VN")}</span>
        {tier && (
          <span className={cn("text-[10px] font-semibold px-1.5 py-0.5 rounded-full", tier.cls)}>
            {tier.label}
          </span>
        )}
      </div>
    </TableCell>
  )
}
```

Cell render cho `totalSpent` (prop `canViewSpent` truyền từ page):

Để không làm phức tạp props, `totalSpent` hiển thị `formatVnd` — **ẩn nếu không có dữ liệu** (totalSpent == null → "-"). Không cần role check tại table level (data đã được truyền vào, page quyết định có truyền hay không).

```tsx
// Thêm import formatVnd hoặc dùng toLocaleString:
if (columnKey === "totalSpent") {
  const spent = item.totalSpent
  return (
    <TableCell key={columnKey} className={cn(CUSTOMER_TABLE_COL.totalSpent, TABLE_CELL_NUMBER_CLASS, "px-4")}>
      {spent != null ? spent.toLocaleString("vi-VN", { style: "currency", currency: "VND", maximumFractionDigits: 0 }) : "-"}
    </TableCell>
  )
}
```

Fix `colSpan` hardcoded = 8 → động: `defaultColumnKeys.length + 2`.

Thêm head cells cho `loyaltyPoints` và `totalSpent` (theo pattern if-check hiện tại):
```tsx
{orderedBusinessColumns.includes("loyaltyPoints") && (
  <TableHead className={cn(CUSTOMER_TABLE_COL.loyaltyPoints, TABLE_HEAD_CLASS, "px-4")}>Điểm tích lũy</TableHead>
)}
{orderedBusinessColumns.includes("totalSpent") && (
  <TableHead className={cn(CUSTOMER_TABLE_COL.totalSpent, TABLE_HEAD_CLASS, "px-4")}>Tổng mua</TableHead>
)}
```

---

### Slice 6 — `CustomersPage.tsx`: Bulk delete + fix quyền xóa

**A. Thêm `isDeletingBulk` state** (hiện tại chưa có):
```tsx
const [isDeletingBulk, setIsDeletingBulk] = useState(false)
```

**B. Thêm `bulkDeleteCustomersMutation`:**
```tsx
import { ..., postCustomersBulkDelete } from "../api/customersApi"
// ...
const bulkDeleteCustomersMutation = useMutation({
  mutationFn: (ids: number[]) => postCustomersBulkDelete(ids),
  onSuccess: (data) => {
    void queryClient.invalidateQueries({ queryKey: [...CUSTOMER_LIST_QUERY_KEY] })
    for (const id of data.deletedIds) {
      void queryClient.invalidateQueries({ queryKey: ["product-management", "customers", "detail", id] })
    }
    setSelectedIds([])
    setIsDeletingBulk(false)
    setSelectedCustomer((p) => {
      if (p && data.deletedIds.includes(p.id)) { setIsDetailOpen(false); return null }
      return p
    })
    setEditingCustomer((p) => {
      if (p && data.deletedIds.includes(p.id)) { setIsFormOpen(false); return undefined }
      return p
    })
    toast.success(data.deletedCount > 0 ? `Đã xóa ${data.deletedCount} khách hàng` : "Đã xóa khách hàng")
  },
  onError: (e) => {
    setIsDeletingBulk(false)
    if (e instanceof ApiRequestError) {
      if (e.status === 409) { toastCustomerDeleteError(e); return }
      if (e.status === 403) { toast.error(e.body?.message ?? e.message); return }
      if (e.status === 400) { errToast(e); return }
    }
    errToast(e)
  },
})
```

**C. Fix `handleToolbarAction("delete")`:**
```tsx
case "delete":
  if (isStaff) {
    toast.error("Chỉ Owner hoặc Admin mới được xóa hàng loạt khách hàng.")
    return
  }
  setIsDeletingBulk(true)
  break
```

**D. Thêm `confirmBulkDelete`:**
```tsx
const confirmBulkDelete = () => {
  if (isStaff) { setIsDeletingBulk(false); return }
  const ids = [...new Set(selectedIds)]
  if (ids.length === 0) { setIsDeletingBulk(false); return }
  void bulkDeleteCustomersMutation.mutateAsync(ids)
}
```

**E. Fix role check cho xóa đơn lẻ:**
```tsx
// Thay isAdmin → !isStaff
const handleDelete = (item: Customer) => {
  if (isStaff) {
    toast.error("Chỉ Owner hoặc Admin mới được xóa khách hàng.")
    return
  }
  setDeleteTarget(item)
}
```

**F. Cập nhật JSX:**
```tsx
// canBulkDelete: false → !isStaff
<CustomerToolbar
  ...
  canBulkDelete={!isStaff}
/>

// Thêm ConfirmDialog bulk:
<ConfirmDialog
  open={isDeletingBulk}
  onOpenChange={setIsDeletingBulk}
  onConfirm={confirmBulkDelete}
  title="Xác nhận xóa nhiều"
  description={`Bạn có chắc chắn muốn xóa ${selectedIds.length} khách hàng đã chọn? (Xóa mềm)`}
/>

// canDelete: isAdmin → !isStaff
<CustomerTable
  ...
  canDelete={!isStaff}
/>
```

---

### Slice 7 — `ProductsPage.tsx`: Bỏ `mockCategories` fallback

```tsx
// Xóa import:
// import { mockCategories } from "../mockData"

// Thay:
const formCategoryOptions = useMemo(() => categoryOptions, [categoryOptions])
```

---

### Slice 8 — `CategoriesPage.tsx`: Pill tabs cho status filter

Cần đọc file để xác định filter hiện tại là inline hay component riêng. Nếu inline trong page: thêm pill tabs trực tiếp. Nếu có `CategoriesToolbar` riêng: sửa ở đó.

Pattern pill tabs giống Slice 2, const: `CATEGORY_STATUS_FILTERS`.

---

## 4. Guardrails

- `SUPPLIER_TABLE_COL.receiptCount` phải được khai báo trong `data-table-layout.ts` trước khi dùng trong `SupplierTable.tsx` (Slice 1 trước Slice 4).
- `CUSTOMER_TABLE_COL.loyaltyPoints` và `.totalSpent` tương tự (Slice 1 trước Slice 5).
- `postCustomersBulkDelete` giới hạn 50 ids theo API — không cần thêm client-side guard vì `selectedIds` trong practice ít hơn.
- `toastCustomerDeleteError` đã có trong `CustomersPage.tsx` — dùng lại.

---

## 5. Test Plan

| Test | Expected |
|------|---------|
| SupplierToolbar: click "Đang hợp tác" | `statusFilter === "Active"`, pill active sáng |
| SupplierToolbar: click "Tất cả" | filter về `all` |
| CustomerToolbar: tương tự | tương tự |
| SupplierTable: supplier có receiptCount=5 | Badge xanh "5" |
| SupplierTable: supplier có receiptCount=0 | Badge xám "0" |
| CustomerTable: customer có loyaltyPoints=1500 | Badge vàng "Bạc" hiển thị |
| CustomerTable: customer có loyaltyPoints=0 | Không có badge |
| CustomerTable: totalSpent hiển thị | Format VND đúng |
| CustomersPage: Staff không thấy nút Xóa bulk | `canBulkDelete={false}` cho Staff |
| CustomersPage: Owner/Admin bulk delete 3 items | Confirm dialog → xóa → toast "Đã xóa 3 khách hàng" |
| CustomersPage: Staff click Xóa đơn | Toast lỗi phân quyền |
| ProductsPage: categoryOptions trống khi load | Không hiển thị mockCategories |
| TS compile | `npx tsc --noEmit` không có lỗi mới |

---

## 6. Open Questions

Không có blocker. CategoriesPage filter structure cần kiểm tra khi implement Slice 8.

**Readiness: READY_FOR_CODING**
