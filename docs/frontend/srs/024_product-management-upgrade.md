# SRS-019: Nâng cấp 4 giao diện Quản lý Sản phẩm

**Ngày:** 2026-06-06
**Phạm vi:** `CategoriesPage`, `ProductsPage`, `SuppliersPage`, `CustomersPage`
**Liên quan:** SQL schema `docs/sql/001_smart_inventory_full_schema.md`

---

## 1. Bối cảnh & Mục tiêu

Bốn giao diện quản lý danh mục sản phẩm hiện tại đã có cấu trúc cơ bản (CRUD, phân trang infinite scroll, search, status filter). Tuy nhiên còn nhiều dữ liệu DB chưa được hiển thị, UX chưa nhất quán với các trang inventory đã nâng cấp (SRS-018), và một số tính năng bị bỏ sót hoặc tạm vô hiệu hóa.

**Mục tiêu nâng cấp:**
1. Hiển thị đầy đủ các trường dữ liệu có giá trị từ DB mà UI đang bỏ qua
2. Nhất quán pattern UX: pill filter tabs thay `<select>`, quick toggle status trực tiếp trên row
3. Kích hoạt các tính năng đang bị stub/tạm tắt (bulk delete khách hàng)
4. Tăng giá trị thông tin: KPI card, badge điểm tích lũy, liên kết công nợ

---

## 2. Hiện trạng & Gap phân tích

### 2.1 CategoriesPage

**Hiện tại:**
- Hiển thị danh mục dạng tree (format: `tree`, flatten để render bảng)
- Columns mặc định: `categoryCode`, `categoryName`, `productCount`, `description`, `status`
- Search + status filter (`all`/`Active`/`Inactive`) qua `<select>`
- Form có field `sortOrder` (số thứ tự) nhưng không có cơ chế sắp xếp lại trực quan
- Xóa đơn, xóa bulk (qua `deleteCategory`)

**Gap:**
- Không có indent trực quan để phân biệt danh mục cha–con trong bảng
- Status filter dùng `<select>` (không nhất quán với inventory)
- Không có quick toggle status trực tiếp trên row
- `sortOrder` chỉ sửa được qua form modal, không có UX nhanh
- Bulk status toggle (kích hoạt/vô hiệu hóa nhiều danh mục) chưa có

### 2.2 ProductsPage

**Hiện tại:**
- Infinite scroll, filters: search + statusFilter + categoryFilter + sort
- Sort dùng native `<select>` với `PRODUCT_LIST_SORT_WHITELIST`
- Columns mặc định: `skuCode`, `productName`, `categoryName`, `stock`, `price`, `status`
- Image thumbnail: `imageUrl` có trong type nhưng chưa rõ hiển thị trong table
- Category filter dùng gì (ProductToolbar chưa read) — cần confirm
- `mockCategories` vẫn được dùng làm fallback khi `categoryOptions` trống
- Bulk delete hoạt động; bulk edit chỉ có `toast.info` (chưa implement)
- `barcode` không hiển thị trong default columns

**Gap:**
- Sort `<select>` không nhất quán với inventory pattern
- `barcode` ẩn khỏi table mặc dù quan trọng cho scanning workflow
- `mockCategories` fallback không nên dùng trong production — gây hiển thị data giả
- Không có pill tab cho status filter (hiện trong `ProductToolbar` — chưa biết)
- Giá hiển thị (`price`) chỉ từ base unit — không rõ đang show `salePrice` hay `costPrice`
- Bulk edit (`action: "edit"`) chỉ `toast.info` — chưa implement thực tế

### 2.3 SuppliersPage

**Hiện tại:**
- Infinite scroll, filters: search + statusFilter + sort
- Sort dùng native `<select>`
- Columns mặc định: `supplierCode`, `supplierName`, `contactName`, `email`, `address`, `status`
- Bulk delete hoạt động (tối đa 50 ids, có duplicate-safe `[...new Set(ids)]`)
- DTO `SupplierDetailDto` có `receiptCount` và `lastReceiptAt` nhưng **không hiển thị trong table**
- Error handling đầy đủ cho `HAS_RECEIPTS`, `HAS_PARTNER_DEBTS`

**Gap:**
- `receiptCount` — trường quan trọng để biết nhà cung cấp nào đang hoạt động — không hiển thị
- `lastReceiptAt` — không hiển thị
- `taxCode` — không hiển thị trong table (chỉ trong form/detail)
- Không có liên kết đến `partnerdebts` từ detail dialog
- Sort `<select>` không nhất quán
- Không có pill tabs cho status filter

### 2.4 CustomersPage

