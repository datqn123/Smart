# BRIDGE — Task069–072 — debts-api

- Task: **Task069–Task072**
- Paths: **`GET|POST /api/v1/debts`**, **`GET|PATCH /api/v1/debts/{id}`**
- Mode: **verify** (BE đã triển khai; FE `DebtPage` chưa bắt buộc trong phiên này)
- Date: **2026-04-30**
- Đã đọc `FE_API_CONNECTION_GUIDE.md`: **Y** (theo quy trình API_BRIDGE sau G-DEV)

| Hạng mục | API doc | Backend | Frontend | Khớp (Y/N) | Hành động |
| :--- | :--- | :--- | :--- | :---: | :--- |
| Endpoint + query/body | `API_Task069` … `API_Task072` | `DebtsController.java`, `PartnerDebtService.java`, `PartnerDebtJdbcRepository.java` | `cashflow/pages/DebtPage.tsx` (mock) | N | Tạo `debtsApi.ts` + TanStack Query khi `wire-fe` |
| Auth + `can_view_finance` | Task069 §4 | `FinanceLedgerAccessPolicy` + controller | — | Y | Giống ledger/cash tx |
| Flyway `created_by` | SRS §4 OQ-2 | `V26__task069_072_partner_debts_created_by.sql` | — | Y | Chạy migrate Postgres |
| PATCH chủ sở hữu / Cleared | Task072, SRS BR-9 | `PartnerDebtService.patch` | — | Y | Kiểm thử tay / FE sau nối |

Kết luận: Backend Spring đủ 4 endpoint theo SRS Approved; mini-erp Sổ nợ cần phiên **wire-fe** để thay mock.
