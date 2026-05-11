# CODE_REVIEW — Task007 (iteration 1)

**Verdict:** PASS

**Inputs:** `TASKS/Task007.md`, `docs/srs/SRS_AI_Task007_agent-sql-factory-upgrade.md`, `docs/adr/ADR-006-agent-sql-factory-upgrade.md`

## Summary

- SQL-Factory–lite building blocks added under `ai_python/app/graph/`: `sql_prompts.py`, `sql_table_selection.py`, `sql_similarity.py`; `gen_sql` / `validate_sql` wired with **feature flags default off** for Task006 parity.
- `AgentState`, `TableMeta.description`, and `GraphSettings` extended per Option B; no Spring/FE edits.
- Unit coverage in `tests/test_task007_sql_factory.py`; existing `tests/test_graph.py` and `tests/test_agents.py` pass (38 tests in combined run after `pip install -r requirements.txt`).

## Findings

- **Low:** SimEmb / separate `select_tables` graph node / HTTP description merge job are **deferred** (explicitly optional in PRD Option B); only hooks and `TableMeta.description` field are in place.

## SRS / ADR alignment

- Meets Option B: heuristic-first selection, optional structured `sql_table_pick` via registry fallback to `default`, explore/exploit prompts, local hybrid similarity pool, enriched schema behind `SQL_ENRICHED_SCHEMA_PROMPT`.
- Subgraph order unchanged; `sql_separate_select_tables_node` reserved only.

## Verdict rationale

No blocking issues; tests green; scope contained to `ai_python/`.
