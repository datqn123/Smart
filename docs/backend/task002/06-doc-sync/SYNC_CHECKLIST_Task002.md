# Doc Sync — Checklist Task002

**SRS:** [`../../srs/SRS_Task002_logout.md`](../../srs/SRS_Task002_logout.md)  
**API:** [`../../../../frontend/docs/api/API_Task002_logout.md`](../../../../frontend/docs/api/API_Task002_logout.md)

## Sau khi merge code

- [ ] `API_Task002_logout.md`: ví dụ lỗi **500** dùng `error: "INTERNAL_SERVER_ERROR"` thay cho `INTERNAL_ERROR` nếu còn lệch [`API_RESPONSE_ENVELOPE.md`](../../../../frontend/docs/api/API_RESPONSE_ENVELOPE.md).  
- [ ] `API_PROJECT_DESIGN.md` §7: trạng thái tài liệu / link SRS trỏ `backend/docs/srs/SRS_Task002_logout.md` nếu có bảng trace.  
- [ ] Postman `docs/postman` khớp envelope thực tế.  
- [ ] Ghi `SYNC_REPORT_*` nếu drift > Low.

## Drift cần tránh

- SRS nói soft revoke + HashMap remove — code không được `DELETE` refresh tại logout.  
- Task001/Task003 đọc refresh thiếu `delete_ymd IS NULL`.
