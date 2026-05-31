# Task003 — Feature (green)

> **ID:** `Task-003-F`  
> **Loại:** Feature  
> **SRS:** [`../../srs/SRS_Task003_auth_refresh.md`](../../srs/SRS_Task003_auth_refresh.md)  
> **Phụ thuộc:** `Task-003-U` (contract / red đã merge hoặc cùng PR theo quy ước team)

## Mục tiêu

Triển khai **`POST /api/v1/auth/refresh`**: không Bearer; tra `refresh_tokens` (`delete_ymd` null, `expires_at`); user **Active**; phát **access JWT** mới; `data.refreshToken` **trùng** input (rotation **tắt** theo chốt §7.1 SRS); **`LoginSessionRegistry.register(userId, access)`** sau commit; **không** `INSERT systemlogs` REFRESH.

**Rate limit (chốt §7.2 SRS):** tối đa **1** access mới / **5 phút** / user (hoặc theo key Tech Lead chọn trong ADR — in-memory MVP vs Redis). Dev implement theo ADR Task003.

## File đụng (dự kiến)

- `auth/**` — controller, DTO refresh, `AuthService` (hoặc service refresh), `RefreshTokenRepository` read path  
- `JwtTokenService`, `LoginSessionRegistry`  
- Không migration bắt buộc nếu schema đủ (SRS §6)

## Verify

```text
cd backend/smart-erp && ./mvnw.cmd verify
```

## Definition of Done

- [ ] `mvn verify` xanh; JaCoCo ≥ ngưỡng dự án.  
- [ ] Logout (Task002) với cùng refresh → refresh sau đó **401** khi gọi refresh.  
- [ ] Rate limit §7.2 đúng hành vi đã ADR (nếu ADR hoãn — ghi rõ ngoại lệ Owner).
