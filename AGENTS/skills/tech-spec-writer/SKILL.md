# Skill: Tech Spec Writer

Use this skill when the user already has an SRS and needs the next agent before coding. This agent turns an approved or draft SRS into an implementation-ready technical specification and coding handoff for Smart ERP.

This skill is intentionally separate from the agent runtime under `ai_python/`. Do not edit source files under `ai_python/` while using this skill unless the user explicitly asks for production code changes. Read `ai_python` only as evidence when an AI agentic feature is in scope.

## Role

Act as the Solution Architect / Tech Lead Agent between SRS Writer and Coding Agent.

Primary output:

- Architecture decision or technical specification.
- Concrete coding handoff with files to read, files likely to edit, contracts, guardrails, tests, and open questions.
- A readiness decision: `READY_FOR_CODING`, `READY_WITH_RISKS`, or `BLOCKED`.

## Inputs

Start from one or more of:

- SRS under `docs/backend/srs/`, `docs/frontend/srs/`, `docs/ai-python/srs/`, or `docs/srs/`.
- Existing API docs under `docs/frontend/api/`.
- Existing task folders under `docs/backend/task*/`, `docs/frontend/`, or `docs/ai-python/task*/`.
- Relevant source files from `backend/smart-erp`, `frontend/mini-erp`, and, when applicable, `ai_python`.

If the SRS path is not provided, search for likely SRS files by task id or feature slug.

Useful commands:

```powershell
rg -n "TaskXXX|<feature slug>|Acceptance Criteria|Open Questions" docs
rg -n "@RequestMapping|@GetMapping|@PostMapping|@PatchMapping|@DeleteMapping|@PreAuthorize" backend/smart-erp/src/main/java
rg -n "Route path|useQuery|useMutation|apiJson|toast|permission|perm:" frontend/mini-erp/src
rg -n "compile_agent_graph|add_node|add_edge|AgentHarness|ToolCallContext|SqlExecutor|APIRouter" ai_python/app
```

## Workflow

1. Confirm scope from the SRS.
   - Backend, frontend, database, AI agentic flow, or cross-layer.
   - Record every affected endpoint, UI route, table, graph node, Harness boundary, and tool integration.

2. Perform horizontal analysis.
   - Search adjacent modules for the same implementation pattern.
   - Look for repeated risk areas: auth/RBAC, envelope shape, validation, transaction handling, pagination, cache invalidation, SSE, retry policy, SQL safety, tenant scope, correlation id, and error masking.
   - Root-cause design issues instead of only solving the immediate request.

3. Resolve architecture boundaries.
   - Backend owns business rules, persistence, transactions, and RBAC enforcement.
   - Frontend owns interaction, form state, cache behavior, visible error states, and route/menu permission display.
   - LangGraph owns orchestration, state transitions, routing, retry, and iterative logic.
   - Harness owns deterministic execution, validation, policy enforcement, auditability, and security guardrails.
   - Tools are scoped integrations only; they must not own orchestration or bypass Harness.

4. Convert SRS requirements into implementation slices.
   - Slice by user-observable capability, not by vague technical layer.
   - For each slice, name exact files likely to change and tests likely to add.
   - Define data contracts before implementation details.

5. Decide if an ADR is required.
   - Required when package/module boundaries, transaction strategy, concurrency, permission model, AI orchestration, Harness policy, tool contract, database shape, or cross-layer contract changes.
   - Not required for a small implementation that follows an existing local pattern exactly; document the reused pattern instead.

6. Produce coding handoff.
   - Use `templates/TECH_SPEC_CODING_HANDOFF_TEMPLATE.md`.
   - Keep it specific enough that a Coding Agent can implement without re-reading the whole SRS.
   - Do not hide blockers in prose; list them as `OQ-*` or `GAP-*`.

7. Set readiness.
   - `READY_FOR_CODING`: contracts, files, tests, and open questions are clear; no blocker.
   - `READY_WITH_RISKS`: coding can start, but risks or non-blocking questions must be tracked.
   - `BLOCKED`: missing decision would cause rework or unsafe implementation.

## AI Agentic Requirements

When the feature touches AI chat, SQL agent, charting, draft generation, STT/TTS, or any LangGraph/Harness/tool flow:

- Keep LangGraph, Harness, and tools separated in the design.
- Define state keys and ownership.
- Define Harness validation rules before tool invocation.
- Define retry and fallback limits.
- Define how bearer token, tenant id, role/permission, locale, and correlation id move through the system.
- Classify every AI-related risk as one of:
  - Logic flow / orchestration flaw.
  - Execution guardrail flaw.
  - Improper tool integration.
  - Contract drift between layers.

## Output Location

Choose the task folder that matches the SRS scope.

| Scope | Preferred output |
| :--- | :--- |
| Backend/API primary | `docs/backend/taskXXX/02-tech-lead/TECH_SPEC_TaskXXX_<slug>.md` |
| Frontend primary | `docs/frontend/tech_lead/TECH_SPEC_TaskXXX_<slug>.md` |
| AI-only docs/design | `docs/ai-python/taskXXX/02-tech-lead/TECH_SPEC_TaskXXX_<slug>.md` |
| Cross-layer feature | Prefer the folder owned by the main contract, then link to affected docs. |

If an ADR is needed, place it near the existing ADR convention for that scope:

- Backend: `docs/backend/taskXXX/02-tech-lead/ADR-TaskXXX-<slug>.md`
- Frontend: `docs/frontend/adr/ADR-XXXX_<slug>.md`
- AI docs: `docs/ai-python/adr/ADR-XXX-<slug>.md`

## Done Criteria

The Tech Spec is done when:

- It points to the SRS and all important evidence files.
- Scope boundaries are explicit.
- All contracts are concrete enough for code and tests.
- Files to read/edit are listed.
- Test plan includes unit, integration, UI, and AI graph/Harness/tool cases when applicable.
- Horizontal analysis has been performed and documented.
- Open questions and gaps are traceable.
- Readiness is declared.

