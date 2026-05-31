# BRIDGE — Task038 — `DELETE /api/v1/products/{id}`

> **Task:** Task038 | **Path:** `DELETE /api/v1/products/{id}` | **Mode:** wire-fe | **Date:** 27/04/2026

**Đã đọc** [`frontend/AGENTS/docs/FE_API_CONNECTION_GUIDE.md`](../../AGENTS/docs/FE_API_CONNECTION_GUIDE.md): Y

| Hạng mục | API doc (`API_Task038_products_delete.md`) + SRS §6, §8.7 / BR-5 | Backend | Frontend | Khớp | Ghi chú |
| :-- | :-- | :-- | :-- | :--: | :-- |
| `DELETE` + Bearer | §2–3 | [`ProductsController.delete`](../../../../backend/smart-erp/src/main/java/com/example/smart_erp/catalog/controller/ProductsController.java) | [`deleteProduct`](../../../mini-erp/src/features/product-management/api/productsApi.ts) | **Y** | |
| Owner-only (§6) | Owner | [`ProductService.delete`](../../../../backend/smart-erp/src/main/java/com/example/smart_erp/catalog/service/ProductService.java) `assertOwnerOnly` → **403** | [`ProductTable`](../../../mini-erp/src/features/product-management/components/ProductTable.tsx) `canDelete={isOwner}`; toolbar bulk; `handleDelete` toast nếu không Owner | **Y** | JWT `role === "Owner"` (khớp claim BE). |
| **200** `data` | `id`, `deleted` | [`ProductDeleteData`](../../../../backend/smart-erp/src/main/java/com/example/smart_erp/catalog/response/ProductDeleteData.java) | `ProductDeleteDto` + toast thành công | **Y** | |
| **409** + `details` | Phiếu nhập / đơn / tồn | `deleteBlockReason` → `reason`, `failedId` | [`toastProductMutationEnvelope`](../../../mini-erp/src/features/product-management/pages/ProductsPage.tsx) (409 + `failedId`/`reason`) | **Y** | Cùng kiểu bulk Task041. |
| **403** | Non-Owner | FORBIDDEN | `toastProductMutationEnvelope` | **Y** | |
| Invalidate | List + detail | — | `invalidateQueries` list + `["detail", deletedId]` | **Y** | Đóng detail/form nếu đang xem/sửa đúng SP đã xóa (ref tránh stale). |
| Confirm UI | Dialog xác nhận | — | [`ConfirmDialog`](../../../mini-erp/src/components/shared/ConfirmDialog.tsx) + [`confirmDelete`](../../../mini-erp/src/features/product-management/pages/ProductsPage.tsx) `mutateAsync(id)` | **Y** | Dialog đóng ngay sau bấm xác nhận (component chung); `id` bắt trước khi đóng. |

**Kết luận:**

- Đã **`wire-fe` Task038**: `deleteProduct` + `deleteProductMutation`, xác nhận xóa một SP, invalidate cache, toast **403/409** qua envelope chung với Task037/041.
- Owner: ẩn nút xóa dòng + chặn bulk/toolbar (đã có từ trước); non-Owner không gọi DELETE từ UI hàng đầu.
- Hạn chế nhỏ: `ConfirmDialog` gọi `onOpenChange(false)` ngay sau `onConfirm` — nếu DELETE lỗi, hộp thoại đã đóng; user có thể chọn xóa lại từ bảng.
