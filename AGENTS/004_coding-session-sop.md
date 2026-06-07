# SOP — One Coding Session

Use this checklist for every code-affecting Smart ERP task.

1. Classify the request with [`AGENT_REGISTRY.md`](AGENT_REGISTRY.md): raw requirement starts at `SRS_WRITER`; direct implementation starts at `CODING_AGENT` only when a clear scope or handoff exists.
2. Load [`WORKFLOW_RULE.md`](WORKFLOW_RULE.md) and confirm whether the task is automatic workflow, manual stage, or explicitly bypassed by the user.
3. Run CodeGraph preflight before broad scanning: status, sync if needed, then context/query/impact for the active stage.
4. Read the relevant source of truth directly: SRS, Tech Spec, QA Spec, API docs, route/page, controller/service, migration, and AI graph files when in scope.
5. Perform horizontal analysis before editing: search adjacent modules for the same auth, RBAC, envelope, UI state, SQL, or AI tool pattern.
6. Implement the smallest behavior-complete slice that satisfies the active handoff; keep unrelated refactors and user changes untouched.
7. Preserve architecture boundaries documented by the active handoff; Spring enforces auth/RBAC and transactions, and Mini-ERP owns UI/cache/messages.
8. Add or update focused tests for the changed contract, including happy path, main failure path, and regression case that caused the bug or feature request.
9. Run verification from narrow to broad: targeted tests first, frontend build or backend compile when contracts changed, and AI pytest when `ai_python` runtime changed.
10. Report the handoff: changed files, verification commands/results, CodeGraph operations used or fallback, residual risks, and whether `CODE_REVIEW_AGENT` should run next.

## Quick Agent Map

| Need | Agent |
| :--- | :--- |
| Clarify requirement / business behavior | `SRS_WRITER` |
| Convert approved SRS to implementation plan | `TECH_SPEC_WRITER` |
| Design regression and acceptance tests | `QA_SPEC_WRITER` |
| Change production code/tests/config | `CODING_AGENT` |
| Review completed diff | `CODE_REVIEW_AGENT` |

## Stop Conditions

- Blocker PO decision remains unresolved.
- The change can cause data loss, security exposure, or unclear user-visible behavior without an accepted risk.
- Required credentials, services, or dependencies are unavailable and no safe fallback exists.
- The task crosses into `ai_python` runtime without an explicit AI coding scope.
