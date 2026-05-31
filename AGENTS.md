# Project Agent Invocation Rules

When the user calls an agent by name, follow `AGENTS/AGENT_REGISTRY.md` and execute that agent's workflow immediately.

When the user says `Agent AUTO`, `AUTO_RUN`, `chạy tự động`, `tự làm hết workflow`, or any equivalent request, run the full workflow in automatic mode:

```text
SRS_WRITER -> TECH_SPEC_WRITER -> QA_SPEC_WRITER -> CODING_AGENT -> CODE_REVIEW_AGENT
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

Project rules:

- Do not edit agent runtime source under `ai_python/` unless the active agent scope explicitly requires production AI code changes.
- Project working agents live under `AGENTS/skills/**`.
- Use `AGENTS/WORKFLOW_RULE.md` for handoff and auto-call behavior.
- Preserve the separation of LangGraph, Harness, and tools for AI agentic work.
