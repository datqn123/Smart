# SRS — Đăng xuất hệ thống (Task002 / Authentication)

> **File**: `backend/docs/task002/00-ba/SRS_Task002_logout.md`  
> **API**: [`../../../../frontend/docs/api/API_Task002_logout.md`](../../../../frontend/docs/api/API_Task002_logout.md)  
> **Envelope**: [`../../../../frontend/docs/api/API_RESPONSE_ENVELOPE.md`](../../../../frontend/docs/api/API_RESPONSE_ENVELOPE.md)  
> **Liên quan**: [`../../srs/SRS_Task001_login-authentication.md`](../../srs/SRS_Task001_login-authentication.md) (phiên đơn, refresh DB — tạo tại `backend/docs/srs/` khi có)  
> **Chuỗi Agent (sau BA)**: [`../../README.md`](../../README.md)  
> **Ngày cập nhật**: 24/04/2026  
> **Phiên bản**: 1.2  
> **Trạng thái**: **Approved** (PO đã chốt mục §7 — 24/04/2026)

---

## 1. Tóm tắt

Người dùng đã đăng nhập gọi **`POST /api/v1/auth/logout`** kèm **Bearer access token** và **refresh token** trong body để **thu hồi phiên**: đánh dấu refresh đã huỷ bằng cột **`delete_ymd`** (cập nhật thời điểm thu hồi — **không** `DELETE` hàng), **gỡ `user_id` khỏi registry phiên đơn** (ConcurrentHashMap như Task001; Redis sau này nếu có), ghi **SystemLogs**, sau đó client xóa token cục bộ. Sau logout thành công, access/refresh cũ không còn dùng được (**401**).

**Nguồn refresh:** chỉ **PostgreSQL** `refresh_tokens` (đã chốt PO).

---

## 2. Phạm vi

| In | Out (task khác) |
| :--- | :--- |
| `POST /api/v1/auth/logout`, validation `refreshToken`, mã 200/400/401/403/500 theo API | Refresh rotation (Task003), đổi mật khẩu |
| Đồng bộ Task001: registry phiên đơn (remove user khi logout) | MFA, revoke đa thiết bị |
| Soft revoke `delete_ymd` + audit | Partition/archive bảng `refresh_tokens` (tech debt) |

---

## 3. Persona & RBAC

- **Owner, Staff, Admin** đã đăng nhập (cùng quy tắc API Task002).
- Thiếu/không hợp lệ Bearer → **401** (theo API).

---

## 4. Luồng server (rút gọn)

1. Xác thực JWT access → `user_id`; không hợp lệ/hết hạn → **401**.  
2. Bean Validation body: `refreshToken` bắt buộc, không rỗng → thiếu/sai → **400** + `details.refreshToken` (theo API + Zod).  
3. Thu hồi refresh: **`UPDATE refresh_tokens SET delete_ymd = now()`** với điều kiện §6.4; **0 dòng cập nhật** → **403** (§7.2).  
4. **Gỡ phiên đơn:** remove `user_id` khỏi **LoginSessionRegistry** (ConcurrentHashMap) ngay trong luồng logout — §7.4. Thực hiện **sau khi DB transaction commit** thành công (§6.4).  
5. Ghi **SystemLogs** (INFO, AUTH, LOGOUT) — cùng transaction DB với bước 3.  
6. Trả **200** + message cố định trong API.

---

## 5. Acceptance Criteria (Given / When / Then)

### 5.1 Thành công

```text
Given người dùng đã đăng nhập với access hợp lệ và refreshToken khớp user_id trong JWT và bản ghi refresh còn hiệu lực (delete_ymd IS NULL)
When gọi POST /api/v1/auth/logout với Authorization Bearer và body { "refreshToken": "<token>" }
Then HTTP 200, success true, data {}, message đúng API Task002 §3.1
  And delete_ymd của bản ghi refresh đó được gán thời điểm thu hồi
  And user_id không còn trong registry phiên đơn (HashMap)
  And một dòng SystemLogs (INFO, AUTH, LOGOUT) đã ghi cho user_id
```

### 5.2 400 — thiếu refresh

```text
Given người dùng gửi request thiếu refreshToken hoặc chuỗi rỗng
When POST /api/v1/auth/logout
Then HTTP 400, BAD_REQUEST, details.refreshToken chứa message theo API §3.2
```

### 5.3 401 — access không hợp lệ

```text
Given Authorization thiếu/sai/hết hạn
When POST /api/v1/auth/logout
Then HTTP 401, UNAUTHORIZED, message theo API §3.2
```

### 5.4 403 — refresh không hợp lệ / đã thu hồi

```text
Given access hợp lệ nhưng refreshToken không khớp bản ghi (user_id + token) hoặc delete_ymd đã khác NULL
When POST /api/v1/auth/logout
Then HTTP 403, FORBIDDEN, message theo API §3.2 (Forbidden)
```

### 5.5 Sau logout — token cũ vô hiệu

```text
Given logout vừa thành công (200)
When client gọi API khác hoặc refresh với access/refresh cũ
Then server trả 401 (theo API §4.2)
```