**Hiện tại:**
- Infinite scroll, filters: search + statusFilter + sort
- Sort dùng native `<select>`
- Columns mặc định: `customerCode`, `customerName`, `phone`, `email`, `orderCount`, `status`
- `canBulkDelete={false}` — bulk delete **bị tắt hoàn toàn** ở JSX, dù mutation đã implement
- `loyaltyPoints` chỉ có trong form (edit), **không hiển thị trong table**
- `totalSpent` không hiển thị ở bất kỳ đâu trên UI
- `canEditLoyaltyPoints = !isStaff` — Staff không sửa được điểm tích lũy
- Xóa đơn: chỉ `isAdmin` (Owner không được, khác với Suppliers)

**Gap:**
- `loyaltyPoints` và `totalSpent` là KPI quan trọng — không có trong table
- Bulk delete tắt hoàn toàn dù mutation đã sẵn sàng
- Không có visual tier/badge cho điểm tích lũy
- Không có liên kết đến `partnerdebts` từ detail dialog
- Sort `<select>` không nhất quán

---

## 3. Kế hoạch nâng cấp chi tiết

### 3.1 CategoriesPage — Nâng cấp tree UX & filter nhất quán

#### 3.1.1 Status filter: pill tabs

Thay `<select>` status filter bằng pill tabs nhất quán với inventory:

```tsx
const CATEGORY_STATUS_FILTERS = [
  { value: "all",      label: "Tất cả" },
  { value: "Active",   label: "Đang dùng" },
  { value: "Inactive", label: "Vô hiệu" },
] as const
```

Render: button `rounded-full` active = `bg-slate-900 text-white`, inactive = `bg-white text-slate-600 border-slate-200`.

#### 3.1.2 Tree indent trong bảng

Danh mục con hiện tại flatten phẳng, mất cấu trúc cha–con. Thêm `depth` vào khi flatten:

```ts
function flattenWithDepth(categories: Category[], depth = 0): Array<Category & { depth: number }> {
  return categories.flatMap((c) => [
    { ...c, depth },
    ...(c.children?.length ? flattenWithDepth(c.children, depth + 1) : []),
  ])
}
```

Trong `CategoryTable`, column `categoryName` render với `paddingLeft: depth * 20px` + prefix icon `└─` khi `depth > 0`:

```tsx
<span style={{ paddingLeft: `${row.depth * 20}px` }}>
  {row.depth > 0 && <span className="text-slate-300 mr-1">└─</span>}
  {row.categoryName}
</span>
```

#### 3.1.3 Quick status toggle trên row

Thêm action "Đổi trạng thái" nhanh trong action menu của từng row (bên cạnh Edit/Delete). Click → gọi `patchCategory(id, { status: current === "Active" ? "Inactive" : "Active" })` trực tiếp, không cần mở form.

**Chỉ Owner** được dùng (giống phần xóa).

#### 3.1.4 Bulk status toggle

Khi chọn ≥2 danh mục, thêm nút "Kích hoạt" / "Vô hiệu hóa" vào toolbar (bên cạnh nút xóa). Flow:
- Hiển thị `ConfirmDialog` xác nhận
- Gọi `patchCategory` tuần tự cho từng id được chọn (không có bulk patch endpoint → gọi lần lượt, `Promise.allSettled`)
- Toast tổng kết: "Đã cập nhật X / Y danh mục"

---

### 3.2 ProductsPage — Hiển thị barcode, giá rõ ràng, bỏ mock data

#### 3.2.1 Thêm `barcode` vào default visible columns

Schema DB: `products.barcode VARCHAR(100)`. Cập nhật `useTableColumnOrder` default:

```ts
const visibleColumnKeys = useTableColumnOrder("product_list", [
  "skuCode",
  "productName",
  "barcode",       // THÊM MỚI
  "categoryName",
  "stock",
  "price",
  "status",
])
```

Column `barcode`: font `font-mono text-xs`, truncate nếu dài, badge nhỏ màu slate-100.

#### 3.2.2 Tách rõ giá bán / giá vốn trong table

Hiện tại column `price` có thể chỉ show một giá. Thay bằng 2 sub-columns (hoặc tooltip) từ base unit:

- **Giá bán** (`salePrice`): màu slate-900, in đậm
- **Giá vốn** (`costPrice`): màu slate-500, font nhỏ hơn, chỉ hiển thị với Owner/Admin

Nếu không muốn 2 column riêng, thì trong column `price`:
```tsx
<div className="flex flex-col">
  <span className="font-medium">{formatVnd(row.salePrice)}</span>
  {canViewCost && (
    <span className="text-xs text-slate-400">Vốn: {formatVnd(row.costPrice)}</span>
  )}
</div>
```

`canViewCost = role !== "Staff"` (Staff không xem giá vốn — business rule).

#### 3.2.3 Bỏ `mockCategories` fallback

Dòng hiện tại:
```ts
const formCategoryOptions = useMemo(
  () => (categoryOptions.length > 0 ? categoryOptions : mockCategories.map((c) => ({ id: c.id, name: c.name }))),
  [categoryOptions],
)
```

