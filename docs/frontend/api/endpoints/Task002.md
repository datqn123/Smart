# Task002 — Auth: đăng xuất

| Path | Method | Spec API | Request mẫu (body) | Response mẫu | Postman (3 file) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `/api/v1/auth/logout` | POST | [`API_Task002_logout.md`](../API_Task002_logout.md) | [`samples/Task002/logout.request.json`](../samples/Task002/logout.request.json) | [`logout.response.200.json`](../samples/Task002/logout.response.200.json), [`logout.response.400.json`](../samples/Task002/logout.response.400.json) | [`Task002_logout.valid.body.json`](../../../../backend/smart-erp/docs/postman/Task002_logout.valid.body.json), [`Task002_logout.invalid.missing-refresh.body.json`](../../../../backend/smart-erp/docs/postman/Task002_logout.invalid.missing-refresh.body.json), [`Task002_logout.invalid.empty-refresh.body.json`](../../../../backend/smart-erp/docs/postman/Task002_logout.invalid.empty-refresh.body.json) |

**Header:** `Authorization: Bearer <accessToken>` (không nằm trong file body mẫu).

**UI:** thường gọi từ layout / menu đăng xuất — tra `FEATURES_UI_INDEX` + `Grep` `logout` trong `mini-erp/src`.
