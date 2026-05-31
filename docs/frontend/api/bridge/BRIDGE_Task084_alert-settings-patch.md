Task=Task084 | Path=/api/v1/alert-settings/{id} | Mode=wire-fe | Date=2026-04-30

Đã đọc `frontend/AGENTS/docs/FE_API_CONNECTION_GUIDE.md`: **Y**

| Hạng mục | API doc (mục) | Backend (file) | Frontend (`api/*.ts` + UI) | Khớp (Y/N) | Hành động |
| :--- | :--- | :--- | :--- | :---: | :--- |
| Endpoint + body partial | `frontend/docs/api/API_Task084_alert_settings_patch.md` §1–2 | `backend/smart-erp/src/main/java/com/example/smart_erp/settings/alerts/controller/AlertSettingsController.java` (PATCH `patch`) + `backend/smart-erp/src/main/java/com/example/smart_erp/settings/alerts/service/AlertSettingsService.java` (`PATCH_KEYS`) | `frontend/mini-erp/src/features/settings/api/alertSettingsApi.ts` (`patchAlertSetting`) + `frontend/mini-erp/src/features/settings/pages/AlertSettingsPage.tsx` (Lưu cấu hình → PATCH) | Y | OK |
| Rule: body không rỗng → 400 | API doc Zod refine + SRS §8.3.2 (Rule) | `backend/smart-erp/src/main/java/com/example/smart_erp/settings/alerts/service/AlertSettingsService.java` (body `isEmpty` → `BAD_REQUEST` + details `body`) | `frontend/mini-erp/src/features/settings/pages/AlertSettingsPage.tsx` (body luôn có `isEnabled` và/hoặc `thresholdValue`; map 400(details) → toast) | Y | OK |
| 404 trong scope owner | API doc §4 + SRS §8.3.5 | `backend/smart-erp/src/main/java/com/example/smart_erp/settings/alerts/service/AlertSettingsService.java` + `backend/smart-erp/src/main/java/com/example/smart_erp/settings/alerts/repository/AlertSettingsJdbcRepository.java` | `frontend/mini-erp/src/features/settings/pages/AlertSettingsPage.tsx` (catch `ApiRequestError` 404 → toast) | Y | OK |

Kết luận:
- BE đã implement PATCH partial, enforce body không rỗng (400), và 404 khi không tìm thấy trong scope owner.
- FE đã nối dây `patchAlertSetting()` và móc mutation vào `AlertSettingsPage` (toggle + chỉnh ngưỡng; bấm “Lưu cấu hình” để PATCH).
