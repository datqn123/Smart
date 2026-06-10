# Developer — Handoff Task100

**SRS:** [`../../srs/SRS_Task100_auth-session-registry-stale-access.md`](../../srs/SRS_Task100_auth-session-registry-stale-access.md)  
**ADR:** [`../02-tech-lead/ADR-Task100-session-map-stale-jwt.md`](../02-tech-lead/ADR-Task100-session-map-stale-jwt.md)

## Checklist

1. [x] `JwtTokenService`: `tryParseActiveAccessClaims` + `isAccessTokenActiveForSessionMap` + `parseAccessTokenUserId` dùng chung.  
2. [x] `LoginSessionRegistry`: inject `JwtTokenService`; prune stale (`remove` CAS) trước 403.  
3. [x] `mvn verify`.
