---
name: superpowers-bridge
description: Use when project agents need to align Smart ERP workflow stages with installed Superpowers skills without changing the project agent chain
---

# Skill: Superpowers Bridge

Use this skill as the project-local adapter between installed Superpowers skills and the Smart ERP agent workflow.

This bridge does not replace the project chain:

```text
SRS_WRITER -> TECH_SPEC_WRITER -> QA_SPEC_WRITER -> CODING_AGENT -> CODE_REVIEW_AGENT
```

It adds Superpowers discipline to each stage while preserving the project rules in `AGENTS.md` and `AGENTS/WORKFLOW_RULE.md`.

## Priority

Follow instructions in this order:

1. Direct user instructions.
2. Root `AGENTS.md` and `AGENTS/WORKFLOW_RULE.md`.
3. Project skills under `AGENTS/skills/**`.
4. Installed Superpowers skills.
5. Default assistant behavior.

If Superpowers and the project workflow conflict, keep the project workflow and use the Superpowers principle only where it fits.

## Required Preflight Order

For code-affecting work:

1. Announce `CodeGraph preflight` in the first progress update.
2. Run CodeGraph MCP or CLI fallback in the first tool batch.
3. Check relevant Superpowers skills before deciding how to execute the stage.
4. Run the active project workflow stage.

Do not use Superpowers as a reason to skip CodeGraph, skip project artifacts, or bypass `AUTO_RUN`.

## Stage Mapping

| Project stage | Superpowers alignment |
| :--- | :--- |
| `SRS_WRITER` | Use `superpowers:brainstorming` principles to clarify intent, options, constraints, and owner decisions before freezing requirements. |
| `TECH_SPEC_WRITER` | Use `superpowers:writing-plans` principles to make implementation slices exact, testable, small, and free of placeholders. |
| `QA_SPEC_WRITER` | Use `superpowers:test-driven-development` principles to define tests before implementation and to name expected failing cases. |
| `CODING_AGENT` | Use `superpowers:systematic-debugging` for bugs, `superpowers:test-driven-development` for behavior changes, and `superpowers:executing-plans` or `superpowers:subagent-driven-development` for plan execution. |
| `CODE_REVIEW_AGENT` | Use `superpowers:requesting-code-review`, `superpowers:receiving-code-review`, and `superpowers:verification-before-completion` principles for evidence-based review. |

## Coding Execution Rule

When production code changes are required:

- If a Tech Spec, QA Spec, and implementation plan already exist, execute task-by-task.
- If independent task execution tools are available, prefer subagent-driven development.
- If subagent tools are unavailable, execute inline using the same checkpoints.
- For features, bugfixes, refactors, and behavior changes, write or identify the failing test before implementation unless the task is pure documentation, generated code, or configuration-only.
- For bugs or failed tests, investigate root cause and horizontal impact before proposing a fix.
- Before claiming completion, run fresh verification or clearly state what could not be verified.

## Boundaries

- Do not edit production agent runtime under `ai_python/` unless the active scope explicitly requires AI runtime code changes.
- Do not create `CLAUDE.md` for this project unless the user explicitly asks for it.
- Do not let Superpowers default plan locations override the project documentation naming rule.
- Do not auto-merge, delete worktrees, or discard changes without explicit user approval.

## Output Expectations

Each project stage should mention the Superpowers alignment it used in its artifact or final response when relevant.

For code/workflow tasks, final responses must still include:

```text
CodeGraph: <actual operation used>
Superpowers: <skills or principles applied>
```
