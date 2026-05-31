# Smart ERP Agent Registry

This registry maps user-invoked agent names to project skills and handoff behavior.

## Invocation Rule

When the user message contains `Agent <name>` or clearly calls one of the aliases below, activate the matching agent and perform the work. Do not only describe what the agent would do.

If the user calls `Agent AUTO`, `AUTO_RUN`, `chạy tự động`, `tự làm hết workflow`, or equivalent, enter automatic mode and choose the first missing stage in the workflow:

1. `SRS_WRITER`
2. `TECH_SPEC_WRITER`
3. `QA_SPEC_WRITER`
4. `CODING_AGENT`
5. `CODE_REVIEW_AGENT`

In automatic mode, do not wait for the user to call each next agent. Stop only when a stage is blocked, requires owner approval, has an unsafe unresolved risk, or reaches the final `CODE_REVIEW_AGENT` result.

## Registry

| Agent | Aliases | Skill / instructions | Primary output | Auto next |
| :--- | :--- | :--- | :--- | :--- |
| `SRS_WRITER` | `BA`, `SRS`, `BA_AGENT` | `AGENTS/skills/srs-writer/SKILL.md` | SRS document | `TECH_SPEC_WRITER` after approval or explicit continue |
| `TECH_SPEC_WRITER` | `TECH_SPEC`, `TECH_LEAD`, `SOLUTION_ARCHITECT`, `ARCHITECT_AGENT` | `AGENTS/skills/tech-spec-writer/SKILL.md` | Tech Spec, ADR decision, Coding Handoff | `QA_SPEC_WRITER` when readiness is `READY_FOR_CODING` or user explicitly accepts risk |
| `QA_SPEC_WRITER` | `QA`, `TESTER`, `TEST_DESIGN_AGENT`, `QA_AGENT` | `AGENTS/skills/qa-spec-writer/SKILL.md` | Test plan, failure modes, QA readiness | `CODING_AGENT` when readiness is `QA_READY_FOR_CODING` or user explicitly accepts risk |
| `CODING_AGENT` | `DEV`, `DEVELOPER`, `CODE_AGENT`, `CODER` | `AGENTS/skills/coding-agent/SKILL.md` | Code changes, tests, verification summary | `CODE_REVIEW_AGENT` after implementation and verification |
| `CODE_REVIEW_AGENT` | `REVIEWER`, `CR`, `CODE_REVIEW`, `REVIEW_AGENT` | `AGENTS/skills/code-review-agent/SKILL.md` | Review findings, test gaps, residual risks | Stop and report result |
| `AUTO` | `AUTO_AGENT`, `AUTO_RUN`, `ORCHESTRATE`, `RUN_WORKFLOW`, `chạy tự động`, `tự làm hết workflow` | `AGENTS/WORKFLOW_RULE.md` | Runs all unblocked stages in order | Depends on current stage |

## Resolution Rules

- Prefer exact agent names over aliases.
- If two aliases could match, choose the stage that matches the artifact the user provided.
- If the user provides raw feature requirements, start with `SRS_WRITER`.
- If the user provides an SRS path, start with `TECH_SPEC_WRITER`.
- If the user provides a Tech Spec or Coding Handoff path, start with `QA_SPEC_WRITER` unless they explicitly request coding.
- If the user provides a QA Spec or asks to implement, start with `CODING_AGENT`.
- If the user asks for review or provides a completed diff, start with `CODE_REVIEW_AGENT`.
- If the requested scope touches AI runtime, read `ai_python` as evidence but do not edit it unless the active coding task explicitly includes production AI code.

## Handoff Contract

Each agent must leave a clear handoff marker:

| From | Required handoff |
| :--- | :--- |
| `SRS_WRITER` | SRS path, scope, open questions, approval state |
| `TECH_SPEC_WRITER` | Tech Spec path, readiness, files to read/edit, test plan |
| `QA_SPEC_WRITER` | QA Spec path, readiness, P0 tests, failure-mode coverage |
| `CODING_AGENT` | Changed files, verification commands, remaining risks |
| `CODE_REVIEW_AGENT` | Findings, review status, residual risks |
