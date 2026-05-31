# BRIDGE — Task065 — cash-transactions-post

- Task: **Task065**
- Path: **`POST /api/v1/cash-transactions`**
- Mode: **wire-fe**
- Date: **2026-05-02**
- Đã đọc `FE_API_CONNECTION_GUIDE.md`: **Y**

| Hạng mục | API doc (mục) | Backend (file) | Frontend (`api/*.ts` + UI) | Khớp (Y/N) | Hành động |
| :--- | :--- | :--- | :--- | :---: | :--- |
| POST + body | `API_Task065_cash_transactions_post.md` §5–§6 | `CashTransactionsController.create` + `CashTransactionCreateRequest` (`fundId`, `category` ≤ 500) | `cashTransactionsApi.ts` — `postCashTransaction` + `CashTransactionCreateBody` + `TransactionsPage` / `TransactionFormDialog` (chọn quỹ, `getCashFundsList`) | **Y** | — |
| 201 + invalidate Task064 | §6 | BE 201 + envelope | `TransactionsPage` `handleFormSubmit` (create): `postCashTransaction` → `toast.success` → `invalidateQueries` `CASH_TRANSACTIONS_LIST_QUERY_KEY` | **Y** | — |
| OQ-2 / UX tạo | §5 | Server luôn Pending | Form tạo: ẩn chọn trạng thái, text “Chờ xử lý (server)”; mặc định form `status: Pending` | **Y** | — |
| Lỗi / giữ dialog | §8 | 400/403/409 | `ApiRequestError` → `toast.error`; không đóng dialog khi lỗi; `TransactionFormDialog` `await onSubmit` (không toast/close nội bộ) | **Y** | — |
| Chỉnh sửa | `API_Task067` | PATCH Task067 | `patchCashTransaction` + quyền Admin hoặc người tạo | **Y** | — |

Kết luận:
- Đã nối `POST /api/v1/cash-transactions` với **`fundId` bắt buộc** và danh sách quỹ `GET /cash-funds`.
- Sau Task067 (Completed), thêm `invalidateQueries` cho `FINANCE_LEDGER_LIST_QUERY_KEY` (Task063) nếu chưa có.
