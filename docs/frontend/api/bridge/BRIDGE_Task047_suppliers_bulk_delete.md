# BRIDGE — Task047 — `POST /api/v1/suppliers/bulk-delete`

> **Task:** Task047 | **Path:** `POST /api/v1/suppliers/bulk-delete` | **Mode:** wire-fe | **Date:** 27/04/2026

**Đã đọc** [`frontend/AGENTS/docs/FE_API_CONNECTION_GUIDE.md`](../../AGENTS/docs/FE_API_CONNECTION_GUIDE.md): Y

| Hạng mục | API doc + SRS (Task047) | Backend | Frontend | Khớp | Hành động / ghi chú |
| :-- | :-- | :-- | :-- | :--: | :-- |
| Body `{ ids }`, max 50 | [`API_Task047_suppliers_bulk_delete.md`](../API_Task047_suppliers_bulk_delete.md) §4 | `SuppliersBulkDeleteRequest` | [`postSuppliersBulkDelete`](../../../mini-erp/src/features/product-management/api/suppliersApi.ts) — `confirmBulkDelete` dùng `[...new Set(selectedIds)]` (dedupe, không thay BE) | Y | Trùng id trên BE vẫn 400. |
| 200 `deletedIds` / `deletedCount` | Doc §5 | `SupplierBulkDeleteData` | `bulkDeleteSuppliersMutation` `onSuccess` + toast | Y | `invalidate` list + từng `detail` đã xóa. |
| 409 all-or-nothing | Doc §6 | `failedId` + `reason` | Dùng chung `toastSupplierDeleteError` (bulk + lẻ) | Y | Thêm gợi ý `failedId` + `NOT_FOUND`. |
| Owner | Doc §3 | `assertOwnerOnly` | `canBulkDelete={isOwner}`; `confirmBulkDelete` kiểm `isOwner` | Y | — |
| Lỗi / đóng dialog | — | — | `onError` gọi `setIsDeletingBulk(false)` | Y | Có thể mở lại và chọn lại. |

**Kết luận:** Xóa hàng loạt gọi `POST /api/v1/suppliers/bulk-delete` với `ids` đã dedupe; all-or-nothing 409 hiển thị qua `details`.  
