Task=Task083 | Path=/api/v1/alert-settings | Mode=wire-fe | Date=2026-04-30

Đã đọc `frontend/AGENTS/docs/FE_API_CONNECTION_GUIDE.md`: **Y**

| Hạng mục | API doc (mục) | Backend (file) | Frontend (`api/*.ts` + UI) | Khớp (Y/N) | Hành động |
| :--- | :--- | :--- | :--- | :---: | :--- |
| Endpoint + method | `frontend/docs/api/API_Task083_alert_settings_post.md` §1 | `backend/smart-erp/src/main/java/com/example/smart_erp/settings/alerts/controller/AlertSettingsController.java` (POST `create`) | `frontend/mini-erp/src/features/settings/api/alertSettingsApi.ts` (`postCreateAlertSetting`) | Y | OK |
| Request body + default | API doc §2 + SRS §8.2.2 | `backend/smart-erp/src/main/java/com/example/smart_erp/settings/alerts/dto/AlertSettingCreateRequest.java` + `backend/smart-erp/src/main/java/com/example/smart_erp/settings/alerts/service/AlertSettingsService.java` (default `frequency=Realtime`, `isEnabled=true`) | `frontend/mini-erp/src/features/settings/api/alertSettingsApi.ts` (`AlertSettingCreateBody`) | Y | OK |
| Response 201 envelope | API doc §4 + SRS §8.2.4 | `backend/smart-erp/src/main/java/com/example/smart_erp/settings/alerts/controller/AlertSettingsController.java` trả `201 Created` + envelope | `frontend/mini-erp/src/features/settings/api/alertSettingsApi.ts` (apiJson parse envelope) | Y | OK |
| Lỗi 409 trùng rule | API doc §3 + SRS §8.2.5 (409) | `backend/smart-erp/src/main/java/com/example/smart_erp/settings/alerts/service/AlertSettingsService.java` (catch → 409) | `frontend/mini-erp/src/features/settings/pages/AlertSettingsPage.tsx` (catch `ApiRequestError` status 409 → toast) | Y | OK |

Kết luận:
- BE đã implement `POST /api/v1/alert-settings` đúng 201 envelope và 409 CONFLICT khi trùng `(owner_id, alert_type)` theo SRS §8.2.
- FE đã nối dây `postCreateAlertSetting()` và móc vào `AlertSettingsPage` (nút “Lưu cấu hình” sẽ tạo các rule còn thiếu).
