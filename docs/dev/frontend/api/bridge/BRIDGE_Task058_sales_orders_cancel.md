# BRIDGE — Task058 — `POST /api/v1/sales-orders/{id}/cancel`

| Trường | Giá trị |
| :----- | :------ |
| **Task** | Task058 |
| **Path** | `POST /api/v1/sales-orders/{id}/cancel` |
| **Mode** | wire-fe |
| **Date** | 28/04/2026 |
| **Đã đọc `FE_API_CONNECTION_GUIDE.md` (Y/N)** | Y |

## Bảng đối chiếu

| Hạng mục | API doc (mục) | Backend (file) | Frontend (`api/*.ts` + UI) | Khớp (Y/N) | Hành động |
| :-------- | :-------------- | :------------- | :--------------------------- | :--------: | :-------- |
| Path + POST + body optional | §2, §3 | `SalesOrdersController.cancel` + `SalesOrderService.cancel` | `salesOrdersApi.ts`: `postCancelSalesOrder`, `SalesOrderCancelBodyInput` — JSON **`reason`** (max 500); hỗ trợ alias **`cancelReason`** → map sang `reason` | **Y** | Wire prompt ghi `cancelReason` — BE/API dùng `reason` (đã ghi trong JSDoc type). |
| **OQ-5** — idempotent **200** khi đã `Cancelled` | §5 (sửa doc: 200) | Trả `SalesOrderCancelData` 200 | `WholesalePage` / `ReturnsPage`: `handleCancelOrderConfirm` — nếu đơn đã `Cancelled` trước khi gọi → `toast.info` sau thành công | **Y** | — |
| **OQ-6** — **409** khi đã xuất / dispatched | §5 bước 3 | `CONFLICT` + message tiếng Việt | `catch` → `toast.error` với `e.body.message` hoặc fallback mô tả OQ-6; **rethrow** để `SalesOrderCancelDialog` không đóng khi lỗi | **Y** | — |
| Invalidate list | — | — | `queryClient.invalidateQueries({ queryKey: SALES_ORDER_LIST_QUERY_KEY })` | **Y** | — |
| UI — bảng / toolbar / chi tiết | UC9 | — | `OrderTable` cột thao tác (`onDelete`); `OrderToolbar` **Xoá** khi chọn đúng 1 dòng; `OrderDetailDialog` nút **Hủy đơn** (`onCancelOrder`); `SalesOrderCancelDialog` nhập lý do tuỳ chọn | **Y** | `WholesalePage` + `ReturnsPage`. Màn approvals chỉ xem detail — không truyền `onCancelOrder` → nút disabled. |

## Kết luận (≤5 dòng)

1. **`postCancelSalesOrder`** trong `features/orders/api/salesOrdersApi.ts` — `apiJson` + Bearer.  
2. **`SalesOrderCancelDialog`** + tích hợp **Bán buôn** / **Trả hàng** + **Chi tiết đơn** (hủy / sửa).  
3. **409** (OQ-6) và **200 idempotent** (OQ-5) đã có toast/message rõ.  
4. **`reason`** là field hợp đồng JSON; `cancelReason` chỉ là alias phía TS khi build body.  
5. `npm run build` trong `frontend/mini-erp` — **OK**.
