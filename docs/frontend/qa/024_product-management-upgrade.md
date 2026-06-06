# TEST_PLAN_024: Product Management Upgrade

**Tech Spec:** `docs/frontend/tech_lead/023_product-management-upgrade.md`
**SRS:** `docs/frontend/srs/019_product-management-upgrade.md`
**Ngày:** 2026-06-06
**Readiness:** QA_READY_FOR_CODING

---

## P0 — Blocking (phải pass trước khi merge)

| # | Test | Input | Expected |
|---|------|-------|---------|
| P0-1 | `npx tsc --noEmit` không lỗi mới | Sau khi sửa tất cả 8 slices | 0 lỗi TS mới so với trước |
| P0-2 | Pill status SupplierToolbar — chọn "Đang hợp tác" | Click pill | `statusFilter = "Active"`, pill active style `bg-slate-900 text-white`, API call với `status=Active` |
| P0-3 | Pill status CustomerToolbar — chọn "Vô hiệu" | Click pill | `statusFilter = "Inactive"`, pill active, API call `status=Inactive` |
| P0-4 | Pill reset về "Tất cả" | Click "Tất cả" pill | `statusFilter = "all"`, không append `status=` vào query |
| P0-5 | SupplierTable: receiptCount hiển thị đúng | Supplier `receiptCount=3` | Badge xanh "3" trong column "Phiếu nhập" |
| P0-6 | SupplierTable: receiptCount=0 | Supplier `receiptCount=0` | Badge xám "0" |
| P0-7 | CustomerTable: loyaltyPoints tier Bạc | `loyaltyPoints=1500` | Số "1.500" + badge vàng "Bạc" |
| P0-8 | CustomerTable: loyaltyPoints tier Vàng | `loyaltyPoints=5000` | Số "5.000" + badge cam "Vàng" |
| P0-9 | CustomerTable: loyaltyPoints=0 | `loyaltyPoints=0` | Chỉ "0", không có badge |
| P0-10 | CustomersPage: Owner bulk delete 2 customers | Chọn 2 items, click Xóa bulk | ConfirmDialog hiện; xác nhận → `postCustomersBulkDelete([id1,id2])` → toast "Đã xóa 2 khách hàng" |
| P0-11 | CustomersPage: Staff không thấy Xóa bulk | Role=Staff | Nút Xóa không xuất hiện trong toolbar selection bar |
| P0-12 | CustomersPage: Staff click xóa đơn | Role=Staff, click trash icon row | Toast "Chỉ Owner hoặc Admin mới được xóa" |
| P0-13 | ProductsPage: không render mockCategories | CategoryOptions = [] (chưa load) | Form dropdown rỗng hoặc loading, không hiển thị "Danh mục 1, Danh mục 2..." |

---

## P1 — Quan trọng (nên pass)

| # | Test | Input | Expected |
|---|------|-------|---------|
| P1-1 | SupplierTable: column receiptCount có trong header | Render table | Header "Phiếu nhập" xuất hiện |
| P1-2 | CustomerTable: header "Điểm tích lũy" và "Tổng mua" | Render table | Cả 2 header xuất hiện |
| P1-3 | CustomerTable: totalSpent format VND | `totalSpent=12500000` | "12.500.000 ₫" hoặc tương đương |
| P1-4 | CustomerTable: totalSpent=null | `totalSpent=undefined` | Hiển thị "-" |
| P1-5 | CustomersPage: Admin cũng được bulk delete | Role=Admin | Nút Xóa bulk hiển thị, flow như P0-10 |
| P1-6 | CustomersPage: ConfirmDialog cancel | Mở confirm, click Cancel | Dialog đóng, không gọi API, selectedIds giữ nguyên |
| P1-7 | SupplierToolbar: pill tabs không break layout trên mobile | Viewport 375px | Tabs wrap đúng, không tràn ngang |
| P1-8 | CustomerToolbar: pill tabs không break layout | Viewport 375px | Tương tự |
| P1-9 | CategoriesPage: pill tabs cho status | Click "Đang dùng" | Filter về Active hoạt động |
| P1-10 | SupplierTable: DEFAULT_COLUMNS bỏ address → không tràn | Render mặc định | Không có column "Địa chỉ" trong default; layout không tràn ngang |

---

## P2 — Nice to have

| # | Test | Expected |
|---|------|---------|
| P2-1 | loyaltyPoints tier Đồng (1-999) | Badge xám "Đồng" |
| P2-2 | CustomersPage: bulk delete 50+ items | Nếu selectedIds > 50: API gọi với 50 items đầu; hoặc API xử lý và trả error — xử lý graceful |
| P2-3 | SupplierTable: column settings toggle receiptCount | Ẩn receiptCount qua column settings | Column biến mất |

---

## Failure Mode Matrix

| Mode | Scenario | Guard |
|------|---------|-------|
| Role bypass | Staff gọi bulk delete API trực tiếp | BE enforce RBAC — FE chỉ ẩn nút |
| Empty selectedIds bulk delete | Gọi confirm khi 0 selected | `ids.length === 0` → `setIsDeletingBulk(false)` early return |
| `postCustomersBulkDelete` 409 | Customer có đơn hàng chưa hoàn tất | `toastCustomerDeleteError` → toast "có đơn hàng chưa hoàn tất" |
| `postCustomersBulkDelete` network error | Timeout/500 | `errToast(e)` |
| loyaltyPoints negative | Không xảy ra (DB constraint) | Tier function trả null cho pts <= 0 |
| mockCategories import vẫn còn | Unused import warning TS | `npx tsc --noEmit` không lỗi; có thể warning lint |

---

## Regression Scope

- `SuppliersPage.tsx` bulk delete flow không bị ảnh hưởng (chỉ Customers thay đổi)
- `CustomerDetailDialog` không thay đổi — vẫn hiển thị đúng
- `CustomerForm` `canEditLoyaltyPoints` không thay đổi logic
- Column settings (`useTableColumnOrder`) cho `"product_customers"` — key mới `loyaltyPoints`/`totalSpent` sẽ hiển thị lần đầu vì không có trong localStorage → fallback về defaultColumnKeys = hiển thị mặc định ✓

**QA_READY_FOR_CODING**
