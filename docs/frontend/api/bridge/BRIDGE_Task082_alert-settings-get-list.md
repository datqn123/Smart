Task=Task082 | Path=/api/v1/alert-settings | Mode=wire-fe | Date=2026-04-30

Đã đọc `frontend/AGENTS/docs/FE_API_CONNECTION_GUIDE.md`: **Y**

| Hạng mục | API doc (mục) | Backend (file) | Frontend (`api/*.ts` + UI) | Khớp (Y/N) | Hành động |
| :--- | :--- | :--- | :--- | :---: | :--- |
| Endpoint + Query | `frontend/docs/api/API_Task082_alert_settings_get_list.md` §1–3 | `backend/smart-erp/src/main/java/com/example/smart_erp/settings/alerts/controller/AlertSettingsController.java` (GET `list`) | `frontend/mini-erp/src/features/settings/api/alertSettingsApi.ts` (`getAlertSettingsList`) | Y | OK |
| RBAC (Owner/Admin) | API doc §2 + SRS §6, §8.1 | `backend/smart-erp/src/main/java/com/example/smart_erp/settings/alerts/service/AlertSettingsService.java` (`Owner` scope theo JWT userId; `Admin` global + optional `ownerId`) | `frontend/mini-erp/src/features/settings/api/alertSettingsApi.ts` (`auth: true`) | Y | OK (FE luôn gửi Bearer; filter `ownerId` để Admin dùng khi cần) |
| Response shape | API doc §4 | `backend/smart-erp/src/main/java/com/example/smart_erp/settings/alerts/response/AlertSettingsListData.java`, `backend/smart-erp/src/main/java/com/example/smart_erp/settings/alerts/repository/AlertSettingsJdbcRepository.java` (map `items[]`) | `frontend/mini-erp/src/features/settings/pages/AlertSettingsPage.tsx` (load + map `alertType` → switch state) | Y | OK |

Kết luận:
- BE đã có endpoint `GET /api/v1/alert-settings` đúng path/query và RBAC theo SRS (Owner/Admin).
- FE đã nối dây endpoint qua `getAlertSettingsList()` và `AlertSettingsPage` load dữ liệu khi mở màn.
- Lưu ý: hiện màn chỉ **GET list**; toggle + nút “Lưu cấu hình” chưa gọi PATCH/POST (sẽ thuộc Task084/083).
