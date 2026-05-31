# BRIDGE — Task045 — `PATCH /api/v1/suppliers/{id}`

> **Task:** Task045 | **Path:** `PATCH /api/v1/suppliers/{id}` | **Mode:** wire-fe | **Date:** 27/04/2026

**Đã đọc** [`frontend/AGENTS/docs/FE_API_CONNECTION_GUIDE.md`](../../AGENTS/docs/FE_API_CONNECTION_GUIDE.md): Y

| Hạng mục | API doc + SRS (Task045) | Backend | Frontend | Khớp | Hành động / ghi chú |
| :-- | :-- | :-- | :-- | :--: | :-- |
| `PATCH` partial, 200 = detail | [`API_Task045_suppliers_patch.md`](../API_Task045_suppliers_patch.md) §2–4 | [`SuppliersController#patch`](../../../../backend/smart-erp/src/main/java/com/example/smart_erp/catalog/controller/SuppliersController.java) + `patch(JsonNode)` | [`patchSupplier`](../../../mini-erp/src/features/product-management/api/suppliersApi.ts); `buildSupplierPatchBody` từ snapshot; `useMutation` + `invalidate` list + `detail` tại `id` | Y | Tối thiểu một trường hợp lệ; không gửi key nếu không đổi. |
| Snapshot sửa | — | `GET` detail cùng cache | `useQuery` cùng key `detail` khi mở form sửa; ưu tiên DTO hơn dòng list; `key` form theo `updatedAt` khi DTO tải xong | Y | Nếu GET detail chưa xong: chặn lưu + thông báo. |
| 400 / 409 + `details` | Doc §6 | 409 mã trùng | `SupplierForm` gắn `setError` từ `details` + toast fallback | Y | 409 có thể chỉ có `message` — vẫn toast. |
| Sửa nhiều từ toolbar | — | — | Chỉ sửa từ từng dòng (form) — chưa bulk. | n/a | Ngoài scope Task045. |

**Kết luận:** Sửa NCC qua `PATCH` đã nối; `SupplierForm` khi sửa gọi `patchSupplier` và làm mới list + cache chi tiết.  
