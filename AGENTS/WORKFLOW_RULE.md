# Smart ERP Agent Workflow Rule

Use this workflow when the user wants agents to call each other or invokes `Agent AUTO`, `AUTO_RUN`, `chạy tự động`, or `tự làm hết workflow`.

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

Enter automatic mode when the user says any of:

- `Agent AUTO`
- `AUTO_RUN`
- `chạy tự động`
- `tự làm hết workflow`
- `các Agent tự gọi nhau`
- an equivalent instruction that the workflow should continue without separate agent calls

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

## Safety Boundaries

- Do not edit `ai_python` runtime for workflow documentation tasks.
- For AI agentic coding tasks, keep LangGraph as orchestrator, Harness as executor/validation boundary, and tools as scoped integrations.
- For any error or bug, perform horizontal analysis across similar scopes before choosing the fix.
- Do not broaden implementation beyond the active handoff unless it is necessary to keep contracts consistent.
