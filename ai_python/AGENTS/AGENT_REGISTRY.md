# Registry — `ai_python` agents

> **Workflow**: [`WORKFLOW_RULE.md`](WORKFLOW_RULE.md) — đọc trước khi orchestrate.  
> **Design source**: [`../../Design_Agent/CHAT_AGENT_DESIGN.md`](../../Design_Agent/CHAT_AGENT_DESIGN.md).  
> **Auto-runner**: [`../../.cursor/commands/orchestrate.md`](../../.cursor/commands/orchestrate.md) (slash-command).

## 1. Roles

| Call code | Role | Instructions | Output artifact |
| :--- | :--- | :--- | :--- |
| `AI_PLANNER` | Requirement Analyst & Architect (fullstack PRD) | [`../../AGENTS/AI_PLANNER_AGENT_INSTRUCTIONS.md`](../../AGENTS/AI_PLANNER_AGENT_INSTRUCTIONS.md) | `ai_python/docs/prd/PRD_<slug>.md` |
| `AI_BA` | Business Analyst (SSE events, MCP I/O, eval, HITL) | [`AI_BA_AGENT_INSTRUCTIONS.md`](AI_BA_AGENT_INSTRUCTIONS.md) | `ai_python/docs/srs/SRS_AI_TaskXXX_*.md` |
| `AI_PM` | Project Manager (task chain, DoD, nhãn workflow trong Task) | [`AI_PM_AGENT_INSTRUCTIONS.md`](AI_PM_AGENT_INSTRUCTIONS.md) | `ai_python/TASKS/Task*.md` |
| `AI_TECH_LEAD` | Tech Lead (LangGraph topology + ADR + NFR) | [`AI_TECH_LEAD_AGENT_INSTRUCTIONS.md`](AI_TECH_LEAD_AGENT_INSTRUCTIONS.md) | `ai_python/docs/adr/ADR-*.md` |
| `AI_DEVELOPER` | Developer (LangGraph + tools + MCP + SSE; code + test, gate §5) | [`AI_DEVELOPER_AGENT_INSTRUCTIONS.md`](AI_DEVELOPER_AGENT_INSTRUCTIONS.md) | `ai_python/app/**` + tests |
| `AI_CODE_REVIEWER` | Code Reviewer (coding rule + design conformance) | [`AI_CODE_REVIEWER_AGENT_INSTRUCTIONS.md`](AI_CODE_REVIEWER_AGENT_INSTRUCTIONS.md) | `ai_python/docs/taskXXX/05-code-review/CODE_REVIEW_*.md` |
| `AI_TESTER` | Tester (eval harness 30+ prompts, red-team HITL/MCP) | [`AI_TESTER_AGENT_INSTRUCTIONS.md`](AI_TESTER_AGENT_INSTRUCTIONS.md) | `ai_python/docs/taskXXX/04-tester/` |
| `AI_BRIDGE` | API Bridge (SSE Python ↔ Spring ↔ FE; MCP schema) | [`AI_BRIDGE_AGENT_INSTRUCTIONS.md`](AI_BRIDGE_AGENT_INSTRUCTIONS.md) | `ai_python/docs/api/bridge/BRIDGE_AI_*.md` |
| `AI_DOC_SYNC` | Doc Sync (drift Design ↔ SRS ↔ code ↔ schema) | [`AI_DOC_SYNC_AGENT_INSTRUCTIONS.md`](AI_DOC_SYNC_AGENT_INSTRUCTIONS.md) | `ai_python/docs/sync_reports/SYNC_REPORT_*.md` |
| `AI_ORCHESTRATOR` | Process auditor overlay (per-gate spot-check, fake-gate detection) | [`AI_ORCHESTRATOR_AGENT_INSTRUCTIONS.md`](AI_ORCHESTRATOR_AGENT_INSTRUCTIONS.md) | `ai_python/docs/orchestration/AUDIT_*.md` |
| `AI_BUG_INVESTIGATOR` | RCA ad-hoc (hallucination / HITL bypass / cost / latency / SSE drop) | [`AI_BUG_INVESTIGATOR_AGENT_INSTRUCTIONS.md`](AI_BUG_INVESTIGATOR_AGENT_INSTRUCTIONS.md) | `ai_python/docs/bugs/Bug_AI_*.md` |

## 2. Roles **không** dùng (đã bỏ vs. backend, có lý do)

| Backend role | Lý do bỏ ở `ai_python` |
| :--- | :--- |
| `SQL` | DB do backend sở hữu; AI chỉ gọi MCP `db-readonly` template, schema/RBAC ở backend |
| `CODEBASE_ANALYST` | Greenfield ~2 file Python, brief 10 bước overkill; gộp vào AI_TECH_LEAD task đầu |
| `DEBUG` (Java) | Không áp dụng; AI_BUG_INVESTIGATOR cover RCA Python |

## 3. MCP servers (Design Doc §5.1)

> Mô tả tool I/O nằm ở [`../../Design_Agent/mcp/`](../../Design_Agent/mcp/) (file `*_TOOLS.md`). AGENTS Python tham chiếu, không lặp.

| MCP server | Phase | Doc |
| :--- | :---: | :--- |
| `spring-erp` | 0 | [`../../Design_Agent/mcp/SPRING_ERP_TOOLS.md`](../../Design_Agent/mcp/SPRING_ERP_TOOLS.md) |
| `files-storage` | 0 | [`../../Design_Agent/mcp/FILES_STORAGE_TOOLS.md`](../../Design_Agent/mcp/FILES_STORAGE_TOOLS.md) |
| `vector-rag` | 0 | [`../../Design_Agent/mcp/VECTOR_RAG_TOOLS.md`](../../Design_Agent/mcp/VECTOR_RAG_TOOLS.md) |
| `db-readonly` | 1 | [`../../Design_Agent/mcp/DB_READONLY_TOOLS.md`](../../Design_Agent/mcp/DB_READONLY_TOOLS.md) |
| `google-drive-sheets` | 2 | [`../../Design_Agent/mcp/GOOGLE_DRIVE_SHEETS_TOOLS.md`](../../Design_Agent/mcp/GOOGLE_DRIVE_SHEETS_TOOLS.md) |
| `external-accounting` | 3 | [`../../Design_Agent/mcp/EXTERNAL_ACCOUNTING_TOOLS.md`](../../Design_Agent/mcp/EXTERNAL_ACCOUNTING_TOOLS.md) |

## 4. Context7 (library docs MCP, role-dependent)

- General orchestration: [`WORKFLOW_RULE.md`](WORKFLOW_RULE.md) §7.
- Per-role: AI_DEVELOPER §7, AI_TECH_LEAD §6, AI_TESTER §3.