Thay bằng:
```ts
const formCategoryOptions = useMemo(() => categoryOptions, [categoryOptions])
```

Nếu danh mục chưa load, hiển thị loading state trong form select thay vì dữ liệu giả. Xóa `import { mockCategories } from "../mockData"`.

#### 3.2.4 Status filter: pill tabs

`ProductToolbar` hiện chưa rõ có pill tabs chưa — cần kiểm tra khi implement. Nếu chưa, thêm:

```tsx
const PRODUCT_STATUS_FILTERS = [
  { value: "all",      label: "Tất cả" },
  { value: "Active",   label: "Đang bán" },
  { value: "Inactive", label: "Ngừng bán" },
] as const
```

#### 3.2.5 Bulk status toggle (thay thế bulk edit stub)

Hiện `action: "edit"` chỉ có `toast.info(...)`. Thay bằng bulk status modal:

- Khi chọn ≥1 sản phẩm + click "Cập nhật trạng thái": mở dialog chọn Active/Inactive
- Gọi `patchProduct` tuần tự (`Promise.allSettled`), toast kết quả
- Giữ nguyên bulk delete cho Owner

---

### 3.3 SuppliersPage — Hiển thị KPI nhà cung cấp & công nợ

#### 3.3.1 Thêm `receiptCount` vào table

**Đã xác nhận:** `SupplierListItemDto` (suppliersApi.ts:39) có `receiptCount: number` → list endpoint trả về sẵn. `lastReceiptAt` **không có** trong list DTO (chỉ trong `SupplierDetailDto`) → không thêm vào table (tránh N+1), chỉ hiển thị trong detail dialog.

Cập nhật `useTableColumnOrder` default:

```ts
const visibleColumnKeys = useTableColumnOrder("product_suppliers", [
  "supplierCode",
  "supplierName",
  "contactName",
  "phone",
  "receiptCount",    // THÊM MỚI — có sẵn trong list DTO
  "status",
])
```

`receiptCount`: badge số, nếu = 0 thì màu slate-300, nếu > 0 thì màu blue-600.
`lastReceiptAt`: chỉ hiển thị trong `SupplierDetailDialog` (không cần fetch thêm khi đã open detail).

#### 3.3.2 Status filter: pill tabs

Tương tự các trang khác, thay `<select>` trong `SupplierToolbar`:

```tsx
const SUPPLIER_STATUS_FILTERS = [
  { value: "all",      label: "Tất cả" },
  { value: "Active",   label: "Đang hợp tác" },
  { value: "Inactive", label: "Ngừng hợp tác" },
] as const
```

#### 3.3.3 Liên kết công nợ từ detail dialog — TODO (BE chưa sẵn sàng)

**Đã kiểm tra:** Backend chỉ có `PartnerDebtService.java` + `PartnerDebtJdbcRepository.java`, **không có Controller** → không có HTTP endpoint. Frontend cũng không có file API cho partner-debts.

→ **Skip triển khai lần này.** Ghi TODO trong `SupplierDetailDialog`:

```tsx
{/* TODO: Section "Công nợ" — chờ BE expose GET /api/v1/partner-debts?partnerType=Supplier&partnerId={id} */}
```

Khi BE có endpoint: thêm section hiển thị `total_amount - paid_amount`, list khoản nợ với `due_date`, badge `InDebt` (đỏ) / `Cleared` (xanh).

#### 3.3.4 Quick status toggle trên row

Giống CategoriesPage — thêm action "Đổi trạng thái" vào action menu row.

---

### 3.4 CustomersPage — Kích hoạt bulk delete, hiển thị loyalty & KPI

#### 3.4.1 Hiển thị `loyaltyPoints` và `totalSpent` trong table

Cập nhật `useTableColumnOrder` default:

```ts
const visibleColumnKeys = useTableColumnOrder("product_customers", [
  "customerCode",
  "customerName",
  "phone",
  "loyaltyPoints",   // THÊM MỚI
  "totalSpent",      // THÊM MỚI
  "orderCount",
  "status",
])
```

`loyaltyPoints`:
- Format: `1.200 điểm`
- Visual tier badge:
  - 0 pts: không badge
  - 1–999: badge xám "Đồng"
  - 1000–4999: badge vàng "Bạc"
  - ≥5000: badge cam "Vàng"

`totalSpent`:
- Format: `formatVnd(totalSpent)` — ví dụ `12.500.000 ₫`
- Chỉ hiển thị với Owner/Admin (`!isStaff`)

#### 3.4.2 Kích hoạt bulk delete

Hiện tại `canBulkDelete={false}` hard-coded. `bulkDeleteCustomers` mutation chưa implement trong page (chỉ có `deleteCustomer` đơn lẻ). Cần:

