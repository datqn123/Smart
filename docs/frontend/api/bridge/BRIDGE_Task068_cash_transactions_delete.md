# BRIDGE — Task068 — cash-transactions-delete

- Task: **Task068**
- Path: **`DELETE /api/v1/cash-transactions/{id}`**
- Mode: **wire-fe**
- Date: **2026-05-02**
- Đã đọc `FE_API_CONNECTION_GUIDE.md`: **Y**

| Hạng mục | API doc (mục) | Backend (file) | Frontend (`api/*.ts` + UI) | Khớp (Y/N) | Hành động |
| :--- | :--- | :--- | :--- | :---: | :--- |
| DELETE | `API_Task068_cash_transactions_delete.md` §2, §6 | `CashTransactionsController.delete` + quyền người tạo **hoặc** Admin | `cashTransactionsApi.ts` — `deleteCashTransaction` (`apiJson<null>`) | **Y** | — |
| UI xóa | §10 | — | `TransactionsPage`: toolbar **Xoá** (`deleteByIds(selectedIds)`); bảng **onDelete** một `id`; `window.confirm` | **Y** | — |
| Invalidate | prompt | — | Sau xóa thành công: `invalidateQueries` list; `removeQueries` từng `CASH_TRANSACTION_DETAIL_QUERY_KEY` + `id` | **Y** | — |
| Đóng overlay | — | — | Nếu xóa đúng `selectedItem` → clear + đóng chi tiết / form | **Y** | — |
| 403/409 | §8 | BE | `ApiRequestError` → toast; dừng chuỗi xóa nhiều khi lỗi | **Y** | — |

Kết luận:
- Đã nối Task068 từ màn Giao dịch thu chi (xóa một hoặc nhiều id đã chọn, tuần tự).
- Phiếu **Completed** / đã có sổ → BE **409**; UI đã ghi chú trong confirm.
