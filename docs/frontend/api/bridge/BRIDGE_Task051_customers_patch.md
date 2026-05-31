# BRIDGE — Task051 — `PATCH /api/v1/customers/{id}`

> **Task:** Task051 | **Path:** `PATCH /api/v1/customers/{id}` | **Mode:** wire-fe | **Date:** 27/04/2026

**Đã đọc** [`frontend/AGENTS/docs/FE_API_CONNECTION_GUIDE.md`](../../AGENTS/docs/FE_API_CONNECTION_GUIDE.md): Y

| Hạng mục | API doc | Backend | Frontend | Khớp | Hành động / ghi chú |
| :-- | :-- | :-- | :-- | :--: | :-- |
| `PATCH` partial, 200 = `CustomerData` | [`API_Task051_customers_patch.md`](../API_Task051_customers_patch.md) §2–4 | [`CustomersController#patch`](../../../../backend/smart-erp/src/main/java/com/example/smart_erp/catalog/controller/CustomersController.java) + `CustomerService#patch` | [`patchCustomer`](../../../mini-erp/src/features/product-management/api/customersApi.ts); `buildCustomerPatchBody` + snapshot từ GET detail / list row | Y | Ít nhất một field đổi; camelCase JSON. |
| `loyaltyPoints` + Staff → 403 | Doc §3 | `body.has("loyaltyPoints") && isStaffRole(jwt)` → 403 | [`CustomerForm`](../../../mini-erp/src/features/product-management/components/CustomerForm.tsx): `canEditLoyaltyPoints={role !== "Staff"}` — ẩn field + không gửi key; [`CustomersPage`](../../../mini-erp/src/features/product-management/pages/CustomersPage.tsx) truyền từ `useAuthStore` | Y | BR-3: tránh Staff gửi `loyaltyPoints`. |
| `useMutation` + invalidate | — | — | `patchCustomerMutation`: invalidate `[...CUSTOMER_LIST_QUERY_KEY]` + `detail` theo `id`; `createCustomerMutation` (Task049) invalidate list | Y | Form sửa: `useQuery` GET detail khi mở (`editingFormId`), snapshot ưu tiên DTO. |
| 400 / 409 + `details` | Doc §6 | 409 trùng `customerCode` | `applyCustomerCreateApiError` mở rộng field gồm `loyaltyPoints`; form `CustomerFormSubmitAborted` khi không đổi / chưa tải detail | Y | Giữ toast khi không map được `details`. |

**Kết luận:** Sửa khách qua `PATCH` đã nối; Staff không thấy / không gửi điểm tích lũy; cache list + chi tiết được làm mới sau lưu.
