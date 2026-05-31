# Developer — Handoff Task002

**SRS:** [`../../srs/SRS_Task002_logout.md`](../../srs/SRS_Task002_logout.md)  
**PM:** [`../01-pm/`](../01-pm/)  
**ADR:** [`../02-tech-lead/ADR-Task002-logout-soft-revoke-session.md`](../02-tech-lead/ADR-Task002-logout-soft-revoke-session.md)

## Checklist triển khai

1. [ ] Flyway: thêm `delete_ymd TIMESTAMPTZ NULL` vào `refresh_tokens`.  
2. [ ] Entity + repository: hỗ trợ `UPDATE` soft revoke; đọc refresh hợp lệ có `delete_ymd IS NULL`.  
3. [ ] Sửa **Task001** (lưu refresh), **Task003** (nếu đã có): chỉ tương tác bản ghi `delete_ymd IS NULL`.  
4. [ ] `POST /api/v1/auth/logout`: validate body, JWT → `user_id`, transaction `UPDATE` + `INSERT SystemLogs`.  
5. [ ] Sau `commit`: `LoginSessionRegistry` (hoặc tên hiện tại) **remove** theo `user_id`.  
6. [ ] 500 → `INTERNAL_SERVER_ERROR` khớp envelope.  
7. [ ] `./mvnw.cmd verify` xanh.

## Không làm

- Không `DELETE` row `refresh_tokens` tại logout (trừ task archive sau này).  
- Không strip `refreshToken` theo kiểu gây đổi nghĩa token (xem `DEVELOPER_AGENT_INSTRUCTIONS`).
