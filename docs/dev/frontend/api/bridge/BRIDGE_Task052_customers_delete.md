# BRIDGE — Task052 — `DELETE /api/v1/customers/{id}`

> **Task:** Task052 | **Path:** `DELETE /api/v1/customers/{id}` | **Mode:** verify | **Date:** 02/05/2026

**Đã đọc** [`frontend/AGENTS/docs/FE_API_CONNECTION_GUIDE.md`](../../../AGENTS/docs/FE_API_CONNECTION_GUIDE.md): Y

| Hạng mục | API doc + SRS | Backend | Frontend | Khớp | Ghi chú |
| :-- | :-- | :-- | :-- | :--: | :-- |
| `DELETE` 200 `{ id, deleted }` | [`API_Task052`](../API_Task052_customers_delete.md) | `CustomerService.delete` → `softDeleteCustomer` | `deleteCustomer` + `ConfirmDialog` / [`CustomersPage`](../../../mini-erp/src/features/product-management/pages/CustomersPage.tsx) | Y | |
| RBAC Admin | SRS_PRD | `StockDispatchAccessPolicy.isAdmin` | `role === "Admin"` — nút xóa | Y | |
| 409 `HAS_OPEN_SALES_ORDERS` | SRS_PRD | `existsOpenSalesOrderForCustomer` | `toastCustomerDeleteError` | Y | |
| Bulk UI ẩn | SRS_PRD OQ-2 | `bulkDelete` Owner-only (BE giữ) | `canBulkDelete={false}` | Y | |

**Kết luận:** BE/FE đã triển khai theo SRS Approved; chạy `Mode=verify` sau mỗi lần đổi contract.
