# BRIDGE — Task054 — `GET /api/v1/sales-orders`

| Trường | Giá trị |
| :----- | :------ |
| **Task** | Task054 |
| **Path** | `GET /api/v1/sales-orders` |
| **Mode** | wire-fe |
| **Date** | 28/04/2026 |
| **Đã đọc `FE_API_CONNECTION_GUIDE.md` (Y/N)** | Y |

## Bảng đối chiếu

| Hạng mục | API doc (mục) | Backend (file) | Frontend (`api/*.ts` + UI) | Khớp (Y/N) | Hành động |
| :-------- | :-------------- | :------------- | :--------------------------- | :--------: | :-------- |
| Path + query + 200 | `API_Task054_sales_orders_get_list.md` §3, §6, §7 | `SalesOrdersController.list` + `SalesOrderService.list` + `SalesOrderJdbcRepository` | `features/orders/api/salesOrdersApi.ts` — `getSalesOrderList`, `SALES_ORDER_LIST_SORT_WHITELIST`, `mapSalesOrderListItemDtoToOrder`. `hooks/useSalesOrdersListQuery.ts` — TanStack Query, debounce search, **luôn** truyền `orderChannel` theo màn. | **Y** | Sau Task055+ có thể `invalidateQueries` prefix `SALES_ORDER_LIST_QUERY_KEY`. |
| Màn Wholesale / Returns | §11 | `orderChannel` query | `WholesalePage.tsx` (`Wholesale`), `ReturnsPage.tsx` (`Return`) + `OrderToolbar` (status theo BE, `paymentStatus`), phân trang + sort. | **Y** | Chi tiết đơn/dialog vẫn mock/local — ngoài scope Task054. |
| OQ-8a / 403 | §6, SRS | `SalesOrderAccessPolicy` | Toast 403 + message BE; màn này không gọi list không kênh. | **Y** | Màn “tất cả kênh” (Owner/Admin) chưa có — khi thêm thì `orderChannel` optional trong `getSalesOrderList`. |
| RBAC | §5 | `can_manage_orders` | Cùng guard menu BE (JWT). | **Y** | — |

## Kết luận (≤5 dòng)

1. **wire-fe hoàn tất:** `salesOrdersApi.ts` + `useSalesOrdersListQuery` + `WholesalePage` / `ReturnsPage` gọi `GET /api/v1/sales-orders` với `orderChannel` đúng màn.  
2. **`OrderToolbar`:** thêm lọc `paymentStatus`; status dropdown khớp giá trị BE (`Delivered` thay cho `Completed` trong filter).  
3. **`FEATURES_UI_INDEX.md`** bảng `orders/` đã ghi API + hook + trang list.  
4. **Grep** `/api/v1/sales-orders` trong `mini-erp/src` — chỉ `salesOrdersApi.ts`.  
5. Build FE: `npm run build` trong `frontend/mini-erp`.
