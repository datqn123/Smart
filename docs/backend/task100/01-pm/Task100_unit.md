# Task100 — Unit (manual / Dev regression)

> **ID:** `Task-100-U`  
> **SRS:** [`../../srs/SRS_Task100_auth-session-registry-stale-access.md`](../../srs/SRS_Task100_auth-session-registry-stale-access.md)

## Mục tiêu

Xác nhận prune map: entry JWT **hết hạn** không còn chặn `POST /api/v1/auth/login`.

## Artifact

[`../04-tester/MANUAL_UNIT_TEST_Task100.md`](../04-tester/MANUAL_UNIT_TEST_Task100.md)

## Definition of Done

- [ ] Case “chờ hết hạn access rồi login lại” Pass (manual).
