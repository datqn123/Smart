# BRIDGE — Task056 — `POST /api/v1/sales-orders`

| Trường | Giá trị |
| :----- | :------ |
| **Task** | Task056 |
| **Path** | `POST /api/v1/sales-orders` |
| **Mode** | wire-fe |
| **Date** | 28/04/2026 |
| **Đã đọc `FE_API_CONNECTION_GUIDE.md` (Y/N)** | Y |

## Bảng đối chiếu

| Hạng mục | API doc (mục) | Backend (file) | Frontend (`api/*.ts` + UI) | Khớp (Y/N) | Hành động |
| :-------- | :-------------- | :------------- | :--------------------------- | :--------: | :-------- |
| Path + method + 201 | §2, §5 | `SalesOrdersController.create` | `salesOrdersApi.ts` — `postSalesOrder`, `SalesOrderCreateBody` / `SalesOrderCreateLineBody`; trả `SalesOrderDetailDto`. | **Y** | — |
| Body camelCase | §4 | `SalesOrderCreateRequest` | Dialog build đúng tên field; `mapStatusForSalesOrderCreate` (Completed→Delivered, Cancelled→bỏ status). | **Y** | — |
| Wholesale UI | §4.1 | `orderChannel: Wholesale` | `OrderFormDialog` — tạo mới: `customerId`, `lines` (useFieldArray), meta; `WholesalePage` — `handleCreateWholesale` → `postSalesOrder` + `invalidateQueries` `SALES_ORDER_LIST_QUERY_KEY` + toast + đóng dialog. | **Y** | Chọn SP/đơn vị từ catalog (combobox) — cải tiến UX sau. |
| Return UI | §4.2 | `orderChannel: Return`, `refSalesOrderId` | `ReturnFormDialog` — `customerId`, `refSalesOrderId` tuỳ chọn, `lines`, status/payment/notes; `ReturnsPage` — `handleCreateReturn` + invalidate list. | **Y** | Sửa phiếu (edit) PATCH — ngoài scope Task056. |
| Lỗi 400 / 409 | §7 | Envelope `message` / `details` | `ApiRequestError` → `toast.error(body.message)` trong page handlers. | **Y** | Có thể map `details` → field form sau. |
| BR-1 Retail | prompt | Retail → checkout Task060 | Form chỉ gửi Wholesale/Return. | **Y** | — |

## Kết luận (≤5 dòng)

1. **wire-fe hoàn tất:** `postSalesOrder` + form tạo (customerId + ≥1 dòng hàng) trên **Bán buôn** và **Trả hàng**.  
2. **Invalidate** danh sách Task054 sau tạo thành công.  
3. **Grep** `"/api/v1/sales-orders"` (POST root) — `salesOrdersApi.ts` (không kèm path con).  
4. Doc/API: ref không tồn tại BE trả **409**; giá lệch catalog → **400** — FE hiển thị message từ BE.  
5. **Output** `frontend/docs/api/bridge/BRIDGE_Task056_sales_orders_post.md` — cập nhật sau `wire-fe`.
