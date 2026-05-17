# Registry — Agent `ai_python`

> **Workflow**: [`WORKFLOW_RULE.md`](WORKFLOW_RULE.md) — **chuỗi lean mặc định** (`§0.1`) là điều phối chính cho `/orchestrate`.

## Chuỗi lean (bắt buộc — `/orchestrate`)

| Callsign | Role | Instructions |
| :-- | :-- | :-- |
| `AI_PLANNER` | PRD, option A/B/C, HITL | [`AI_PLANNER_AGENT_INSTRUCTIONS.md`](AI_PLANNER_AGENT_INSTRUCTIONS.md) |
| `AI_BA` | SRS từ PRD | [`AI_BA_AGENT_INSTRUCTIONS.md`](AI_BA_AGENT_INSTRUCTIONS.md) |
| `AI_PM` | Task chain + folder task | [`AI_PM_AGENT_INSTRUCTIONS.md`](AI_PM_AGENT_INSTRUCTIONS.md) |
| `AI_TECH_LEAD` | ADR + NFR | [`AI_TECH_LEAD_AGENT_INSTRUCTIONS.md`](AI_TECH_LEAD_AGENT_INSTRUCTIONS.md) |
| `AI_DEVELOPER` | Code + unit tests + lint/type | [`AI_DEVELOPER_AGENT_INSTRUCTIONS.md`](AI_DEVELOPER_AGENT_INSTRUCTIONS.md) |
| `AI_CODE_REVIEWER` | Review + verdict PASS/BLOCK | [`AI_CODE_REVIEWER_AGENT_INSTRUCTIONS.md`](AI_CODE_REVIEWER_AGENT_INSTRUCTIONS.md) |

## Vai trò mở rộng (ngoài lean — `WORKFLOW_RULE §0.3`)

| Callsign | Role | Instructions |
| :-- | :-- | :-- |
| `AI_BRIDGE` | Contract AI service ↔ BE/FE | [`AI_BRIDGE_AGENT_INSTRUCTIONS.md`](AI_BRIDGE_AGENT_INSTRUCTIONS.md) |
| `AI_TESTER` | Eval / QA — **chạy riêng**, không gắn mỗi `/orchestrate` | [`AI_TESTER_AGENT_INSTRUCTIONS.md`](AI_TESTER_AGENT_INSTRUCTIONS.md) |
| `AI_DOC_SYNC` | Đồng bộ tài liệu | [`AI_DOC_SYNC_AGENT_INSTRUCTIONS.md`](AI_DOC_SYNC_AGENT_INSTRUCTIONS.md) |
| `AI_ORCHESTRATOR` | Audit final task | [`AI_ORCHESTRATOR_AGENT_INSTRUCTIONS.md`](AI_ORCHESTRATOR_AGENT_INSTRUCTIONS.md) |

## Artifact tóm tắt

| Agent | Output chính |
| :-- | :-- |
| AI_PLANNER | `ai_python/docs/prd/PRD_*.md` |
| AI_BA | `ai_python/docs/srs/SRS_AI_*.md` |
| AI_PM | `ai_python/TASKS/Task*.md`, `ai_python/docs/task*/` |
| AI_TECH_LEAD | `ai_python/docs/adr/ADR-*.md` |
| AI_DEVELOPER | code `ai_python/app/**`, tests, coverage |
| AI_CODE_REVIEWER | `ai_python/docs/task*/05-code-review/CODE_REVIEW_*.md` |
