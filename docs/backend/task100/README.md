# Task100 — Phiên HashMap / access JWT hết hạn (SRS-only)

**SRS (Approved):** [`../srs/SRS_Task100_auth-session-registry-stale-access.md`](../srs/SRS_Task100_auth-session-registry-stale-access.md)  
**Không có** `API_Task100` — index **100** theo quy ước nghiệp vụ không map endpoint.

Thư mục con theo [`WORKFLOW_RULE.md`](../../AGENTS/WORKFLOW_RULE.md): PM → Tech Lead → Developer → Tester → Codebase Analyst → Doc Sync.

| Thứ tự | Agent | Thư mục | Artifact |
| :---: | :--- | :--- | :--- |
| 0 | BA | [`../srs/SRS_Task100_auth-session-registry-stale-access.md`](../srs/SRS_Task100_auth-session-registry-stale-access.md) | SRS |
| 1 | PM | [`01-pm/`](01-pm/) | `Task100_unit.md`, `Task100_feature.md`, `Task100_e2e.md` |
| 2 | Tech Lead | [`02-tech-lead/`](02-tech-lead/) | `ADR-Task100-session-map-stale-jwt.md` |
| 3 | Developer | [`03-developer/`](03-developer/) | `HANDOFF_Task100.md` |
| 4 | Tester | [`04-tester/`](04-tester/) | `TEST_PLAN_Task100.md`, `MANUAL_UNIT_TEST_Task100.md` |
| 5 | Codebase Analyst | [`05-codebase-analyst/`](05-codebase-analyst/) | `TASK100_BRIEF.md` |
| 6 | Doc Sync | [`06-doc-sync/`](06-doc-sync/) | `SYNC_CHECKLIST_Task100.md` |

## Gate PM (G-PM)

Chuỗi task + artifact merge **`develop`** trước khi coi Dev xong (theo `PM_AGENT_INSTRUCTIONS.md`).
