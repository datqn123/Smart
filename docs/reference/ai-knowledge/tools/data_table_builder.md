# DataTableBuilderTool

> Source: `ai_python/app/graph/tools/data_table_builder.py`
> Prompt: —

## Overview
Builds tabular data display from query result rows. Formats rows into a structured table with title and row count for frontend rendering.

## Manifest (ToolRegistry)
| Field | Value |
|-------|-------|
| name | `data_table_build` |
| capability | `data_table_build` |
| side_effect_class | `read_only` |
| has_hitl | `false` |
| risk_level | `low` |
| produces | `("data_table",)` |
| consumes | `("rows", "result_ref")` |
| result_ref_policy | `result_ref` |
| output_artifact_types | `("data_table",)` |
| examples | — |

## Input Schema
```json
{
  "rows": [{"col1": "val1", "col2": "val2"}],
  "result_ref": "string",
  "title": "string"
}
```
Either `rows` or `result_ref` must be provided. `title` is optional.

## Output / Observation
```json
{
  "query_table_sse": {
    "title": "Kết quả truy vấn",
    "rows": [
      {"col1": "val1", "col2": "val2"}
    ],
    "row_count": 10
  },
  "row_count": 10
}
```
Observation: `"Đã tạo bảng dữ liệu với N dòng."`

## Runtime Integration

### Harness (v3.0)
- Called by: `PlanExecutor` via `ToolRegistry`
- Node type in PlanGraph: `tool`
- Used for tabular display of query results

### LangGraph (Legacy)
- Node: `emit_query_table`
- Emits structured table for frontend

## Error Handling
- `rows_from_args_or_ref()` returns error if no rows and no valid `result_ref`

## Example
**Input:**
```json
{
  "rows": [
    {"product": "A", "quantity": 10},
    {"product": "B", "quantity": 20}
  ],
  "title": "Danh sách sản phẩm"
}
```
**Output:**
```json
{
  "query_table_sse": {
    "title": "Danh sách sản phẩm",
    "rows": [
      {"product": "A", "quantity": 10},
      {"product": "B", "quantity": 20}
    ],
    "row_count": 2
  },
  "row_count": 2
}
```
Observation: `"Đã tạo bảng dữ liệu với 2 dòng."`
