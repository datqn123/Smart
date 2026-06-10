# DataValidatorTool

> Source: `ai_python/app/graph/tools/data_validator.py`
> Prompt: —

## Overview
Validates query result data against business rules before write operations. Checks for missing required columns and negative numeric values. Used as a pre-write validation gate.

## Manifest (ToolRegistry)
| Field | Value |
|-------|-------|
| name | `data_validate` |
| capability | `data_validate` |
| side_effect_class | `read_only` |
| has_hitl | `false` |
| risk_level | `low` |
| produces | `("validation",)` |
| consumes | `("rows",)` |
| result_ref_policy | — |
| examples | — |

## Input Schema
```json
{
  "rows": [{"col1": "val1", "col2": "val2"}],
  "required_data": ["col1", "col2"],
  "result_ref": "string"
}
```
Either `rows` or `result_ref` must be provided. `required_data` is a list of column names that must be present.

## Output / Observation
**Pass:**
```json
{
  "ok": true,
  "issues": [],
  "severity": "pass"
}
```
Observation: `"Dữ liệu đạt kiểm tra nghiệp vụ."`

**Fail:**
```json
{
  "ok": false,
  "issues": ["Missing column: price", "Negative value in column: quantity"],
  "severity": "fail"
}
```
Observation: `"Dữ liệu không đạt kiểm tra nghiệp vụ: Missing column: price, Negative value in column: quantity"`

## Runtime Integration

### Harness (v3.0)
- Called by: `PlanExecutor` via `ToolRegistry`
- Node type in PlanGraph: `tool`
- Pre-write validation in plan execution

### LangGraph (Legacy)
- Node: `validate_result`
- Validates data before persist operations

## Error Handling
- Checks missing columns from `required_data`
- Checks negative numeric values in data columns
- `severity="fail"` if any issues found, `severity="pass"` otherwise

## Example
**Input:**
```json
{
  "rows": [
    {"product": "A", "quantity": 10, "price": 1000},
    {"product": "B", "quantity": -5, "price": 2000}
  ],
  "required_data": ["product", "quantity", "price"]
}
```
**Output:**
```json
{
  "ok": false,
  "issues": ["Negative value in column: quantity (row 2)"],
  "severity": "fail"
}
```
Observation: `"Dữ liệu không đạt kiểm tra nghiệp vụ: Negative value in column: quantity (row 2)"`
