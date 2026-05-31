# BRIDGE — PRD — cash-funds

- Path: **`GET/POST/PATCH /api/v1/cash-funds`**
- Mode: **wire-fe** (GET); **admin-only** (POST/PATCH)
- Date: **2026-05-02**
- Đã đọc `FE_API_CONNECTION_GUIDE.md`: **Y**

| Hạng mục | API doc | Backend | Frontend | Khớp (Y/N) | Hành động |
| :--- | :--- | :--- | :--- | :---: | :--- |
| GET danh sách | `API_PRD_cash_funds.md` §1 | `CashFundsController.list` + `CashFundService` | `cashFundsApi.ts` — `getCashFundsList`, `CASH_FUNDS_LIST_QUERY_KEY`; `TransactionsPage` + `TransactionFormDialog` (dropdown quỹ) | **Y** | — |
| POST/PATCH quỹ | §2–§3 | `CashFundsController` + Admin check | Chưa có UI quản trị quỹ trong `mini-erp` | **N** | Có thể thêm màn Admin sau |

Kết luận:
- Đủ để Staff/Admin có `can_view_finance` chọn quỹ khi tạo phiếu thu chi.
- CRUD quỹ bằng UI: backlog (Postman / Admin console tạm thời).
