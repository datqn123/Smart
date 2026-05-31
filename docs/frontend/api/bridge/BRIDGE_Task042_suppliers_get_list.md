# BRIDGE — Task042 — `GET /api/v1/suppliers`

> **Task:** Task042 | **Path:** `GET /api/v1/suppliers` | **Mode:** wire-fe | **Date:** 27/04/2026

**Đã đọc** [`frontend/AGENTS/docs/FE_API_CONNECTION_GUIDE.md`](../../AGENTS/docs/FE_API_CONNECTION_GUIDE.md): Y

| Hạng mục | API doc + SRS (Task042) | Backend | Frontend | Khớp | Hành động / ghi chú |
| :-- | :-- | :-- | :-- | :--: | :-- |
| Method + path, 200 | [`API_Task042_suppliers_get_list.md`](../API_Task042_suppliers_get_list.md) §2, §5–6 | [`SuppliersController#list`](../../../../backend/smart-erp/src/main/java/com/example/smart_erp/catalog/controller/SuppliersController.java) | [`getSupplierList`](../../../mini-erp/src/features/product-management/api/suppliersApi.ts) + `useQuery` + `SUPPLIER_LIST_SORT_WHITELIST` — debounce 400 ms; phân trang; [`SuppliersPage`](../../../mini-erp/src/features/product-management/pages/SuppliersPage.tsx) | Y (list) | — |
| Query, sort | §5, §5.1; SRS §8.2 | `SupplierService#list` + whitelist | `listParams` → `getSupplierList` | Y | Lọc `search` / `status` gửi server. |
| RBAC + Bearer | §4; SRS §6 | `can_manage_products` + JWT | `apiJson` `auth: true` | Y* | *Doc “Owner, Staff, Admin” ↔ authority. |

| CRUD từ form / xóa (ngoài list) | — | Task043+ | Toast hướng dẫn nối Task043/045/046/047; chưa gọi POST/PATCH/DELETE | N (chờ task) | **Scope Task042 = chỉ danh sách (GET).** |

**Kết luận:** Danh sách NCC tải từ `GET /api/v1/suppliers` với phân trang, sắp xếp whitelist, tìm kiếm/ trạng thái. Tạo/sửa/xóa trên server: các Task tiếp theo.  
