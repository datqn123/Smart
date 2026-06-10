# BuildChartTool

> Source: `ai_python/app/graph/tools/build_chart.py`
> Prompt: —

## Overview
Builds chart specifications from query result rows. Infers chart type (bar, line, pie, etc.) using heuristics and produces a chart spec for frontend rendering.

## Manifest (ToolRegistry)
| Field | Value |
|-------|-------|
| name | `chart_build` |
| capability | `chart_build` |
| side_effect_class | `read_only` |
| has_hitl | `false` |
| risk_level | `low` |
| produces | `("chart",)` |
| consumes | `("rows",)` |
| result_ref_policy | `result_ref` |
| output_artifact_types | `("chart",)` |
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
  "chartType": "bar",
  "title": "Doanh thu theo tháng",
  "data": {...},
  "config": {...}
}
```
Observation: `"Đã tạo biểu đồ {chartType}."`

## Runtime Integration

### Harness (v3.0)
- Called by: `PlanExecutor` via `ToolRegistry`
- Node type in PlanGraph: `tool`
- Used for visualization of query results

### LangGraph (Legacy)
- Node: `agent_chart`
- Produces chart spec from query results

## Error Handling
- `rows_from_args_or_ref()` returns error if no rows and no valid `result_ref`
- Chart type inference via `_infer_chart()` heuristic based on data shape and column types

## Example
**Input:**
```json
{
  "rows": [
    {"month": "Jan", "revenue": 1000},
    {"month": "Feb", "revenue": 1500},
    {"month": "Mar", "revenue": 1200}
  ],
  "title": "Doanh thu quý 1"
}
```
**Output:**
```json
{
  "chartType": "bar",
  "title": "Doanh thu quý 1",
  "data": {
    "labels": ["Jan", "Feb", "Mar"],
    "datasets": [{"label": "revenue", "data": [1000, 1500, 1200]}]
  }
}
```
Observation: `"Đã tạo biểu đồ bar."`
