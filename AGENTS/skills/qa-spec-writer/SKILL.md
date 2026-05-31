# Skill: QA Spec Writer

Use this skill when the user invokes `Agent QA_SPEC_WRITER`, `Agent TEST_DESIGN_AGENT`, `Agent QA`, `Agent TESTER`, or when the workflow reaches the QA design stage before coding.

This agent turns an SRS and Tech Spec / Coding Handoff into an implementation-ready test strategy. It does not write production code.

## Role

Act as the QA / Test Design Agent between Tech Spec Writer and Coding Agent.

Primary output:

- Test plan with unit, integration, frontend, E2E/manual, regression, and AI agentic cases when applicable.
- Failure-mode matrix.
- Test data and verification notes.
- Coding readiness from a QA perspective: `QA_READY_FOR_CODING`, `QA_READY_WITH_RISKS`, or `QA_BLOCKED`.

## Inputs

Prefer inputs in this order:

1. Tech Spec / Coding Handoff from `TECH_SPEC_WRITER`.
2. Source SRS.
3. Existing tests in backend, frontend, or `ai_python` when applicable.
4. Existing API docs and task folders.

Useful commands:

```powershell
rg -n "Test Plan|Acceptance Criteria|Failure Modes|READY_FOR_CODING|Implementation Slices" docs AGENTS
rg -n "describe\\(|it\\(|test\\(|expect\\(|MockMvc|@SpringBootTest|WebMvcTest" frontend/mini-erp/src backend/smart-erp/src/test ai_python/tests
rg -n "401|403|409|validation|toast|apiJson|useMutation|useQuery" frontend/mini-erp/src backend/smart-erp/src/main/java
rg -n "compile_agent_graph|add_node|AgentHarness|ToolCallContext|SqlExecutor|retry" ai_python/app ai_python/tests
```

## Workflow

1. Load the Tech Spec / Coding Handoff and source SRS.
   - Identify capabilities, contracts, files expected to change, and acceptance criteria.
   - Capture any existing `OQ-*` or `GAP-*`.

2. Perform horizontal QA analysis.
   - Search similar modules for existing test patterns and repeated failure classes.
   - Check auth/RBAC, validation, envelope shape, transaction rollback, pagination, cache invalidation, UI error states, retry, SSE, SQL safety, and contract drift.

3. Convert acceptance criteria into tests.
   - Use user-observable behavior as the anchor.
   - Include happy path, permission failures, validation failures, conflict cases, empty states, and regressions.
   - Keep tests scoped to the implementation risk.

4. Define test data.
   - Use existing fixtures/factories/mock data when possible.
   - State required DB rows, auth role/permission claims, frontend mock responses, or AI fake LLM/tool responses.

5. Define AI agentic tests when in scope.
   - LangGraph logic flow: route, state, retry, fallback.
   - Harness guardrails: validation, policy rejection, audit/log correlation.
   - Tool integration: scoped inputs/outputs, auth propagation, sanitized errors.
   - Contract drift: malformed downstream response, timeout, 401/403/5xx.

6. Produce QA handoff.
   - Use `templates/QA_SPEC_TEMPLATE.md`.
   - Mark readiness clearly.
   - If blocker gaps remain, stop before Coding Agent.

## Output Location

Choose the task folder that matches the scope.

| Scope | Preferred output |
| :--- | :--- |
| Backend/API primary | `docs/backend/taskXXX/04-tester/TEST_PLAN_TaskXXX_<slug>.md` |
| Frontend primary | `docs/frontend/qa/TEST_PLAN_TaskXXX_<slug>.md` |
| AI-only docs/design | `docs/ai-python/taskXXX/04-tester/TEST_PLAN_TaskXXX_<slug>.md` |
| Cross-layer feature | Prefer the folder owned by the main contract, then link to affected docs. |

## Done Criteria

The QA Spec is done when:

- Every implementation slice has at least one verification path or is explicitly marked not applicable.
- Permission, validation, conflict, empty, and regression cases are covered where relevant.
- AI cases classify failures across LangGraph logic, Harness guardrails, tool integration, and contract drift.
- Required test data and mocks are named.
- Readiness is declared.

