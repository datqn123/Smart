# Smart ERP Agent Skills

This directory is the new home for project-specific agent skills.

## Current Skills

| Skill | Purpose |
| :--- | :--- |
| [`srs-writer`](skills/srs-writer/SKILL.md) | Write full-stack SRS documents for Smart ERP features, including backend, frontend, database, and AI agentic flows. |

## Rules

- Do not edit agent runtime source under `ai_python/`.
- Use skills in `AGENTS/skills/**` as project working instructions, not production code.
- Prefer one focused skill per responsibility.
- Keep SRS documents traceable to code, API docs, routes, Flyway migrations, and AI graph nodes.

