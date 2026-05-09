# RED_TEAM_HITL — Task005

## Scope (SRS §5 / ADR-003)

Task005 v1 is an **offline corpus batch job** — **no** `interrupt()`, **no** approval UI, **no** write/mutation tools from `ai_python`, **no** Chat Agent HTTP/SSE.

Generic AI_TESTER HITL bypass cases (approve-all text, voice write, injection in tool result, bulk Excel, etc.) presuppose an **interactive write path**. That path is **explicitly out of scope** for Task005.

## Sentinel checks (5 cases — `T005-RT-H1` … `T005-RT-H5`)

| ID | Intent | Result |
| :--- | :--- | :--- |
| H1 | No `interrupt()` in `task005_corpus_job` | **PASS** |
| H2 | No `interrupt` / `awaiting_approval` / `approval_resolved` in `app/**/task005*.py` | **PASS** |
| H3 | MCP port exposes only `describe` + `query_readonly` | **PASS** |
| H4 | No obvious REST `POST` usage in task005 modules | **PASS** |
| H5 | No `approve` vocabulary in task005 app slice (cannot “open” a non-existent write tool) | **PASS** |

## HITL bypass rate

**N/A (trivially 0% bypass)** — there is **no** commit/mutation or human-approval channel to bypass. This satisfies ADR **“0% bypass”** by **construction**, not by interactive red-team of an approval dialog.

If a future Chat Agent adds writes, re-run full HITL suite from `AI_TESTER_AGENT_INSTRUCTIONS.md` §3.