1. Import `postCustomersBulkDelete` (đã có trong `customersApi.ts`)
2. Thêm `bulkDeleteCustomersMutation` tương tự pattern Suppliers
3. Đổi `canBulkDelete={!isStaff}` → cho Owner và Admin được xóa bulk, Staff không
4. `handleToolbarAction("delete")` → set `isDeletingBulk(true)` thay vì toast

**Lưu ý:** `handleDelete` đơn lẻ hiện kiểm tra `isAdmin` — cần thống nhất: nên là `!isStaff` (Owner cũng được xóa) hoặc giữ nguyên `isAdmin`. Xem lại business rule.

#### 3.4.3 Status filter: pill tabs

```tsx
const CUSTOMER_STATUS_FILTERS = [
  { value: "all",      label: "Tất cả" },
  { value: "Active",   label: "Đang hoạt động" },
  { value: "Inactive", label: "Vô hiệu" },
] as const
```

#### 3.4.4 Liên kết công nợ từ detail dialog — TODO (BE chưa sẵn sàng)

Tương tự §3.3.3 — endpoint chưa có. Ghi TODO trong `CustomerDetailDialog`, skip triển khai lần này.

#### 3.4.5 Quick status toggle trên row

Thêm action "Đổi trạng thái" vào action menu row — giống CategoriesPage/SuppliersPage.

---

## 4. Thứ tự ưu tiên triển khai

| # | Task | Trang | Độ ưu tiên | Ghi chú |
|---|------|-------|-----------|---------|
| 1 | Pill filter tabs cho status | Tất cả 4 trang | Cao | Nhất quán UX, dễ làm |
| 2 | `loyaltyPoints` + `totalSpent` trong table | CustomersPage | Cao | Dữ liệu đã có sẵn |
| 3 | Kích hoạt bulk delete khách hàng | CustomersPage | Cao | Mutation đã có, chỉ cần enable |
| 4 | `receiptCount` trong table | SuppliersPage | Cao | Nếu list endpoint có sẵn field |
| 5 | `barcode` trong table | ProductsPage | Trung bình | Thêm column |
| 6 | Tách giá bán / giá vốn | ProductsPage | Trung bình | Cần role check |
| 7 | Tree indent cho danh mục | CategoriesPage | Trung bình | UX improvement |
| 8 | Quick status toggle trên row | Tất cả 4 trang | Trung bình | Pattern lặp lại |
| 9 | Bỏ mockCategories fallback | ProductsPage | Trung bình | Code hygiene |
| 10 | Bulk status toggle | CategoriesPage + ProductsPage | Thấp | Cần UX design |
| 11 | Liên kết công nợ (partnerdebts) | Suppliers + Customers | Thấp | Phụ thuộc BE endpoint |

---

## 5. Quyết định đã xác nhận

| # | Câu hỏi | Kết luận |
|---|---------|---------|
| Q1 | `receiptCount` có trong Supplier list endpoint không? | **Có** — `SupplierListItemDto` line 39 đã có `receiptCount: number`. `lastReceiptAt` không có trong list → chỉ show trong detail dialog |
| Q2 | Quyền xóa khách hàng: `isAdmin` hay `!isStaff`? | **`isOwner or isAdmin`** — cả Owner và Admin đều được xóa |
| Q3 | Bulk delete khách hàng cần ConfirmDialog không? | **Có** — dùng `ConfirmDialog` giống Suppliers (Option A) |
| Q4 | BE có endpoint partner-debts chưa? | **Chưa** — chỉ có Service + Repository, không có Controller → skip, TODO comment |

## 6. Component/File cần thay đổi

| File | Thay đổi |
|------|---------|
| `pages/CategoriesPage.tsx` | Pill tabs, bulk status toggle, call flattenWithDepth |
| `components/CategoryTable.tsx` | Tree indent theo depth, action menu quick toggle |
| `pages/ProductsPage.tsx` | Bỏ mockCategories, add barcode column, bulk status |
| `components/ProductToolbar.tsx` | Pill tabs cho status filter (nếu chưa có) |
| `components/ProductTable.tsx` | Thêm barcode column, tách giá bán/vốn |
| `pages/SuppliersPage.tsx` | Pill tabs cho status |
| `components/SupplierToolbar.tsx` | Pill tabs |
| `components/SupplierTable.tsx` | Thêm receiptCount, lastReceiptAt columns |
| `components/SupplierDetailDialog.tsx` | Section công nợ (nếu BE có endpoint) |
| `pages/CustomersPage.tsx` | Enable bulk delete, canBulkDelete logic |
| `components/CustomerToolbar.tsx` | Pill tabs |
| `components/CustomerTable.tsx` | Thêm loyaltyPoints (với tier badge), totalSpent |
| `components/CustomerDetailDialog.tsx` | Section công nợ (nếu BE có endpoint) |
