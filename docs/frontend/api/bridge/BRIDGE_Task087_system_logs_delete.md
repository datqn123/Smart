Task=Task087 | Path=DELETE /api/v1/system-logs/{id} | Mode=verify | Date=2026-04-30

Đã đọc `frontend/AGENTS/docs/FE_API_CONNECTION_GUIDE.md`: **Y**

| Hạng mục | API doc (mục) | Backend (file) | Frontend (`api/*.ts` + UI) | Khớp (Y/N) | Hành động |
| :--- | :--- | :--- | :--- | :---: | :--- |
| Endpoint | `frontend/docs/api/API_Task087_system_logs_delete.md` §1 | `backend/smart-erp/src/main/java/com/example/smart_erp/settings/controller/SystemLogsController.java` (DELETE `delete`) | UI hiện có nút xoá mock: `frontend/mini-erp/src/features/settings/pages/LogsPage.tsx` (confirm delete cập nhật state local) | N | `wire-fe`: gọi API thật hoặc ẩn nút xoá theo policy |
| Policy tuân thủ (cấm xoá) | API doc §2 (có đề cập có thể cấm) | `backend/smart-erp/src/main/java/com/example/smart_erp/settings/systemlogs/SystemLogsService.java` (`deleteById` luôn throw 403 theo policy) | UI hiện vẫn cho xoá mock | N | `fix-fe`: ẩn nút xoá / disable bulk delete (theo SRS Approved) |
| Response code / envelope | API doc §4 (**[CẦN CHỐT]** 200 vs 204) | BE hiện luôn 403; controller trả `204` nhưng không reachable vì service throw 403 | — | N | `fix-doc`: cập nhật API doc theo quyết định PO (cấm xoá → 403) và bỏ mục “200 vs 204” |
| RBAC | API doc §3 | `MenuPermissionClaims` + `V30__task086_can_view_system_logs_permission.sql` | — | Y (BE) / N (FE) | Khi/ nếu cho gọi, FE dùng Bearer theo guide |

Kết luận:
- Theo SRS Approved, policy **cấm xoá log** → BE đã enforce 403 cho `DELETE`.
- FE hiện vẫn xử lý xoá bằng mock state; cần ẩn nút xoá để tránh UX sai.
- API doc Task087 đang Draft và còn mục “[CẦN CHỐT]”; cần Doc Sync theo quyết định PO.

