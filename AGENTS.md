# Project Agent Invocation Rules

## Mandatory Coding Workflow

All implementation work in this repository must run through the agent workflow.

If the user asks to write, modify, implement, fix, refactor, wire, migrate, configure, or test production code, automatically treat the request as `AUTO_RUN` even when the user does not type an agent name.

Mandatory chain:

```text
SRS_WRITER -> TECH_SPEC_WRITER -> QA_SPEC_WRITER -> CODING_AGENT -> CODE_REVIEW_AGENT
```

Start at the first missing artifact:

- No SRS or requirement artifact: start with `SRS_WRITER`.
- SRS exists but no Tech Spec / Coding Handoff: start with `TECH_SPEC_WRITER`.
- Tech Spec exists but no QA Spec: start with `QA_SPEC_WRITER`.
- QA Spec exists and code is not implemented: start with `CODING_AGENT`.
- Code is implemented but not reviewed: start with `CODE_REVIEW_AGENT`.

Do not bypass this workflow for code changes unless the user explicitly says `bỏ qua workflow`, `skip workflow`, or `chỉ sửa nhanh không tạo tài liệu`. If bypassing, state that the user explicitly requested the bypass.

## Mandatory Docs File Naming

When creating any new documentation file under `docs/**` or `AGENTS/**`, assign its sequence number from the target folder itself.

Required process:

1. Identify the exact destination folder first.
2. Count only files directly inside that folder, non-recursive.
3. New sequence number = current file count + 1.
4. Do not continue numbering from sibling folders, parent folders, other task folders, or similarly named files elsewhere.
5. Use a folder-local numeric prefix for new workflow docs: `<NNN>_<descriptive-slug>.md`.
6. Use 3 digits by default (`001`, `002`, `003`). If that folder already consistently uses another numeric width, preserve the folder's width.

Example:

```text
docs/backend/task123/02-tech-lead/
  existing files: 3
  next new doc: 004_<slug>.md
```

When the user calls an agent by name, follow `AGENTS/AGENT_REGISTRY.md` and execute that agent's workflow immediately.

## Mandatory CodeGraph Discovery

Before any workflow stage performs broad manual scanning or makes scope, impact, test, coding, or review decisions, it must use CodeGraph when available.

Required process:

1. Load `AGENTS/skills/codegraph-context/SKILL.md`.
2. Prefer CodeGraph MCP tools if present in the session.
3. If MCP tools are unavailable, use CLI fallback such as `codegraph status --json`, `codegraph context`, `codegraph query`, `codegraph impact`, and `codegraph affected`.
4. If `codegraph status --json` reports pending changes, run `codegraph sync` before relying on CodeGraph results.
5. Use CodeGraph to guide discovery only; still read source files directly before writing requirements, plans, code, tests, or review findings.

Visible enforcement:

- The first progress update for any code-affecting prompt must mention `CodeGraph preflight`.
- The first tool batch must include CodeGraph MCP or CLI fallback before `rg`, `Get-Content`, or broad manual file reads.
- If CodeGraph is unavailable, the agent must say so before manual scanning and name the fallback path.
- Final responses for workflow/code tasks must include a short `CodeGraph:` line that states what ran, for example `status + context`, `status + impact + affected`, or `unavailable, used rg fallback`.
- A workflow/code task that only shows `rg`, `Get-Content`, or direct file reads without a CodeGraph preflight is non-compliant unless the user explicitly bypassed CodeGraph.

## Mandatory Superpowers Alignment

Installed Superpowers skills are a methodology layer for the project agents. They do not replace the mandatory project workflow.

For any code-affecting prompt:

1. Run the mandatory CodeGraph preflight first.
2. Load `AGENTS/skills/superpowers-bridge/SKILL.md`.
3. Apply the relevant Superpowers skill principles for the active stage.
4. Continue through the project agent chain unless explicitly bypassed by the user.

Stage alignment:

- `SRS_WRITER`: use brainstorming principles for requirements discovery and owner decisions.
- `TECH_SPEC_WRITER`: use writing-plans principles for exact, bite-sized, testable implementation slices.
- `QA_SPEC_WRITER`: use test-driven-development principles to define expected failing tests before coding.
- `CODING_AGENT`: use systematic-debugging for bugs, test-driven-development for behavior changes, and executing-plans or subagent-driven-development for implementation.
- `CODE_REVIEW_AGENT`: use requesting-code-review, receiving-code-review, and verification-before-completion principles.

Visible enforcement:

- Final responses for workflow/code tasks must include a short `Superpowers:` line, for example `brainstorming + writing-plans` or `TDD + verification-before-completion`.
- If the installed Superpowers tool or skill is unavailable, continue with the project-local bridge and state the fallback.
- Do not create `CLAUDE.md` unless the user explicitly asks for it.
- Do not let Superpowers default doc locations override the project documentation naming rule.

When the user says `Agent AUTO`, `AUTO_RUN`, `chạy tự động`, `tự làm hết workflow`, or any equivalent request, run the full workflow in automatic mode:

```text
SRS_WRITER -> TECH_SPEC_WRITER -> QA_SPEC_WRITER -> CODING_AGENT -> CODE_REVIEW_AGENT
```

When the user says `AUTO_DOCS`, `chỉ soạn docs`, `soạn tài liệu`, `auto run soạn docs`, or `chạy tự động soạn tài liệu`, run docs-only mode (stop before coding):

```text
SRS_WRITER -> TECH_SPEC_WRITER -> QA_SPEC_WRITER  [STOP]
```

When the user says `AUTO_CODE`, `chỉ code`, `triển khai code`, `auto run triển khai`, or `chạy tự động triển khai code`, read existing docs then run code-only mode:

```text
[read QA Spec + Tech Spec + SRS] -> CODING_AGENT -> CODE_REVIEW_AGENT  [STOP]
```

In automatic mode, do not wait for the user to call each next agent. Continue to the next stage until a blocker, required owner decision, unsafe risk, or final review result is reached.

Examples:

- `Agent SRS_WRITER, viết SRS cho Task123 ...`
- `Agent TECH_SPEC_WRITER, tạo handoff coding từ SRS_Task123 ...`
- `Agent QA_SPEC_WRITER, tạo test plan từ handoff Task123 ...`
- `Agent CODING_AGENT, implement theo handoff Task123 ...`
- `Agent CODE_REVIEW_AGENT, review diff Task123 ...`
- `Agent AUTO, chạy từ SRS đến coding cho Task123 ...`
- `AUTO_RUN, làm hết workflow cho Task123 ...`
- `AUTO_DOCS, soạn tài liệu cho Task123 ...`
- `AUTO_CODE, triển khai code theo docs Task123 ...`

Project rules:

- Any production code, test, migration, or config change must enter automatic workflow mode unless explicitly bypassed by the user.
- Any new docs file must use folder-local counting for its numeric prefix.
- Any workflow stage must use CodeGraph discovery when available, then verify results by reading source files.
- Do not edit agent runtime source under `ai_python/` unless the active agent scope explicitly requires production AI code changes.
- Project working agents live under `AGENTS/skills/**`.
- Use `AGENTS/WORKFLOW_RULE.md` for handoff and auto-call behavior.
