# BRIDGE — Task063 — finance-ledger-get-list

- Task: **Task063**
- Path: **`GET /api/v1/finance-ledger`**
- Mode: **wire-fe**
- Date: **2026-04-29**
- Đã đọc `FE_API_CONNECTION_GUIDE.md`: **Y**

| Hạng mục | API doc (mục) | Backend (file) | Frontend (`api/*.ts` + UI) | Khớp (Y/N) | Hành động |
| :--- | :--- | :--- | :--- | :---: | :--- |
| Endpoint + query | `frontend/docs/api/API_Task063_finance_ledger_get_list.md` §4–§7 | (chưa đối chiếu trong phiên) | `frontend/mini-erp/src/features/cashflow/api/financeLedgerApi.ts` + `frontend/mini-erp/src/features/cashflow/pages/LedgerPage.tsx` | Y | Đã tạo hàm gọi API + truyền query `dateFrom/dateTo/search/page/limit` |
| Auth Bearer | Task063 §5.1 | (chưa đối chiếu trong phiên) | `financeLedgerApi.ts` (`auth: true`) | Y | Dùng `apiJson` theo guide FE |
| Render bảng items | Task063 §7 (`data.items[]`) | (chưa đối chiếu trong phiên) | `LedgerPage.tsx` → `LedgerTable.tsx` | Y | Thay mock bằng `data.items` |
| Pagination | Task063 §5.2 (`page`, `limit`) + §7 (`total`) | (chưa đối chiếu trong phiên) | `LedgerPage.tsx` | Y | UI có nút Trước/Sau, tính `totalPages` từ `total` |
| Error handling | Task063 §9 + envelope | (chưa đối chiếu trong phiên) | `LedgerPage.tsx` (toast với `ApiRequestError`) | Y | Hiển thị toast khi query lỗi |

Kết luận:
- Đã nối `GET /api/v1/finance-ledger` vào màn `/cashflow/ledger` theo contract Task063.
- Cashflow hiện vẫn còn mock cho Transactions/Debt (ngoài phạm vi Task063).

