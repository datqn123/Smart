Task=Task086 | Path=GET /api/v1/system-logs | Mode=verify | Date=2026-04-30

Đã đọc `frontend/AGENTS/docs/FE_API_CONNECTION_GUIDE.md`: **Y**

| Hạng mục | API doc (mục) | Backend (file) | Frontend (`api/*.ts` + UI) | Khớp (Y/N) | Hành động |
| :--- | :--- | :--- | :--- | :---: | :--- |
| Endpoint + Query | `frontend/docs/api/API_Task086_system_logs_get_list.md` §1–3 | `backend/smart-erp/src/main/java/com/example/smart_erp/settings/controller/SystemLogsController.java` (GET `list`) · `backend/smart-erp/src/main/java/com/example/smart_erp/settings/systemlogs/SystemLogsService.java` · `backend/smart-erp/src/main/java/com/example/smart_erp/settings/systemlogs/SystemLogsJdbcRepository.java` | UI hiện có nhưng **chưa gọi API**: `frontend/mini-erp/src/features/settings/pages/LogsPage.tsx` (mock) · `frontend/mini-erp/src/features/settings/components/LogTable.tsx` · `frontend/mini-erp/src/features/settings/components/LogToolbar.tsx` | N | `wire-fe`: tạo `frontend/mini-erp/src/features/settings/api/systemLogsApi.ts` và thay mock bằng call `apiJson` |
| RBAC | API doc §2 | `backend/smart-erp/src/main/java/com/example/smart_erp/auth/support/MenuPermissionClaims.java` (thêm `can_view_system_logs`) · `backend/smart-erp/src/main/resources/db/migration/V30__task086_can_view_system_logs_permission.sql` | Chưa có layer API nên chưa thể hiện Bearer/401/403 trong UI | Y (BE) / N (FE) | FE cần xử lý 403 theo guide (toast/redirect tuỳ UX) |
| Response shape | API doc §4 | `backend/smart-erp/src/main/java/com/example/smart_erp/settings/systemlogs/response/SystemLogsListData.java` · `backend/smart-erp/src/main/java/com/example/smart_erp/settings/systemlogs/response/SystemLogItemData.java` | `frontend/mini-erp/src/features/settings/log-types.ts` (type FE) | Y (BE) / ? (FE) | Khi `wire-fe`, map field theo spec (`timestamp`, `severity`, `ipAddress`) |
| Search scope | API doc §3 (không nêu `context_data`) | `SystemLogsJdbcRepository` search có `s.context_data::text ILIKE :search` | — | N (doc vs BE) | `fix-doc`: cập nhật API doc mô tả search gồm cả `context_data` (theo SRS Approved) |

Kết luận:
- BE đã có `GET /api/v1/system-logs` theo envelope và filter/paging; RBAC dùng `can_view_system_logs`.
- FE màn `LogsPage` hiện đang dùng mock và chưa có `features/settings/api/*` cho endpoint này.
- API doc Task086 cần đồng bộ lại phạm vi search (bao gồm `context_data`) và trạng thái (hiện vẫn Draft).

