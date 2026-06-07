# Skill: SRS Writer

Use this skill when the user asks to create, update, verify, or standardize an SRS for Smart ERP.

The output must fit this project, not a generic SRS template. Smart ERP has three cooperating layers:

- `backend/smart-erp`: Spring Boot API, JWT/RBAC, transaction boundaries, Flyway/PostgreSQL.
- `frontend/mini-erp`: React/Vite UI, route/menu permissions, TanStack Query, user-visible error states.
- `ai_python`: FastAPI AI runtime, current graph/execution stack, and tool integrations that call Spring.

Do not edit source files under `ai_python/` while using this skill unless the user explicitly asks for code changes. For SRS work, read `ai_python` only as evidence.

## Project Evidence To Read

Read only the slices needed for the requested feature, but cover every affected layer.

### CodeGraph First

Before broad manual scanning, use [`../codegraph-context/SKILL.md`](../codegraph-context/SKILL.md).

Required discovery:

```powershell
codegraph status --json
codegraph context "<feature or bug request>" --format json
codegraph query "<domain symbol, route, page, service, table>" --json
```

If status reports pending changes, run `codegraph sync` before relying on results. Use CodeGraph `relatedFiles`, symbols, routes, and relationships as traceability candidates, then read the actual source files before writing requirements.

### Superpowers Alignment

Use [`../superpowers-bridge/SKILL.md`](../superpowers-bridge/SKILL.md) for project-local Superpowers alignment.

For SRS work, apply `superpowers:brainstorming` principles:

- Clarify the user's real goal before freezing requirements.
- Surface viable options and tradeoffs when the requested behavior is ambiguous.
- Ask only blocker questions; otherwise record assumptions and continue.
- Present requirements in readable sections that can be approved or challenged.
- Do not skip the project SRS template or CodeGraph evidence requirements.

### Always Read

- `docs/frontend/mini-erp/features/FEATURES_UI_INDEX.md`
- Related files in `docs/frontend/api/` when an API contract exists.
- Related existing SRS in `docs/backend/srs/`, `docs/frontend/srs/`, or `docs/ai-python/srs/`.
- The relevant controller/service/API route files.
- Relevant Flyway migrations under `backend/smart-erp/src/main/resources/db/migration/`.

### Backend Evidence

Look for:

- `@RequestMapping`, `@GetMapping`, `@PostMapping`, `@PatchMapping`, `@DeleteMapping`
- `SecurityFilterChain`, `@PreAuthorize`, JWT claims, permission checks.
- Service transaction boundaries.
- Repository/JDBC/JPA queries.
- Error envelope/message conventions.

Useful commands:

```powershell
rg -n "@RequestMapping|@GetMapping|@PostMapping|@PatchMapping|@DeleteMapping|SecurityFilterChain|@PreAuthorize" backend/smart-erp/src/main/java
rg -n "CREATE TABLE|ALTER TABLE|CREATE INDEX|roles|permissions" backend/smart-erp/src/main/resources/db/migration
```

### Frontend Evidence

Look for:

- Route in `frontend/mini-erp/src/App.tsx`.
- Menu label and permission in `frontend/mini-erp/src/components/shared/layout/Sidebar.tsx`.
- Feature page, API hook, form validation, and toast/error handling.

Useful commands:

```powershell
rg -n "Route path|label:|perm:|apiJson|useQuery|useMutation|toast" frontend/mini-erp/src
```

### AI Agentic Evidence

Look for:

- FastAPI routes in `ai_python/app/api/routes.py`.
- Runtime state in `ai_python/app/api/runtime.py`.
- AI runtime components in `ai_python/app/graph/` or the current execution stack.
- Execution and policy boundaries in `ai_python/app/harness/` or the current approved runtime layer.
- SQL/tool clients such as `sql_executor`, draft clients, describe clients.

Useful commands:

```powershell
rg -n "APIRouter|@router|compile_agent_graph|add_node|add_edge|ToolCallContext|AgentHarness|SqlExecutor" ai_python/app
```

