# Task003 — E2E

> **ID:** `Task-003-E`  
> **Loại:** E2E / integration API  
> **SRS:** [`../../srs/SRS_Task003_auth_refresh.md`](../../srs/SRS_Task003_auth_refresh.md)  
> **Phụ thuộc:** `Task-003-F` hoàn thành (hoặc môi trường staging có build chứa feature)

## Mục tiêu

Xác thực **Given/When/Then** §5 SRS: login (Task001) → refresh → **200** + access mới + `refreshToken` không đổi chuỗi; sau logout (Task002) → refresh cùng token → **401**.

## Công cụ

- MockMvc full stack / Testcontainers / REST Assured — một hướng, Tech Lead ghi trong ADR Task003 nếu khác mặc định dự án.

## Verify

```text
cd backend/smart-erp && ./mvnw.cmd -q -Dtest=*Task003*E2E* test
```

_(Điều chỉnh pattern `-Dtest=` theo tên class thực tế.)_

## Definition of Done

- [ ] Luồng **login → refresh → expect 200** và **logout → refresh → 401** có ít nhất một bài kiểm thử đầu cuối hoặc tương đương được Tech Lead chấp nhận.  
- [ ] Postman mẫu trong repo đồng bộ contract (Tester).
