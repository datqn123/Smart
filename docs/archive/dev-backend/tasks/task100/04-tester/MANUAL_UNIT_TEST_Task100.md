# Task100 — Kiểm thử thủ công (session map / JWT hết hạn)

**SRS:** [`../../srs/SRS_Task100_auth-session-registry-stale-access.md`](../../srs/SRS_Task100_auth-session-registry-stale-access.md)  
**Postman:** dùng [`../../../smart-erp/docs/postman/Task001_login.valid.body.json`](../../../smart-erp/docs/postman/Task001_login.valid.body.json) (chỉ `POST /auth/login`).

## U-100-01 — Sau khi access hết hạn, login lại không bị 403 oan

**Given:** Đã `POST /api/v1/auth/login` thành công; **không** gọi refresh; **không** logout.  
**When:** Chờ thời gian **lớn hơn TTL access JWT** (hiện cấu hình trong `JwtTokenService` — ví dụ 10 phút nếu code đang là 10).  
**Then:** `POST /api/v1/auth/login` lại cùng user → **200** (không 403 “thiết bị khác” chỉ vì map).

**Pass/Fail:** ______ **Ghi chú:** ________________________

## U-100-02 — Hai tab cùng access còn hạn vẫn bị chặn

**Given:** Session A đã login, access còn hạn.  
**When:** Login lần 2 cùng user (thiết bị/phiên khác).  
**Then:** **403** theo Task001.

**Pass/Fail:** ______ **Ghi chú:** ________________________

## E2E (manual)

Login → chờ TTL → login lại → kiểm tra response + có thể gọi một API cần JWT nếu profile `jwt-api` (tuỳ môi trường).
