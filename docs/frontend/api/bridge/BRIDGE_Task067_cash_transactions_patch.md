# BRIDGE — Task067 — cash-transactions-patch

- Task: **Task067**
- Path: **`PATCH /api/v1/cash-transactions/{id}`**
- Mode: **wire-fe**
- Date: **2026-05-02**
- Đã đọc `FE_API_CONNECTION_GUIDE.md`: **Y**

| Hạng mục | API doc (mục) | Backend (file) | Frontend (`api/*.ts` + UI) | Khớp (Y/N) | Hành động |
| :--- | :--- | :--- | :--- | :---: | :--- |
| PATCH | `API_Task067_cash_transactions_patch.md` §5–§7 | `CashTransactionsController.patch` + `CashTransactionService.patch` (`assertCanMutateCashTx`: người tạo **hoặc** Admin) | `cashTransactionsApi.ts` — `patchCashTransaction` | **Y** | — |
| Body theo BR | §5, BR-10 | Pending / Completed / Cancelled rules | `TransactionsPage` — `buildCashTransactionPatchBody` + `handleFormSubmit` (ctx `source` từ Task066) | **Y** | — |
| Form UX | §10 | — | `TransactionFormDialog` — khóa hướng khi edit; khóa thuộc tính khi Completed/Cancelled (chỉ mô tả khi Cancelled) | **Y** | — |
| Invalidate | §1 + Task063 | — | Sau PATCH thành công: list + detail cash tx; nếu `updated.status === "Completed"` → `FINANCE_LEDGER_LIST_QUERY_KEY` | **Y** | — |
| Lỗi 403/409 | §8 | BE | `ApiRequestError` → toast, giữ dialog | **Y** | — |

Kết luận:
- Form **Sửa** gọi PATCH đúng luồng Pending / hoàn tất / huỷ + idempotent Completed.
- Sổ cái (`LedgerPage` / Task063) được làm mới khi phiếu ở trạng thái **Completed** (có thể vừa ghi sổ).
