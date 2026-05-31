# Smart ERP Agents

This directory is the home for project-specific agent registry, workflow rules, and skills.

## Invocation

Use [`AGENT_REGISTRY.md`](AGENT_REGISTRY.md) to map a user-called agent name to the correct skill.

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
| [`srs-writer`](skills/srs-writer/SKILL.md) | Write full-stack SRS documents for Smart ERP features, including backend, frontend, database, and AI agentic flows. |
| [`tech-spec-writer`](skills/tech-spec-writer/SKILL.md) | Convert an SRS into an implementation-ready technical specification, architecture decision, and coding handoff. |
| [`qa-spec-writer`](skills/qa-spec-writer/SKILL.md) | Convert a Tech Spec into a test plan, failure-mode matrix, and QA readiness gate before coding. |
| [`coding-agent`](skills/coding-agent/SKILL.md) | Implement code from a Tech Spec or Coding Handoff, then test and report verification. |
| [`code-review-agent`](skills/code-review-agent/SKILL.md) | Review code changes after implementation, prioritizing findings, missing tests, and contract risks. |

## Rules

- Do not edit agent runtime source under `ai_python/`.
- Use skills in `AGENTS/skills/**` as project working instructions, not production code.
- Prefer one focused skill per responsibility.
- Keep SRS documents traceable to code, API docs, routes, Flyway migrations, and AI graph nodes.
- Use [`WORKFLOW_RULE.md`](WORKFLOW_RULE.md) when agents should call each other automatically.
