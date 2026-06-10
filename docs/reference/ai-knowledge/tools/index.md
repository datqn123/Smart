# Agentic Tools Reference

> This directory contains reference documentation for all tools in the ai_python agentic system.

## Tool Summary

| Tool | Capability | Side Effect | HITL | Source | Prompt |
|------|-----------|-------------|------|--------|--------|
| [sql_query](sql_query.md) | data_read | read_only | No | `tools/sql_query.py` | gen_sql.md, sql_review.md, verify_sql_intent.md, analyze_empty_result.md, schema_explore.md |
| [schema_explore](schema_explore.md) | data_read | read_only | No | `tools/schema_explore.py` | schema_explore.md |
| [catalog_draft](catalog_draft.md) | draft_create | non_idempotent_write | Yes | `tools/catalog_draft.py` | catalog_draft.md + 6 entity playbooks |
| [inventory_draft](inventory_draft.md) | draft_create | non_idempotent_write | Yes | `tools/inventory_draft.py` | inventory_draft.md + 4 doc playbooks |
| [answer_composer](answer_composer.md) | answer_compose | read_only | No | `tools/answer_composer.py` | — |
| [build_chart](build_chart.md) | chart_build | read_only | No | `tools/build_chart.py` | — |
| [data_table_builder](data_table_builder.md) | data_table_build | read_only | No | `tools/data_table_builder.py` | — |
| [data_validator](data_validator.md) | data_validate | read_only | No | `tools/data_validator.py` | — |
| [erp_guide](erp_guide.md) | erp_guide | read_only | No | `tools/erp_guide.py` | — |

## Runtime Mapping

### Harness (v3.0)
All 9 tools are registered in `ToolRegistry` and called by `PlanExecutor` via the agentic loop:
- sql_query, schema_explore, catalog_draft, inventory_draft, answer_composer, build_chart, data_table_builder, data_validator, erp_guide

### LangGraph (Legacy)
Tools used in deterministic graph nodes:
- **sql_subgraph**: sql_query (gen_sql, sql_review, validate_sql, execute_sql nodes), schema_explore
- **catalog_draft_subgraph**: catalog_draft
- **inventory_draft_subgraph**: inventory_draft

## Auto-Update Rule

When you change code in `ai_python/`, you MUST update the corresponding tool reference file. See `.opencode/instructions.md` for details.
