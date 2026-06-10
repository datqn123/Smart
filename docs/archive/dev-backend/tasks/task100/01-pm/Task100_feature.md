# Task100 — Feature

> **ID:** `Task-100-F`  
> **Phụ thuộc:** `Task-100-U` (manual xác nhận hành vi mong muốn)  
> **SRS:** [`../../srs/SRS_Task100_auth-session-registry-stale-access.md`](../../srs/SRS_Task100_auth-session-registry-stale-access.md)

## Mục tiêu

`LoginSessionRegistry.assertNoConcurrentSession` gỡ entry **stale** (JWT không còn hiệu lực) trước khi 403; dùng `JwtTokenService` cùng secret/iss/aud.

## File đụng

- `auth/session/LoginSessionRegistry.java`
- `auth/support/JwtTokenService.java`

## Verify

```text
cd backend/smart-erp && .\mvnw.cmd -q verify
```

## Definition of Done

- [ ] `mvn verify` xanh; logic khớp SRS §5.