## Workflow

1. Identify feature scope.
   - Backend only, frontend only, AI only, or full-stack.
   - Record affected routes/endpoints/graph nodes.

2. Perform horizontal analysis.
   - Do not focus only on the immediate request.
   - Search adjacent modules for the same pattern: auth, message mapping, RBAC, envelope, transaction, cache, token relay, SQL guardrails.
   - Record similar scopes and whether they are affected.

3. Resolve source-of-truth conflicts.
   - If API docs, code, Flyway, or UI disagree, write a GAP.
   - Do not silently merge conflicting behavior.
   - Do not invent tables, fields, permissions, or routes.

4. Write Open Questions.
   - Use stable IDs: `OQ-1`, `OQ-2`, ...
   - Mark blocker status.
   - State impact if unanswered.

5. Specify measurable requirements.
   - Functional requirements must have observable behavior.
   - Non-functional requirements must have verification method.
   - Error messages must be user-functional and Vietnamese when client-visible.

6. For AI features, capture architecture ownership from the current approved design.
   - Define runtime flow, state ownership, validation/policy boundary, and tool integration contracts.
   - If an issue exists, classify whether it belongs to runtime flow, validation/policy, tool integration, or contract drift.

7. Add acceptance criteria and test strategy.
   - Include happy path and main failure branches.
   - Include 401/403 when auth is involved.
   - Include AI graph/tool tests when AI is involved.

## Output Location

Choose location by scope:

| Scope | Location |
| :--- | :--- |
| Backend/API primary | `docs/backend/srs/SRS_TaskXXX_<slug>.md` |
| UI-only Mini-ERP | `docs/frontend/srs/SRS_TaskXXX_<slug>.md` |
| AI-only design/docs | `docs/ai-python/srs/SRS_AI_TaskXXX_<slug>.md` |
| Full-stack / cross-layer | Prefer `docs/backend/srs/` if Spring API is the main contract; otherwise use `docs/srs/`. |

Use kebab-case for the slug.

## Required SRS Sections

Use [`templates/SRS_FULLSTACK_AI_TEMPLATE.md`](templates/SRS_FULLSTACK_AI_TEMPLATE.md) as the default.

Minimum sections:

- Title and metadata.
- Input and traceability.
- GAP/source conflict analysis.
- Executive summary.
- Scope.
- Capability breakdown.
- Persona/RBAC.
- Business flow with Mermaid when there are at least two systems.
- Frontend specification when UI is affected.
- Backend HTTP contract when API is affected.
- Business rules.
- Data and SQL when DB is affected.
- AI agentic flow when `ai_python` is affected.
- NFR.
- Test strategy.
- Acceptance criteria.
- Open Questions.
- Risks and rollout.
- PO sign-off.

## Error Message Rules

Client-visible messages must explain the business impact and next action.

Do not expose:

- Stack traces.
- SQL/JDBC/class/package names.
- Raw infrastructure failures.
- URLs/proxy/dev-server details.
- Vendor/provider raw errors.

Preferred examples:

| Case | Message |
| :--- | :--- |
| 401 | `Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.` |
| 403 | `Bạn không có quyền thực hiện thao tác này.` |
| Validation | `Dữ liệu không hợp lệ. Vui lòng kiểm tra lại các trường được đánh dấu.` |
| Conflict | Use a business reason, e.g. `Không thể xóa khách hàng vì vẫn còn đơn hàng đang xử lý.` |
| AI unavailable | `Trợ lý AI tạm thời chưa sẵn sàng. Vui lòng thử lại sau.` |

## Done Criteria

An SRS is done when:

- Every affected layer has evidence or is explicitly marked not applicable.
- Every endpoint/route/node mentioned has a traceable file path.
- RBAC names exact claims/permissions.
- Request/response/error examples are complete enough for FE/BE tests.
- SQL/data impact is tied to real migrations or marked as OQ/GAP.
- AI flow names runtime ownership, validation/policy behavior, tool contracts, and state keys.
- Open questions are explicit and not hidden inside prose.
