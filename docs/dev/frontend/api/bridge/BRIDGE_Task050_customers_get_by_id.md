# BRIDGE — Task050 — `GET /api/v1/customers/{id}`

> **Task:** Task050 | **Path:** `GET /api/v1/customers/{id}` | **Mode:** wire-fe | **Date:** 27/04/2026

**Đã đọc** [`frontend/AGENTS/docs/FE_API_CONNECTION_GUIDE.md`](../../AGENTS/docs/FE_API_CONNECTION_GUIDE.md): Y

| Hạng mục | API doc | Backend | Frontend | Khớp | Hành động / ghi chú |
| :-- | :-- | :-- | :-- | :--: | :-- |
| `GET` detail + aggregates | [`API_Task050_customers_get_by_id.md`](../API_Task050_customers_get_by_id.md) §2–4 | [`CustomersController#getById`](../../../../backend/smart-erp/src/main/java/com/example/smart_erp/catalog/controller/CustomersController.java) + `CustomerData` | [`getCustomerById`](../../../mini-erp/src/features/product-management/api/customersApi.ts) | Y | `mapCustomerDetailDtoToCustomer` — `totalSpent`, `orderCount` từ BE. |
| Mở chi tiết | — | — | [`CustomersPage`](../../../mini-erp/src/features/product-management/pages/CustomersPage.tsx): `useQuery` `enabled: isDetailOpen && id`; `displayCustomer` ưu tiên DTO; `useEffect` merge vào `customers` (read-model) | Y | Lỗi: `errToast` khi mở dialog. |
| UI | — | — | [`CustomerDetailDialog`](../../../mini-erp/src/features/product-management/components/CustomerDetailDialog.tsx): `isDetailLoading` / `isDetailError` trên khối điểm / chi tiêu | Y | Danh sách mock vẫn có thể không khớp id BE — 404 khi test thật. |

**Kết luận:** Chi tiết khách tải từ `GET /api/v1/customers/{id}` khi mở dialog; hiển thị và đồng bộ `totalSpent`, `orderCount` (và các field khác từ DTO) theo server.
