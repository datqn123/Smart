# BRIDGE — Task066 — cash-transactions-get-by-id

- Task: **Task066**
- Path: **`GET /api/v1/cash-transactions/{id}`**
- Mode: **wire-fe**
- Date: **2026-05-02**
- Đã đọc `FE_API_CONNECTION_GUIDE.md`: **Y**

| Hạng mục | API doc (mục) | Backend (file) | Frontend (`api/*.ts` + UI) | Khớp (Y/N) | Hành động |
| :--- | :--- | :--- | :--- | :---: | :--- |
| GET by id | `API_Task066_cash_transactions_get_by_id.md` §2, §6 | `CashTransactionsController.getById` | `cashTransactionsApi.ts` — `getCashTransactionById`, `CASH_TRANSACTION_DETAIL_QUERY_KEY` | **Y** | — |
| Chi tiết dialog | §6 + OQ-4 | — | `TransactionDetailDialog.tsx` — `useQuery` khi `isOpen` + `transactionId`; hiển thị `fundCode`/`fundId`, `createdByName` / `performedByName` | **Y** | — |
| Form sửa | §10 prefill | — | `TransactionFormDialog.tsx` — `detailSourceId` + cùng query; reset form từ API; overlay tải lần đầu | **Y** | Task067 PATCH sau |
| Map type | — | JSON `CashTransaction` | Dùng `Transaction` / `CashTransaction` từ `types.ts` | **Y** | — |

Kết luận:
- Đã gọi Task066 khi mở **Xem chi tiết** và khi mở **Sửa** (prefill đồng bộ server).
- Sau Task067 nên `invalidateQueries` detail + list (+ ledger khi Completed).
