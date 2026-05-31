# Task002 — Feature (green)

> **ID:** `Task-002-F`  
> **Loại:** Feature  
> **SRS:** [`../../srs/SRS_Task002_logout.md`](../../srs/SRS_Task002_logout.md)  
> **Phụ thuộc:** `Task-002-U` (test skeleton / red đã merge hoặc cùng PR theo quy ước team)

## Mục tiêu

Triển khai **`POST /api/v1/auth/logout`**: JWT filter, body `refreshToken`, `UPDATE refresh_tokens … delete_ymd`, `INSERT SystemLogs`, sau commit → **remove `user_id` khỏi `LoginSessionRegistry`**; mã lỗi đúng §7 SRS.

## File đụng (dự kiến)

- `db/migration/V*__task002_refresh_tokens_delete_ymd.sql` (tên version tuân Flyway)
- `auth/**` — controller, service, repository, entity `RefreshToken` + field `delete_ymd`
- Đồng bộ Task001/Task003: query refresh có `delete_ymd IS NULL`

## Verify

```text
cd backend/smart-erp && ./mvnw.cmd verify
```

## Definition of Done

- [ ] `mvn verify` xanh; JaCoCo ≥ ngưỡng dự án.
- [ ] Không `DELETE` hàng refresh tại logout; chỉ `UPDATE delete_ymd`.
- [ ] Registry phiên: remove user sau commit DB.
