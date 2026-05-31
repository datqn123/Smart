# Task001 — Auth: đăng nhập

| Path | Method | Spec API | Request mẫu (body) | Response mẫu | Postman (3 file) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `/api/v1/auth/login` | POST | [`API_Task001_login.md`](../API_Task001_login.md) | [`samples/Task001/login.request.json`](../samples/Task001/login.request.json) | [`login.response.200.json`](../samples/Task001/login.response.200.json), [`login.response.400.json`](../samples/Task001/login.response.400.json), [`login.response.401.json`](../samples/Task001/login.response.401.json) | [`Task001_login.valid.body.json`](../../../../backend/smart-erp/docs/postman/Task001_login.valid.body.json), [`Task001_login.invalid.missing-fields.body.json`](../../../../backend/smart-erp/docs/postman/Task001_login.invalid.missing-fields.body.json), [`Task001_login.invalid.short-password.body.json`](../../../../backend/smart-erp/docs/postman/Task001_login.invalid.short-password.body.json) |

**UI mặc định:** [`FEATURES_UI_INDEX`](../../../mini-erp/src/features/FEATURES_UI_INDEX.md) — `/login` → `auth/pages/LoginPage.tsx`, form `auth/components/LoginForm.tsx`.
