# ErpGuideTool

> Source: `ai_python/app/graph/tools/erp_guide.py`
> Prompt: —

## Overview
Provides Vietnamese ERP guidance text based on topic keyword matching. Simple routing logic with no LLM call — returns pre-defined guidance for inventory, finance, or generic topics.

## Manifest (ToolRegistry)
| Field | Value |
|-------|-------|
| name | `erp_guide` |
| capability | `erp_guide` |
| side_effect_class | `read_only` |
| has_hitl | `false` |
| risk_level | `low` |
| produces | `("guidance",)` |
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
```json
{
  "topic": "inventory",
  "guide": "Hướng dẫn quản lý kho: Nhập kho, xuất kho, kiểm kê..."
}
```
Observation: Vietnamese ERP guidance text (keyword-matched: inventory/kho, finance/doanh thu, or generic).

## Runtime Integration

### Harness (v3.0)
- Called by: `PlanExecutor` via `ToolRegistry`
- Node type in PlanGraph: `tool`
- Knowledge retrieval for ERP guidance

### LangGraph (Legacy)
- Not used in legacy graph

## Error Handling
- Always returns `ok=True`
- Simple keyword routing — no error scenarios

## Example
**Input:**
```json
{
  "topic": "kho"
}
```
**Output:**
```json
{
  "topic": "inventory",
  "guide": "Hướng dẫn quản lý kho: Nhập kho, xuất kho, kiểm kê, điều chuyển kho. Các chứng từ cần thiết: phiếu nhập kho, phiếu xuất kho, biên bản kiểm kê."
}
```
Observation: `"Hướng dẫn quản lý kho: Nhập kho, xuất kho, kiểm kê..."`
