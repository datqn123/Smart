# BRIDGE — Task057 — `PATCH /api/v1/sales-orders/{id}`

| Trường | Giá trị |
| :----- | :------ |
| **Task** | Task057 |
| **Path** | `PATCH /api/v1/sales-orders/{id}` |
| **Mode** | wire-fe |
| **Date** | 28/04/2026 |
| **Đã đọc `FE_API_CONNECTION_GUIDE.md` (Y/N)** | Y |

## Bảng đối chiếu

| Hạng mục | API doc (mục) | Backend (file) | Frontend (`api/*.ts` + UI) | Khớp (Y/N) | Hành động |
| :-------- | :-------------- | :------------- | :--------------------------- | :--------: | :-------- |
| Path + method + body camelCase | §2, §4, §5 | `SalesOrdersController.patch` + `SalesOrderService.patch` | `salesOrdersApi.ts`: `patchSalesOrder`, `buildSalesOrderPatchBody`, type `SalesOrderPatchBody` / `SalesOrderDetailDto` | **Y** | — |
| **BR-4** — đơn `Cancelled` → **409** | §3, §7 | `CONFLICT` + message tiếng Việt | `WholesalePage.handleSave`: `ApiRequestError` `status === 409` → `toast.error` (message từ BE); `OrderFormDialog`: banner + vô hiệu hóa submit khi `status === Cancelled` | **Y** | ReturnsPage chưa dùng `OrderFormDialog` — nếu sau này sửa meta đơn trả, tái sử dụng cùng API. |
| Meta form (status, payment, ship, notes, discount) | §4 | `JsonNode` các field trên | `OrderFormDialog`: `shippingAddress`, `notes`, `discountAmount` đã `register`; status whitelist **Pending / Processing / Partial / Shipped / Delivered** (không gửi `Cancelled` qua PATCH); map UI cũ **Completed** → **Delivered** trong `buildSalesOrderPatchBody` | **Y** | `shippingAddress` khi mở từ list chưa có GET detail — mặc định rỗng; bổ sung GET by id (Task055) nếu cần hiển thị địa chỉ đã lưu. |
| Invalidate list sau PATCH | — | — | `WholesalePage`: `queryClient.invalidateQueries({ queryKey: SALES_ORDER_LIST_QUERY_KEY })` | **Y** | — |
| **404** / **400** | §7 | BE như verify trước | Lỗi chung: `toast.error` với `ApiRequestError.body.message`; chưa map `details` → từng field form | **Partial** | Có thể `setError` theo `details` khi Owner yêu cầu. |

## Kết luận (≤5 dòng)

1. **`wire-fe` hoàn tất:** `patchSalesOrder` + `buildSalesOrderPatchBody` trong `features/orders/api/salesOrdersApi.ts`.  
2. **UI:** `OrderFormDialog` + `WholesalePage` (`/orders/wholesale`) — lưu chỉnh sửa đơn gọi PATCH; **409** và đơn **Cancelled** đã xử lý UX + toast.  
3. **Tạo đơn mới** vẫn placeholder (chưa POST Task056).  
4. **Doc Zod §8** (ít nhất một field): FE luôn gửi đủ meta từ form khi sửa — không gửi body rỗng.  
5. Build `npm run build` trong `frontend/mini-erp` — **OK**.
