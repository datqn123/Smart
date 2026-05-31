Task=Task085 | Path=/api/v1/alert-settings/{id} | Mode=wire-fe | Date=2026-04-30

Đã đọc `frontend/AGENTS/docs/FE_API_CONNECTION_GUIDE.md`: **Y**

| Hạng mục | API doc (mục) | Backend (file) | Frontend (`api/*.ts` + UI) | Khớp (Y/N) | Hành động |
| :--- | :--- | :--- | :--- | :---: | :--- |
| Endpoint + response 204 | `frontend/docs/api/API_Task085_alert_settings_delete.md` §1–3 | `backend/smart-erp/src/main/java/com/example/smart_erp/settings/alerts/controller/AlertSettingsController.java` (DELETE `softDisable` → 204) | `frontend/mini-erp/src/features/settings/api/alertSettingsApi.ts` (`deleteAlertSetting`) | Y | OK |
| Hành vi soft disable | API doc §3 + SRS §8.4 | `backend/smart-erp/src/main/java/com/example/smart_erp/settings/alerts/service/AlertSettingsService.java` + `backend/smart-erp/src/main/java/com/example/smart_erp/settings/alerts/repository/AlertSettingsJdbcRepository.java` (`UPDATE ... SET is_enabled=FALSE`) | `frontend/mini-erp/src/features/settings/pages/AlertSettingsPage.tsx` (nút “Xóa” → DELETE; update local state `isEnabled=false`) | Y | OK |

Kết luận:
- BE đã implement DELETE đúng 204 và thực chất là **soft disable** (`is_enabled=false`), không xóa vật lý.
- FE đã nối dây `deleteAlertSetting()` và móc hành vi “Xóa” vào `AlertSettingsPage` (gọi DELETE và cập nhật local state để switch về false).
