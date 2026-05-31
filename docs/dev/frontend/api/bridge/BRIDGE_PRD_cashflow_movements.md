# BRIDGE — PRD — cashflow-movements

- Path: **`GET /api/v1/cashflow/movements`**
- Mode: **wire-fe**
- Date: **2026-05-02**
- Đã đọc `FE_API_CONNECTION_GUIDE.md`: **Y**

| Hạng mục | API doc | Backend | Frontend | Khớp (Y/N) | Hành động |
| :--- | :--- | :--- | :--- | :---: | :--- |
| GET + summary | `API_PRD_cashflow_movements_get_list.md` | `CashflowMovementsController` + `CashflowMovementService` (mặc định ngày hôm nay nếu không gửi `dateFrom`/`dateTo`) | Chưa có `api/*.ts` hay trang trong `mini-erp` | **N** | Thêm khi làm tab/màn “Dòng tiền thống nhất” (Admin) |
| RBAC Admin | §1 | `StockDispatchAccessPolicy.isAdmin` + `can_view_finance` | Ẩn entry menu theo role khi có UI | **—** | — |

Kết luận:
- Endpoint BE đã sẵn sàng theo PRD; FE chờ màn hình báo cáo.
