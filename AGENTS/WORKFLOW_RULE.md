# Smart ERP Agent Workflow Rule

Use this workflow for every implementation request in this repository.

This workflow is mandatory when the user asks to write, modify, implement, fix, refactor, wire, migrate, configure, or test production code. Treat those requests as `AUTO_RUN` even when the user does not type an agent name.

The workflow is also used when the user explicitly invokes `Agent AUTO`, `AUTO_RUN`, `chạy tự động`, or `tự làm hết workflow`.

## Default Chain

```text
Raw request
  -> SRS_WRITER
  -> TECH_SPEC_WRITER
  -> QA_SPEC_WRITER
  -> CODING_AGENT
  -> CODE_REVIEW_AGENT
```

## Stage Rules

### 1. SRS_WRITER

Use when the input is a feature idea, bug description, business requirement, or unclear task.

Required output:

- SRS document.
- Scope and affected layers.
- Open questions.
- Acceptance criteria.

Next step:

- If blocker questions remain, stop and ask for the minimum needed decision.
- If the user says `continue`, `approve`, or invokes `Agent AUTO`, run `TECH_SPEC_WRITER`.

### 2. TECH_SPEC_WRITER

Use when an SRS exists and coding should not start until architecture, contracts, and handoff are clear.

Required output:

- Tech Spec or ADR decision.
- Coding Handoff.
- Horizontal analysis.
- Readiness: `READY_FOR_CODING`, `READY_WITH_RISKS`, or `BLOCKED`.

Next step:

- `READY_FOR_CODING`: run `QA_SPEC_WRITER` when the user invokes `Agent AUTO`, `Agent QA_SPEC_WRITER`, or explicitly says to continue.
- `READY_WITH_RISKS`: ask for acceptance only if the risk can cause rework, data loss, security exposure, or unclear UX.
- `BLOCKED`: stop and list blocker decisions.

### 3. QA_SPEC_WRITER

Use when a Tech Spec or Coding Handoff exists and tests should be designed before code is written.

Required output:

- QA Spec / Test Plan.
- Horizontal QA analysis.
- P0/P1 test matrix.
- Failure-mode coverage.
- Readiness: `QA_READY_FOR_CODING`, `QA_READY_WITH_RISKS`, or `QA_BLOCKED`.

Next step:

- `QA_READY_FOR_CODING`: run `CODING_AGENT` when the user invokes `Agent AUTO`, `Agent CODING_AGENT`, or explicitly says to continue.
- `QA_READY_WITH_RISKS`: ask for acceptance only if the risk can cause rework, data loss, security exposure, or unclear UX.
- `QA_BLOCKED`: stop and list blocker decisions.

### 4. CODING_AGENT

Use when a Tech Spec or Coding Handoff exists, or when the user directly asks to implement a scoped task.

Required output:

- Code changes.
- Tests or verification.
- Summary of files changed.
- Remaining risks if tests could not be run.

Next step:

- If the user invoked `Agent AUTO` or explicitly asked agents to call each other, run `CODE_REVIEW_AGENT`.
- Otherwise, report result and wait for review invocation.

### 5. CODE_REVIEW_AGENT

Use after Coding Agent changes code or when the user asks for a review.

Required output:

- Findings ordered by severity.
- Contract review.
- Test gap review.
- Horizontal analysis.
- Status: `REVIEW_PASS`, `REVIEW_PASS_WITH_RISKS`, or `REVIEW_BLOCKED`.

Next step:

- Stop and report result.

## Auto-Call Behavior

### Automatic Mode Trigger

Enter automatic mode when the user asks for any code-affecting work:

- implement a feature
- fix a bug
- refactor code
- add or update tests
- add or update migrations
- change runtime config
- wire frontend/backend/API/AI behavior
- modify production source files

Also enter automatic mode when the user says any of:

- `Agent AUTO`
- `AUTO_RUN`
- `chạy tự động`
- `tự làm hết workflow`
- `các Agent tự gọi nhau`
- an equivalent instruction that the workflow should continue without separate agent calls

### Explicit Bypass

The workflow can be bypassed only when the user explicitly says one of:

- `bỏ qua workflow`
- `skip workflow`
- `chỉ sửa nhanh không tạo tài liệu`

If bypassed, state that the user explicitly requested the bypass and still preserve core safety rules.

### Automatic Mode Loop

When automatic mode is active and an agent finishes:

1. Read the handoff from the completed stage.
2. Determine the next stage from the default chain.
3. Load the next stage's `SKILL.md`.
4. Execute the next stage immediately.
5. Repeat until blocked or final review is complete.

### Manual Mode

When automatic mode is not active:

- Report the handoff after each stage.
- Wait for the next agent invocation unless the user explicitly says to continue.

### Stop Conditions

Stop automatic mode when:

- A stage returns `BLOCKED`, `QA_BLOCKED`, or `REVIEW_BLOCKED`.
- A stage has an unresolved risk that can cause rework, data loss, security exposure, or unclear UX.
- Owner approval is explicitly required by the SRS, Tech Spec, or QA Spec.
- Required credentials, environment, dependencies, or external services are unavailable and no safe fallback exists.
- `CODE_REVIEW_AGENT` completes.

When stopping, report the current stage, reason, last artifact path, and the exact decision or action needed next.

## CodeGraph Discovery Rule

Before a workflow stage performs broad manual scanning or makes scope, impact, test, coding, or review decisions:

1. Load `AGENTS/skills/codegraph-context/SKILL.md`.
2. Check CodeGraph freshness with MCP status or `codegraph status --json`.
3. If `pendingChanges` is non-zero, run `codegraph sync` and re-check status.
4. Use CodeGraph to guide discovery:
   - SRS: `context` and `query`.
   - Tech Spec: `impact`, `callers`, and `callees`.
   - QA Spec: `affected` and `context`.
   - Coding: `context`, `query`, `impact`, then `affected` for tests.
   - Code Review: `impact`, `callers`, `callees`, and `affected`.
5. Verify CodeGraph results by reading the relevant source files directly.

If CodeGraph is unavailable, continue with `rg`, direct file reads, and project docs; record the fallback in the handoff or final response when relevant.

### Visible CodeGraph Preflight

For every code-affecting prompt:

1. The first user-facing progress update must say `CodeGraph preflight` and name the intended CodeGraph operation for the active stage.
2. The first tool batch must run CodeGraph MCP or CLI fallback before broad manual scanning with `rg`, `Get-Content`, `ls`, or file reads.
3. If CodeGraph cannot run, say `CodeGraph unavailable` and name the fallback before manual scanning.
4. The final response must include a concise `CodeGraph:` line with the actual operation used.
5. If a transcript shows only manual file reads/searches and no CodeGraph preflight, treat that run as workflow non-compliance and restart discovery with CodeGraph before continuing.

## Safety Boundaries

- Do not edit `ai_python` runtime for workflow documentation tasks.
- For AI agentic coding tasks, keep LangGraph as orchestrator, Harness as executor/validation boundary, and tools as scoped integrations.
- For any error or bug, perform horizontal analysis across similar scopes before choosing the fix.
- Do not broaden implementation beyond the active handoff unless it is necessary to keep contracts consistent.

## Documentation Naming Rule

Before creating any new documentation file under `docs/**` or `AGENTS/**`:

1. Choose the exact destination folder.
2. Count only files directly inside that folder, non-recursive.
3. Set the new sequence number to `count + 1`.
4. Name the file `<NNN>_<descriptive-slug>.md` by default.
5. Preserve a different numeric width only when the destination folder already consistently uses that width.

Never derive the next number from sibling folders, parent folders, another task folder, global task ids, or files with similar names elsewhere.
