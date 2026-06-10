# SchemaExploreTool

> Source: `ai_python/app/graph/tools/schema_explore.py`
> Prompt: schema_explore.md

## Overview
Discovers and retrieves database schema information for a given topic. Produces a schema plan or runtime schema artifact used by downstream SQL generation.

## Manifest (ToolRegistry)
| Field | Value |
|-------|-------|
| name | `schema_explore` |
| capability | `data_read` |
| side_effect_class | `read_only` |
| has_hitl | `false` |
| risk_level | `low` |
| produces | `("schema",)` |
| consumes | — |
| result_ref_policy | — |
| examples | — |

## Input Schema
```json
{
  "topic": "string"
}
```

## Output / Observation
**Schema plan mode:**
```json
{
  "schema_plan": {
    "tables": ["table_a", "table_b"],
    "columns": {"table_a": ["col1", "col2"]}
  }
}
```
Observation: `"Schema plan: {JSON truncated to 800 chars}"`

**Runtime artifact mode:**
```json
{
  "runtime_schema_artifact": {
    "tables": {...},
    "relationships": {...}
  }
}
```
Observation: `"Schema artifact loaded."`

## Runtime Integration

### Harness (v3.0)
- Called by: `PlanExecutor` via `ToolRegistry`
- Node type in PlanGraph: `tool`
- Used for schema discovery before SQL generation

### LangGraph (Legacy)
- Subgraph: `sql_subgraph`
- Nodes: `schema_explore`
- First node in the SQL pipeline, provides schema context

## Error Handling
- Delegates to `make_schema_explore_node`
- Success check: `ok = not bool(error_payload)`
- Returns error payload if schema discovery fails

## Example
**Input:**
```json
{
  "topic": "customer orders"
}
```
**Output:**
```json
{
  "schema_plan": {
    "tables": ["customers", "orders", "order_items"],
    "columns": {
      "customers": ["customer_id", "customer_name", "email"],
      "orders": ["order_id", "customer_id", "order_date", "total"],
      "order_items": ["item_id", "order_id", "product_id", "quantity"]
    }
  }
}
```
Observation: `"Schema plan: {\"tables\": [\"customers\", \"orders\", \"order_items\"], ...}"`
