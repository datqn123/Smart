# Smart ERP Agents

This directory is the home for project-specific agent registry, workflow rules, and skills.

## Invocation

Use [`AGENT_REGISTRY.md`](AGENT_REGISTRY.md) to map a user-called agent name to the correct skill.

For a compact per-session checklist, use [`004_coding-session-sop.md`](004_coding-session-sop.md).

For any implementation request, the workflow is mandatory even if the user does not type an agent name. Code changes automatically use:

```text
SRS_WRITER -> TECH_SPEC_WRITER -> QA_SPEC_WRITER -> CODING_AGENT -> CODE_REVIEW_AGENT
```

Examples:

- `Agent SRS_WRITER, viết SRS cho Task123 ...`
- `Agent TECH_SPEC_WRITER, tạo handoff coding từ SRS_Task123 ...`
- `Agent QA_SPEC_WRITER, tạo test plan từ handoff Task123 ...`
- `Agent CODING_AGENT, implement theo handoff Task123 ...`
- `Agent CODE_REVIEW_AGENT, review diff Task123 ...`
- `Agent AUTO, chạy workflow tiếp theo cho Task123 ...`

## Current Skills

| Skill | Purpose |
| :--- | :--- |
| [`codegraph-context`](skills/codegraph-context/SKILL.md) | Use CodeGraph MCP or CLI fallback for code discovery, impact analysis, affected tests, and review scope. |
| [`superpowers-bridge`](skills/superpowers-bridge/SKILL.md) | Align installed Superpowers skills with the project agent workflow without replacing the mandatory chain. |
| [`srs-writer`](skills/srs-writer/SKILL.md) | Write full-stack SRS documents for Smart ERP features, including backend, frontend, database, and AI agentic flows. |
| [`tech-spec-writer`](skills/tech-spec-writer/SKILL.md) | Convert an SRS into an implementation-ready technical specification, architecture decision, and coding handoff. |
| [`qa-spec-writer`](skills/qa-spec-writer/SKILL.md) | Convert a Tech Spec into a test plan, failure-mode matrix, and QA readiness gate before coding. |
| [`coding-agent`](skills/coding-agent/SKILL.md) | Implement code from a Tech Spec or Coding Handoff, then test and report verification. |
| [`code-review-agent`](skills/code-review-agent/SKILL.md) | Review code changes after implementation, prioritizing findings, missing tests, and contract risks. |

## Rules

- All production code, tests, migrations, runtime config, API behavior, UI behavior, and AI runtime changes must run through [`WORKFLOW_RULE.md`](WORKFLOW_RULE.md).
- Only bypass the workflow when the user explicitly says `bỏ qua workflow`, `skip workflow`, or `chỉ sửa nhanh không tạo tài liệu`.
- New documentation files under `docs/**` or `AGENTS/**` must be numbered by counting files in the exact destination folder, non-recursively, then using `<NNN>_<descriptive-slug>.md`.
- Do not continue doc numbering from sibling folders, parent folders, other task folders, or similarly named files elsewhere.
- Workflow stages must use [`codegraph-context`](skills/codegraph-context/SKILL.md) before broad manual scanning, then verify findings by reading source files.
- Workflow stages must use [`superpowers-bridge`](skills/superpowers-bridge/SKILL.md) to align installed Superpowers skills with the active project agent stage.
- CodeGraph usage must be visible: first progress update says `CodeGraph preflight`, first tool batch runs CodeGraph or declares fallback, and final response includes a `CodeGraph:` line.
- Superpowers usage must be visible for code/workflow tasks: final response includes a `Superpowers:` line naming the skills or principles applied.
- Do not edit agent runtime source under `ai_python/`.
- Use skills in `AGENTS/skills/**` as project working instructions, not production code.
- Prefer one focused skill per responsibility.
- Keep SRS documents traceable to code, API docs, routes, Flyway migrations, and AI graph nodes.
- Use [`WORKFLOW_RULE.md`](WORKFLOW_RULE.md) when agents should call each other automatically.
