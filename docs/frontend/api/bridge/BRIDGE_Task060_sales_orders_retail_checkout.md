# BRIDGE — Task060 — `POST /api/v1/sales-orders/retail/checkout`

| Trường | Giá trị |
| :----- | :------ |
| **Task** | Task060 |
| **Path** | `POST /api/v1/sales-orders/retail/checkout` |
| **Mode** | verify |
| **Date** | 29/04/2026 |
| **Đã đọc `FE_API_CONNECTION_GUIDE.md` (Y/N)** | Y |

## Bảng đối chiếu

| Hạng mục | API doc (mục) | Backend (file) | Frontend (`api/*.ts` + UI) | Khớp (Y/N) | Hành động |
| :-------- | :-------------- | :------------- | :--------------------------- | :--------: | :-------- |
| Path + method + 201 envelope | `API_Task060_sales_orders_retail_checkout.md` §3, §5 | `SalesOrdersController.java` `@PostMapping("/retail/checkout")` → `SalesOrderService.retailCheckout` | `features/orders/api/salesOrdersApi.ts` — `postRetailCheckout` gọi `apiJson("/api/v1/sales-orders/retail/checkout")` | **Y** | — |
| Body schema (không có `locationId`) | §4, §8 | `RetailCheckoutRequest` + validate trong `SalesOrderService.validateLines` | `buildRetailCheckoutBody` tạo body camelCase; **không** gửi `locationId` | **Y** | — |
| Trừ tồn theo `StoreProfiles` + FEFO + `FOR UPDATE` | §4 (ghi chú Task090), §6, §7 | `RetailStockService` + `RetailStockJdbcRepository` (lock inventory FEFO `expiry_date NULLS LAST`, tạo `StockDispatches`, `InventoryLogs` OUTBOUND, update `OrderDetails.dispatched_qty`) + Flyway `V20__task090_storeprofiles_default_retail_location.sql` (`default_retail_location_id`) | FE không cần field chọn kho; UI chỉ hiển thị kết quả sau checkout | **Y** (doc↔BE); **N/A** (FE không tham gia logic) | (Doc) nên nâng `API_Task060` trạng thái khỏi Draft khi DoD xong. |
| 409 thiếu tồn | §7 | `BusinessException(ApiErrorCode.CONFLICT, ...)` từ `RetailStockService` khi thiếu tồn sau khi lock | `apiJson` ném `ApiRequestError` status 409; UI cần toast/message theo `message` | **Y** | Nếu UX muốn highlight dòng thiếu tồn: chuẩn hóa `details` key trong 409 (hiện là `productId:<id>`). |
| `dispatched_qty` phản ánh sau checkout | (Task090 SRS) | `RetailStockJdbcRepository.markOrderLinesDispatchedAll` | FE hiển thị `dispatchedQty` qua detail (Task055/060 response) | **Y** | — |

## Kết luận (≤5 dòng)

1. `API_Task060` đã được **đồng bộ** theo Task090: checkout POS trừ tồn theo kho mặc định `StoreProfiles` (V20) và cấp phát FEFO, trả 409 khi thiếu tồn.  
2. Backend đã triển khai đủ chuỗi: `SalesOrderService.retailCheckout` → `RetailStockService.deductStockForRetailCheckout` (dispatch/log/dispatched_qty).  
3. Frontend đã có `postRetailCheckout` + `buildRetailCheckoutBody` và **không** gửi `locationId`.  
4. Cần thêm phiên `API_BRIDGE` cho **Task058 cancel** (Retail hoàn kho) để hoàn tất bộ prompt Task090.  
5. Output: `frontend/docs/api/bridge/BRIDGE_Task060_sales_orders_retail_checkout.md` (verify).

# BRIDGE — Task060 — `POST /api/v1/sales-orders/retail/checkout`

| Trường | Giá trị |
| :----- | :------ |
| **Task** | Task060 |
| **Path** | `POST /api/v1/sales-orders/retail/checkout` |
| **Mode** | wire-fe |
| **Date** | 28/04/2026 |
| **Đã đọc `FE_API_CONNECTION_GUIDE.md` (Y/N)** | Y |

## Bảng đối chiếu

| Hạng mục | API doc (mục) | Backend (file) | Frontend (`api/*.ts` + UI) | Khớp (Y/N) | Hành động |
| :-------- | :-------------- | :------------- | :--------------------------- | :--------: | :-------- |
| Path + `201` + envelope | §3, §5 | `SalesOrdersController.retailCheckout` | `salesOrdersApi.ts` — `postRetailCheckout` | **Y** | — |
| Body: `lines`, `walkIn`/`customerId`, `discountAmount`, `voucherCode`, `paymentStatus`, `notes`, `shiftReference` | §4, §8 | `RetailCheckoutRequest` | `buildRetailCheckoutBody` + `POSCartPanel` (`useMutation`) | **Y** | `shiftReference`: `sessionStorage.posShiftReference` hoặc field snapshot (mở rộng UI sau). |
| Walk-in | §2 | Như verify trước | `customerId == null` → `walkIn: true` | **Y** | — |
| Sau 201 | (prompt) | — | `clearCart` + `invalidateQueries` `SALES_ORDER_LIST_QUERY_KEY` + `POS_PRODUCTS_SEARCH_QUERY_KEY` + toast `orderCode` | **Y** | Chưa điều hướng trang chi tiết (chưa có route POS → detail). |
| 400 + `details` | §7 | `BusinessException` + `details` | `checkoutErrorToast` → `toast.error` + `description` từ `details` | **Y** | — |
| UI `/orders/retail` | §9 | — | `POSCartPanel`: Tiền mặt → `Paid`; Thẻ/Chuyển khoản → `Unpaid`; voucher “Áp dụng” lưu mã (BE xác nhận lúc checkout); tổng hiển thị “ước tính” (voucher không trừ client) | **Partial** | Đồng bộ % hiển thị voucher với BE khi có API tra policy. |

## Kết luận (≤5 dòng)

1. **`postRetailCheckout`** + **`buildRetailCheckoutBody`** trong `frontend/mini-erp/src/features/orders/api/salesOrdersApi.ts`.  
2. **`POSCartPanel`** gọi mutation, xử lý lỗi `ApiRequestError` (400 + `details`), sau thành công xóa giỏ + invalidate list POS + list đơn.  
3. **`Grep`** `retail/checkout` trong `mini-erp/src`: `salesOrdersApi.ts` (path POST).  
4. **`getFinalTotal`** (store) chỉ trừ `discount` tay; voucher chỉ gửi body — khớp “server tính lại” (§9).  
5. Build **mini-erp** `npm run build` **thành công**.
