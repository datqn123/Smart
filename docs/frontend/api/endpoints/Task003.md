# Task003 — Auth: refresh token

| Path | Method | Spec API | Request mẫu (body) | Response mẫu | Postman (3 file) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `/api/v1/auth/refresh` | POST | [`API_Task003_auth_refresh.md`](../API_Task003_auth_refresh.md) | [`samples/Task003/refresh.request.json`](../samples/Task003/refresh.request.json) | [`refresh.response.200.json`](../samples/Task003/refresh.response.200.json), [`refresh.response.400.json`](../samples/Task003/refresh.response.400.json), [`refresh.response.401.json`](../samples/Task003/refresh.response.401.json) | [`Task003_refresh.valid.body.json`](../../../../backend/smart-erp/docs/postman/Task003_refresh.valid.body.json), [`Task003_refresh.invalid.missing-refresh.body.json`](../../../../backend/smart-erp/docs/postman/Task003_refresh.invalid.missing-refresh.body.json), [`Task003_refresh.invalid.empty-refresh.body.json`](../../../../backend/smart-erp/docs/postman/Task003_refresh.invalid.empty-refresh.body.json) |

**UI:** interceptor / `auth` module — `FEATURES_UI_INDEX` → `auth/`; không gắn một route menu cố định.
