# SqlQueryTool

> Source: `ai_python/app/graph/tools/sql_query.py`
> Prompts: gen_sql.md, sql_review.md, verify_sql_intent.md, analyze_empty_result.md, schema_explore.md

## Overview
Executes SQL queries against the database with self-correction capabilities. Handles schema exploration, SQL generation, validation, execution, and result analysis with retry budgets.

## Manifest (ToolRegistry)
| Field | Value |
|-------|-------|
| name | `sql_query` |
| capability | `data_read` |
| side_effect_class | `read_only` |
| has_hitl | `false` |
| risk_level | `low` |
| produces | `("rows",)` |
| consumes | — |
| result_ref_policy | `result_ref` |
| examples | — |

## Input Schema
```json
{
  "query": "string"
}
```

## Output / Observation
```json
{
  "query_result": {
    "rows": [
      {"col1": "val1", "col2": "val2"}
    ]
  },
  "generated_sql": "SELECT ..."
}
```
Observation: `"SQL rows: [first 5 rows JSON] ... N rows total"`

## Runtime Integration

### Harness (v3.0)
- Called by: `PlanExecutor` via `ToolRegistry`
- Node type in PlanGraph: `tool`
- Uses `SelfCorrectingSqlRunner` with retry budgets for automatic error correction

### LangGraph (Legacy)
- Subgraph: `sql_subgraph`
- Nodes: `schema_explore`, `gen_sql`, `verify_sql_intent`, `sql_review`, `validate_sql`, `execute_sql`, `analyze_empty_result`, `validate_result`, `chart_readiness`
- Executes SQL with multi-stage validation and correction loop

## Error Handling
- **Self-correction loop**: gen_sql → sql_review → execute_sql with retry budget
- **Duplicate failure detection**: Prevents infinite loops on repeated errors
- **Empty result analysis**: Triggers `analyze_empty_result` prompt when query returns no rows
- **Role-based column masking**: Filters sensitive columns based on user role
- **sanitize_user_data**: Escapes and validates user input to prevent SQL injection

## Example
**Input:**
```json
{
  "query": "Show me top 10 products by revenue this month"
}
```
**Output:**
```json
{
  "query_result": {
    "rows": [
      {"product_name": "Product A", "revenue": 1500000},
      {"product_name": "Product B", "revenue": 1200000}
    ]
  },
  "generated_sql": "SELECT product_name, SUM(revenue) as revenue FROM sales WHERE month = CURRENT_MONTH GROUP BY product_name ORDER BY revenue DESC LIMIT 10"
}
```
Observation: `"SQL rows: [{\"product_name\": \"Product A\", \"revenue\": 1500000}, ...] ... 10 rows total"`
