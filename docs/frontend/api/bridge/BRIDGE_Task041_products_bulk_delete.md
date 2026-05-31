# BRIDGE — Task041 — `POST /api/v1/products/bulk-delete`

> **Task:** Task041 | **Path:** `POST /api/v1/products/bulk-delete` | **Mode:** wire-fe | **Date:** 27/04/2026

**Đã đọc** [`frontend/AGENTS/docs/FE_API_CONNECTION_GUIDE.md`](../../AGENTS/docs/FE_API_CONNECTION_GUIDE.md): Y

| Hạng mục | API doc ([`API_Task041_products_bulk_delete.md`](../API_Task041_products_bulk_delete.md)) | Backend | Frontend | Khớp | Hành động / ghi chú |
| :-- | :-- | :-- | :-- | :--: | :-- |
| Body | `{ "ids": number[] }` 1..100 | [`ProductsBulkDeleteRequest`](../../../../backend/smart-erp/src/main/java/com/example/smart_erp/catalog/dto/ProductsBulkDeleteRequest.java) | [`postProductsBulkDelete`](../../../mini-erp/src/features/product-management/api/productsApi.ts) → `apiJson` | **Y** | — |
| All-or-nothing **409** | Có | [`ProductService.bulkDelete`](../../../../backend/smart-erp/src/main/java/com/example/smart_erp/catalog/service/ProductService.java) | `toastProductMutationEnvelope` — ưu tiên hiển thị `failedId` + `reason` nếu có | **Y** | — |
| **403** Owner | SRS §6 | `assertOwnerOnly` | `user.role === "Owner"` ( [`useAuthStore`](../../../mini-erp/src/features/auth/store/useAuthStore) ): ẩn **Xoá** toolbar + cột xóa dòng; chặn handler + `toast.error`; xử lý 403 từ BE | **Y** | — |
| **200** | `deletedIds` / `deletedCount` | `ProductBulkDeleteData` | `ProductsBulkDeleteDto`; toast thành công + `invalidateQueries` list + bỏ chọn | **Y** | — |
| UI | Toolbar + `ConfirmDialog` | — | [`ProductsPage`](../../../mini-erp/src/features/product-management/pages/ProductsPage.tsx) `bulkDeleteMutation` · [`ProductToolbar`](../../../mini-erp/src/features/product-management/components/ProductToolbar.tsx) `canBulkDelete` · [`ProductTable`](../../../mini-erp/src/features/product-management/components/ProductTable.tsx) `canDelete` | **Y** | `ConfirmDialog` vẫn đóng ngay; lỗi → toast (đã bắt) |

**Kết luận:** Đã nối Task041 + giới hạn **Owner** trùng SRS/BE. `npm run build` + `ProductsPage` structural test **OK**.
