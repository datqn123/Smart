# BRIDGE — Task102 — `GET /api/v1/sales-orders/retail/history`

| Trường | Giá trị |
| :----- | :------ |
| **Task** | Task102 |
| **Path** | `GET /api/v1/sales-orders/retail/history` |
| **Mode** | wire-fe |
| **Date** | 02/05/2026 |
| **Đã đọc `FE_API_CONNECTION_GUIDE.md` (Y/N)** | Y |

## Bảng đối chiếu

| Hạng mục | API doc | Backend | Frontend | Khớp (Y/N) | Ghi chú |
| :-------- | :-------- | :------ | :--------- | :--------: | :------ |
| Path + query + 200 | `API_Task102_sales_orders_retail_history_get_list.md` | `SalesOrdersController.retailHistory` → `SalesOrderService.listRetailHistory` → `SalesOrderJdbcRepository.countRetailHistory` / `findRetailHistoryPage` | `salesOrdersApi.ts` — `getRetailSalesHistoryList`; `useRetailSalesHistoryListQuery.ts`; `WholesalePage.tsx` | **Y** | Lọc `Retail` + `Delivered`/`Cancelled`; `dateFrom`/`dateTo` yyyy-MM-dd, múi giờ `Asia/Ho_Chi_Minh` (BE). |
| Chi tiết chỉ đọc | Task055 | `GET /sales-orders/{id}` | `getSalesOrderDetail` + `OrderDetailDialog` `readOnly` + `detailLines` | **Y** | Màn lịch sử không gọi PATCH/cancel. |
| RBAC | §4 SRS | `can_manage_orders` | Cùng JWT như POS / đơn hàng | **Y** | — |

## Kết luận

1. **wire-fe:** Màn `/orders/wholesale` — **Lịch sử hóa đơn bán lẻ** — dùng Task102 list + Task055 detail.  
2. **Menu:** `Sidebar` nhãn *Lịch sử hóa đơn* (đã đồng bộ trước đó).  
3. **Test BE:** `SalesOrdersControllerWebMvcTest.retailHistory_returns200`.  
4. **Invalidate:** sau checkout POS có thể `invalidateQueries` prefix `RETAIL_SALES_HISTORY_LIST_QUERY_KEY` (tùy phiên tích hợp `RetailPage`).
