# BRIDGE — Task055 — `GET /api/v1/sales-orders/{id}`

| Trường | Giá trị |
| :----- | :------ |
| **Task** | Task055 |
| **Path** | `GET /api/v1/sales-orders/{id}` |
| **Mode** | verify |
| **Date** | 28/04/2026 |
| **Đã đọc `FE_API_CONNECTION_GUIDE.md` (Y/N)** | Y (theo quy trình API_BRIDGE) |

## Bảng đối chiếu

| Hạng mục | API doc (mục) | Backend (file) | Frontend (`api/*.ts` + UI) | Khớp (Y/N) | Hành động |
| :-------- | :-------------- | :------------- | :--------------------------- | :--------: | :-------- |
| Path + method + 200 envelope | `API_Task055_sales_orders_get_by_id.md` §2, §5 | `SalesOrdersController.java` `@GetMapping("/{id:[0-9]+}")` → `getById` → `ApiSuccessResponse<SalesOrderDetailData>` | **Chưa có** `getSalesOrderById` / `GET …/{id}` trong `salesOrdersApi.ts`; chỉ có list (Task054) + `patchSalesOrder` (Task057) cùng kiểu `SalesOrderDetailDto`. | **N** (FE chưa gọi GET) | `wire-fe`: thêm `getSalesOrderById(id)` + `OrderDetailDialog` dùng `useQuery` khi mở (thay `mockOrderItems`). |
| Header + `lines` shape | §5 (id, orderCode, customer…, `lines[]` với sku, quantity, unitPrice, lineTotal, dispatchedQty) | `SalesOrderDetailData` + `SalesOrderLineDetailData` — thêm **`unitId`** mỗi dòng; header thêm **`posShiftRef`**, **`voucherId`**, **`voucherCode`**, **`cancelledAt`**, **`cancelledBy`** (không có trong ví dụ §5) | `SalesOrderDetailDto` / `SalesOrderDetailLineDto` trong `salesOrdersApi.ts` đã có `posShiftRef`, voucher, cancelled; **thiếu `unitId`** trên type dòng so với BE. | **Partial** | Bổ sung `unitId` vào `SalesOrderDetailLineDto` khi wire GET/PATCH; **DOC_SYNC**: cập nhật `API_Task055` §5 (SRS §12 `posShiftRef` + field bổ sung). |
| `refSalesOrderId` / Return | §5 ghi chú Return | Cùng field trên `SalesOrderDetailData` | DTO FE có `refSalesOrderId`. | **Y** | Hiển thị link/ref trên UI khi có. |
| 404 | §6, §7 | `SalesOrderService.getById` → `findDetailById` → `BusinessException(NOT_FOUND, "Không tìm thấy đơn hàng")` | Dialog chưa gọi API. | **—** | FE: toast / đóng dialog khi 404. |
| RBAC | §4 | `@PreAuthorize("hasAuthority('can_manage_orders')")` + JWT | Giống list Task054. | **Y** | — |
| `id` path | §8 Zod | `parsePositiveIntId` — không hợp lệ → **400** + `details.id` | Chưa gọi. | **—** | Chỉ gửi id số dương từ list. |

## Kết luận (≤5 dòng)

1. **Backend** triển khai `GET /api/v1/sales-orders/{id}` đúng contract lõi (header + `lines`), 404 rõ ràng; response **rộng hơn** ví dụ `API_Task055` §5 (`posShiftRef`, voucher, hủy, `unitId` dòng).  
2. **API markdown** nên đồng bộ với BE/SRS §12 (`posShiftRef`) và các field thực tế — việc **DOC_SYNC**.  
3. **Frontend** chưa nối GET chi tiết; `OrderDetailDialog` vẫn **`mockOrderItems`**.  
4. Type **`SalesOrderDetailLineDto`** nên thêm **`unitId`** cho khớp `SalesOrderLineDetailData` trước/song song wire.  
5. **Output** `frontend/docs/api/bridge/BRIDGE_Task055_sales_orders_get_by_id.md` — verify hoàn tất.
