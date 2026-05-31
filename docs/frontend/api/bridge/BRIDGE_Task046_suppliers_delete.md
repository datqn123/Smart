# BRIDGE — Task046 — `DELETE /api/v1/suppliers/{id}`

> **Task:** Task046 | **Path:** `DELETE /api/v1/suppliers/{id}` | **Mode:** wire-fe | **Date:** 27/04/2026

**Đã đọc** [`frontend/AGENTS/docs/FE_API_CONNECTION_GUIDE.md`](../../AGENTS/docs/FE_API_CONNECTION_GUIDE.md): Y

| Hạng mục | API doc + SRS (Task046) | Backend | Frontend | Khớp | Hành động / ghi chú |
| :-- | :-- | :-- | :-- | :--: | :-- |
| `DELETE` 200 | [`API_Task046_suppliers_delete.md`](../API_Task046_suppliers_delete.md) §2, §4 | [`SuppliersController#delete`](../../../../backend/smart-erp/src/main/java/com/example/smart_erp/catalog/controller/SuppliersController.java) | [`deleteSupplier`](../../../mini-erp/src/features/product-management/api/suppliersApi.ts); `useMutation` + `ConfirmDialog`; `invalidate` list + `detail` | Y | Đóng chi tiết / form nếu đang mở đúng `id` (ref như `ProductsPage`). |
| Owner UI | SRS OQ-1 | `assertOwnerOnly` | `useAuthStore` `user.role === "Owner"` — ẩn nút xóa bảng + bulk; toast nếu gọi lệ | Y | Staff không thấy nút; gọi trực tiếp API → **403** + toast. |
| 409 + `details.reason` | Doc §5–6 | `HAS_RECEIPTS` / `HAS_PARTNER_DEBTS` | `toastSupplierDeleteError` — copy thân thiện + message server | Y | — |

**Kết luận:** Xóa một NCC qua `DELETE` đã nối; bulk xóa toolbar chỉ Owner (Task047 sẽ gọi API bulk).  
