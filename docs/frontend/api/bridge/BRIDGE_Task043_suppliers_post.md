# BRIDGE — Task043 — `POST /api/v1/suppliers`

> **Task:** Task043 | **Path:** `POST /api/v1/suppliers` | **Mode:** wire-fe | **Date:** 27/04/2026

**Đã đọc** [`frontend/AGENTS/docs/FE_API_CONNECTION_GUIDE.md`](../../AGENTS/docs/FE_API_CONNECTION_GUIDE.md): Y

| Hạng mục | API doc + SRS (Task043) | Backend | Frontend | Khớp | Hành động / ghi chú |
| :-- | :-- | :-- | :-- | :--: | :-- |
| `POST` body, 201 | [`API_Task043_suppliers_post.md`](../API_Task043_suppliers_post.md) §2, §4–5 | [`SuppliersController#create`](../../../../backend/smart-erp/src/main/java/com/example/smart_erp/catalog/controller/SuppliersController.java) | [`postSupplier`](../../../mini-erp/src/features/product-management/api/suppliersApi.ts) + [`buildSupplierCreateBody`](../../../mini-erp/src/features/product-management/api/suppliersApi.ts); `useMutation` trên [`SuppliersPage`](../../../mini-erp/src/features/product-management/pages/SuppliersPage.tsx) — `invalidateQueries` `["product-management", "suppliers", "list"]` | Y | Nút **Lưu** (tạo mới) gọi server. |
| 400 / 409 + `details` | Doc §4, §6 | Validation + 409 mã trùng | [`SupplierForm`](../../../mini-erp/src/features/product-management/components/SupplierForm.tsx) — `applyApiDetailsToForm` + `setError` theo trường; toast nếu không map được | Y | 409 thường `supplierCode` trong `details`. |
| Sửa (PATCH) | — | Task045 | Chưa: `throw SupplierFormSubmitAborted` + toast; dialog không đóng. | N (sau) | `wire-fe` Task045. |

**Kết luận:** Tạo NCC qua `POST` đã móc form + list refetch. Sửa: chờ Task045.  