---

## 6. Dữ liệu & SQL tham chiếu (đồng soạn BA + SQL)

### 6.1 Lý do dùng `UPDATE` + `delete_ymd` thay vì `DELETE`

- Thu hồi logic: chỉ chấp nhận refresh còn hiệu lực khi **`delete_ymd IS NULL`**.  
- `UPDATE` một hàng theo `token` (UNIQUE) thường **ổn định / nhanh** hơn `DELETE` trong kịch bản ghi WAL tần suất cao.  
- **Tech debt:** bảng lớn dần — **chưa** archive/partition trong Task002 (§7.5); follow-up sau MVP.

### 6.2 Schema bổ sung (migration sau `V3__task001_refresh_tokens.sql`)

```sql
ALTER TABLE refresh_tokens
    ADD COLUMN IF NOT EXISTS delete_ymd TIMESTAMPTZ NULL;

COMMENT ON COLUMN refresh_tokens.delete_ymd IS 'Thời điểm thu hồi (soft delete). NULL = còn hiệu lực.';
```

**Đọc chéo:** Task001 (phát refresh), Task003 (refresh) — mọi truy vấn refresh hợp lệ phải có **`delete_ymd IS NULL`**.

### 6.3 Bảng tham chiếu

- `refresh_tokens` — `V3` + cột `delete_ymd`.  
- `SystemLogs` — `V1`.

### 6.4 SQL thu hồi + audit + thứ tự phiên DB / map

```sql
UPDATE refresh_tokens
SET delete_ymd = CURRENT_TIMESTAMP
WHERE user_id = :userIdFromJwt
  AND token = :refreshTokenFromBody
  AND delete_ymd IS NULL;

INSERT INTO "SystemLogs" (log_level, module, action, user_id, message)
VALUES ('INFO', 'AUTH', 'LOGOUT', :userIdFromJwt, 'Người dùng đã đăng xuất');
```

- **Transaction DB:** `UPDATE` + `INSERT` trong **một** `@Transactional` (commit cùng lúc).  
- **Registry phiên (HashMap):** sau **commit thành công**, gọi remove theo `user_id` (PO §7.4). Nếu remove thất bại (bất thường) → log WARNING, metric; không rollback DB đã commit (ADR `../task002/02-tech-lead/ADR-Task002-logout-soft-revoke-session.md`).

**500:** dùng mã envelope **`INTERNAL_SERVER_ERROR`** ([`API_RESPONSE_ENVELOPE.md`](../../../frontend/docs/api/API_RESPONSE_ENVELOPE.md) §3.3). Doc Sync chỉnh ví dụ JSON trong `API_Task002_logout.md` nếu còn ghi `INTERNAL_ERROR`.

---

## 7. Quy tắc đã chốt (PO — 24/04/2026)

| Mã | Chủ đề | Quyết định |
| :--- | :--- | :--- |
| **7.1** | Nguồn refresh | **Chỉ PostgreSQL** — bảng `refresh_tokens`; không dùng Redis làm store refresh. |
| **7.2** | `UPDATE` 0 dòng | **403 FORBIDDEN** khi JWT access hợp lệ nhưng không cập nhật được đúng một bản ghi refresh hợp lệ (sai cặp user/token, hoặc đã logout / `delete_ymd` đã set). **401** chỉ cho access không hợp lệ / hết hạn. |
| **7.3** | Lỗi 500 | **`INTERNAL_SERVER_ERROR`** theo envelope dự án; đồng bộ `GlobalExceptionHandler` và tài liệu API. |
| **7.4** | Phiên sau logout | **Remove `user_id` khỏi ConcurrentHashMap** (registry phiên đơn Task001) trong luồng logout, sau commit DB. |
| **7.5** | Dung lượng bảng | **Không** triển khai partition/archive trong Task002; ghi tech debt, xử lý task sau. |

---

## 8. Handoff

- **DEV**: Flyway thêm `delete_ymd`; logout `UPDATE` + log; sau commit → remove session map; cập nhật đọc refresh Task001/Task003 thêm `delete_ymd IS NULL`; `@Transactional` phạm vi DB.  
- **TESTER**: Postman + test tự động — 200 (delete_ymd set), 403 (idempotent logout / sai token), 401 access hỏng; đối chiếu [`../task002/04-tester/TEST_PLAN_Task002.md`](../task002/04-tester/TEST_PLAN_Task002.md).  
- **PM / TL / DS**: artifact theo [`../task002/README.md`](../task002/README.md).

---

## 9. Traceability

| Nguồn | Mục đích |
| :--- | :--- |
| [`API_Task002_logout.md`](../../../frontend/docs/api/API_Task002_logout.md) | Hợp đồng HTTP |
| [`API_RESPONSE_ENVELOPE.md`](../../../frontend/docs/api/API_RESPONSE_ENVELOPE.md) | Mã `error` chuẩn |
| Flyway `V1`, `V3` + migration `delete_ymd` | Schema |
| SRS Task001 | Phiên đơn, refresh DB, registry |
