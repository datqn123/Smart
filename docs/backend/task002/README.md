# Task002 — Đăng xuất (`POST /auth/logout`)

**SRS (BA, Approved):** [`../srs/SRS_Task002_logout.md`](../srs/SRS_Task002_logout.md)  
**API:** [`../../../frontend/docs/api/API_Task002_logout.md`](../../../frontend/docs/api/API_Task002_logout.md)

Thư mục con **theo thứ tự** [`WORKFLOW_RULE.md`](../../AGENTS/WORKFLOW_RULE.md): PM → Tech Lead → Developer → Tester → Codebase Analyst → Doc Sync.

| Thứ tự | Agent | Thư mục | Artifact |
| :---: | :--- | :--- | :--- |
| 0 | BA | [`00-ba/`](00-ba/) + [`../srs/`](../srs/) | `SRS_Task002_logout.md` (nguồn chân lý) |
| 1 | PM | [`01-pm/`](01-pm/) | `Task002_unit.md`, `Task002_feature.md`, `Task002_e2e.md` |
| 2 | Tech Lead | [`02-tech-lead/`](02-tech-lead/) | `ADR-Task002-logout-soft-revoke-session.md` |
| 3 | Developer | [`03-developer/`](03-developer/) | `HANDOFF_Task002.md` |
| 4 | Tester | [`04-tester/`](04-tester/) | `TEST_PLAN_Task002.md`, **`MANUAL_UNIT_TEST_Task002.md`** (test tay); Postman `smart-erp/docs/postman/Task002_*.json` |
| 5 | Codebase Analyst | [`05-codebase-analyst/`](05-codebase-analyst/) | `TASK002_BRIEF.md` |
| 6 | Doc Sync | [`06-doc-sync/`](06-doc-sync/) | `SYNC_CHECKLIST_Task002.md` |

## Gate PM (G-PM)

Theo `PM_AGENT_INSTRUCTIONS.md`: chuỗi task phải **có trên nhánh `develop`** trước khi Dev bắt đầu. Owner/PM thực hiện merge/commit sau khi review file trong `01-pm/`.
