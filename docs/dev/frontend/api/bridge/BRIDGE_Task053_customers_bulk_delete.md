# BRIDGE — Task053 — `POST /api/v1/customers/bulk-delete`

> **Task:** Task053 | **Path:** `POST /api/v1/customers/bulk-delete` | **Mode:** wire-fe | **Date:** 27/04/2026

**Đã đọc** [`frontend/AGENTS/docs/FE_API_CONNECTION_GUIDE.md`](../../AGENTS/docs/FE_API_CONNECTION_GUIDE.md): Y

| Hạng mục | API doc + SRS | Backend | Frontend | Khớp | Hành động / ghi chú |
| :-- | :-- | :-- | :-- | :--: | :-- |
| Body `{ ids }` | [`API_Task053_customers_bulk_delete.md`](../API_Task053_customers_bulk_delete.md) §3 | `CustomersBulkDeleteRequest` — validate `@Size(max=200)`; service **`dedupePreserveOrder`** + **1–50** unique | [`postCustomersBulkDelete`](../../../mini-erp/src/features/product-management/api/customersApi.ts); `confirmBulkDelete` dùng `[...new Set(selectedIds)]`; chặn **> 50** unique trước khi gọi (toast) | Y | Trùng trong mảng: BE gộp (SRS OQ-5(b)); gửi trùng vẫn an toàn. |
| 200 `deletedIds` / `deletedCount` | Doc §4; BE record | `CustomerBulkDeleteData` | `bulkDeleteCustomersMutation` `onSuccess` + toast | Y | `invalidateQueries` [`CUSTOMER_LIST_QUERY_KEY`](../../../mini-erp/src/features/product-management/api/customersApi.ts) + từng `detail` id đã xóa. |
| **All-or-nothing** 409 | Doc §4–5; logic §5 | Một `id` lỗi → **409** toàn bộ không xóa | `toastCustomerDeleteError` (`NOT_FOUND`, `HAS_SALES_ORDERS`, `HAS_PARTNER_DEBTS` + `failedId`) | Y | Đóng dialog bulk lỗi: `onError` → `setIsDeletingBulk(false)`. |
| Owner | Task052/053 | `assertOwnerOnly` trong `bulkDelete` | Toolbar `canBulkDelete={isOwner}`; `confirmBulkDelete` kiểm `isOwner` | Y | **403** nếu gọi khi không đủ quyền. |
| 400 | — | Rỗng sau dedupe / > 50 unique | `errToast` trong `onError` (400) | Y | FE thêm guard **> 50** để giảm round-trip. |

**Kết luận:** Xóa hàng loạt gọi `POST /api/v1/customers/bulk-delete` từ [`CustomersPage`](../../../mini-erp/src/features/product-management/pages/CustomersPage.tsx); transaction all-or-nothing khớp BE — lỗi 409 hiển thị qua `details.reason` / `failedId`.
