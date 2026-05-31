# BRIDGE — Task064 — cash-transactions-get-list

- Task: **Task064**
- Path: **`GET /api/v1/cash-transactions`**
- Mode: **wire-fe**
- Date: **2026-05-02**
- Đã đọc `FE_API_CONNECTION_GUIDE.md`: **Y**

| Hạng mục | API doc (mục) | Backend (file) | Frontend (`api/*.ts` + UI) | Khớp (Y/N) | Hành động |
| :--- | :--- | :--- | :--- | :---: | :--- |
| Endpoint + query | `API_Task064_cash_transactions_get_list.md` §5–§6 | `CashTransactionsController.list` + `CashTransactionService` / JDBC | `cashTransactionsApi.ts` (`fundId` trong params) + `TransactionsPage.tsx` | **Y** | Query: `type`, `status`, `search`, `page`, `limit`; `fundId` có trong API client — **toolbar lọc quỹ** có thể bổ sung sau |
| Auth Bearer | §4 | BE JWT + `can_view_finance` | `apiJson` `auth: true` | **Y** | — |
| TanStack Query | — | — | `useQuery` + `queryKey` gồm filters; toast `ApiRequestError` | **Y** | — |
| Bỏ mock list | — | — | Không còn `mockTransactions`; bảng + phân trang theo `total` | **Y** | `mockData.ts` vẫn giữ mock nợ / khác nếu cần |
| Toolbar filter | §5 | BE sort theo có/không mốc ngày | Lọc `type`/`status`/`search` gửi server; thống kê 3 thẻ = **theo trang hiện tại** (ghi chú dưới thẻ) | **Y** | Cần endpoint tổng hợp nếu muốn toàn bộ CSDL |

Kết luận:
- Đã nối `GET /api/v1/cash-transactions` vào `/cashflow/transactions` theo Task064; response có `fundId`/`fundCode` (PRD).
- Form tạo/sửa dùng Task065–067; `GET /cash-funds` phục vụ chọn quỹ — xem `BRIDGE_PRD_cash_funds.md`.
- Sau Task067 (Completed), nên `invalidateQueries` thêm `finance-ledger` list (Task063).
