# BRIDGE — Task044 — `GET /api/v1/suppliers/{id}`

> **Task:** Task044 | **Path:** `GET /api/v1/suppliers/{id}` | **Mode:** wire-fe | **Date:** 27/04/2026

**Đã đọc** [`frontend/AGENTS/docs/FE_API_CONNECTION_GUIDE.md`](../../AGENTS/docs/FE_API_CONNECTION_GUIDE.md): Y

| Hạng mục | API doc + SRS (Task044) | Backend | Frontend | Khớp | Hành động / ghi chú |
| :-- | :-- | :-- | :-- | :--: | :-- |
| `GET` detail, `receiptCount`, `lastReceiptAt` | [`API_Task044_suppliers_get_by_id.md`](../API_Task044_suppliers_get_by_id.md) §2, §4; OQ-4(b) | [`SuppliersController#getById`](../../../../backend/smart-erp/src/main/java/com/example/smart_erp/catalog/controller/SuppliersController.java) + `SupplierDetailData` | [`getSupplierById`](../../../mini-erp/src/features/product-management/api/suppliersApi.ts) | Y | `mapSupplierDetailDtoToSupplier` dùng chung Task043/044. |
| Mở chi tiết | — | — | [`SuppliersPage`](../../../mini-erp/src/features/product-management/pages/SuppliersPage.tsx): `useQuery` `enabled: isDetailOpen && id`; `displaySupplier` = DTO ưu tiên hơn bản từ list | Y | Lỗi: `errToast` + cảnh báo nhẹ trong dialog. |
| UI | — | — | [`SupplierDetailDialog`](../../../mini-erp/src/features/product-management/components/SupplierDetailDialog.tsx): số phiếu nhập; **phiếu nhập gần nhất** (`formatDateTime(lastReceiptAt)`); `isDetailLoading` / `isDetailError` | Y | List Task042 **không** có `lastReceiptAt` — chỉ đầy sau GET detail. |

**Kết luận:** Chi tiết NCC tải từ `GET /api/v1/suppliers/{id}` khi mở dialog; hiển thị `receiptCount` và `lastReceiptAt` theo DTO.  
