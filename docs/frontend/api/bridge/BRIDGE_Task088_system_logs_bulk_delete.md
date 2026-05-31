Task=Task088 | Path=POST /api/v1/system-logs/bulk-delete | Mode=verify | Date=2026-04-30

Đã đọc `frontend/AGENTS/docs/FE_API_CONNECTION_GUIDE.md`: **Y**

| Hạng mục | API doc (mục) | Backend (file) | Frontend (`api/*.ts` + UI) | Khớp (Y/N) | Hành động |
| :--- | :--- | :--- | :--- | :---: | :--- |
| Endpoint + Body | `frontend/docs/api/API_Task088_system_logs_bulk_delete.md` §1–2 | `backend/smart-erp/src/main/java/com/example/smart_erp/settings/controller/SystemLogsController.java` (POST `bulkDelete`) | UI hiện có bulk delete mock: `frontend/mini-erp/src/features/settings/pages/LogsPage.tsx` (xóa local list) | N | `wire-fe` hoặc ẩn bulk delete theo policy |
| Policy tuân thủ (cấm xoá) | API doc §3 (nói “có thể cấm”) | `backend/smart-erp/src/main/java/com/example/smart_erp/settings/systemlogs/SystemLogsService.java` (`bulkDelete` luôn throw 403 theo policy) | UI hiện vẫn cho bulk delete mock | N | `fix-fe`: ẩn nút “xóa hàng loạt” theo SRS Approved |
| Validation ids (1..100) | API doc §2, §6 | `SystemLogsController.parseIds()` (min 1, max 100, positive) | — | Y (BE) / N (FE) | Khi/ nếu gọi API, FE cần validate theo Zod để UX tốt |
| Response `200 OK` (deletedCount) | API doc §4 | BE hiện luôn 403; controller có response 200 (không reachable) | — | N | `fix-doc`: cập nhật API doc theo quyết định PO (cấm xoá → 403) |

Kết luận:
- BE đã có path đúng spec và validate `ids`, nhưng policy theo SRS Approved khiến endpoint luôn 403.
- FE hiện bulk delete bằng mock; cần ẩn/disable UI để không mâu thuẫn policy.
- API doc Task088 đang mô tả 200 OK; cần Doc Sync để phản ánh policy cấm xoá.

