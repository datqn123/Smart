# Task002 — E2E

> **ID:** `Task-002-E`  
> **Loại:** E2E / integration API  
> **SRS:** [`../../srs/SRS_Task002_logout.md`](../../srs/SRS_Task002_logout.md)  
> **Phụ thuộc:** `Task-002-F` hoàn thành (hoặc môi trường staging có build chứa feature)

## Mục tiêu

Xác thực **Given/When/Then** §5: login (Task001) → logout → gọi lại API với token cũ → **401**; kiểm tra DB `delete_ymd` không null sau logout thành công.

## Công cụ

- REST Assured / MockMvc full context / Testcontainers — chọn một, ghi trong ADR Task002 nếu khác mặc định.

## Verify

```text
cd backend/smart-erp && ./mvnw.cmd -q -Dtest=*Task002*E2E* test
```

## Definition of Done

- [ ] Ít nhất một E2E hoặc integration **đầu cuối** login→logout→expect 401.
- [ ] Postman JSON mẫu đồng bộ [`../../smart-erp/docs/postman/`](../../smart-erp/docs/postman/) (Tester).
