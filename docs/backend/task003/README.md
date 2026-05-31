# Task003 — Làm mới access token (`POST /auth/refresh`)

**SRS (Approved):** [`../srs/SRS_Task003_auth_refresh.md`](../srs/SRS_Task003_auth_refresh.md)  
**API:** [`../../../frontend/docs/api/API_Task003_auth_refresh.md`](../../../frontend/docs/api/API_Task003_auth_refresh.md)

**Điểm vào workflow:** SRS đã **Approved** → theo [`WORKFLOW_RULE.md`](../../AGENTS/WORKFLOW_RULE.md) **§0**, **PM** là bước đầu thực thi (G-BA coi đã đạt). Chuỗi đầy đủ sau PM:

`PM → Tech Lead → Developer → Tester → Codebase Analyst → Doc Sync`

| Thứ tự | Agent | Thư mục | Artifact (dự kiến) |
| :---: | :--- | :--- | :--- |
| — | *(BA đã xong gate)* | [`../srs/`](../srs/) | `SRS_Task003_auth_refresh.md` |
| 1 | PM | [`01-pm/`](01-pm/) | `Task003_unit.md`, `Task003_feature.md`, `Task003_e2e.md` |
| 2 | Tech Lead | `02-tech-lead/` | ADR (refresh, rate limit §7.2 SRS nếu áp dụng) |
| 3 | Developer | `03-developer/` | `HANDOFF_Task003.md` |
| 4 | Tester | `04-tester/` | `TEST_PLAN_Task003.md`, `MANUAL_UNIT_TEST_Task003.md`; Postman `Task003_*.json` |
| 5 | Codebase Analyst | `05-codebase-analyst/` | `TASK003_BRIEF.md` |
| 6 | Doc Sync | `06-doc-sync/` | `SYNC_CHECKLIST_Task003.md` |

## Gate PM (G-PM)

Theo `PM_AGENT_INSTRUCTIONS.md`: chuỗi task trong `01-pm/` phải **có trên nhánh `develop`** trước khi Developer bắt đầu.
