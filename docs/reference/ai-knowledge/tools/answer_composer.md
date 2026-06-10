# AnswerComposerTool

> Source: `ai_python/app/graph/tools/answer_composer.py`
> Prompt: —

## Overview
Composes final Vietnamese markdown answers from observations and query results. Pure Python logic with no LLM call — formats rows, metrics, assumptions, and follow-up suggestions.

## Manifest (ToolRegistry)
| Field | Value |
|-------|-------|
| name | `answer_compose` |
| capability | `answer_compose` |
| side_effect_class | `read_only` |
| has_hitl | `false` |
| risk_level | `low` |
| produces | `("answer",)` |
| consumes | `("observations", "rows")` |
| result_ref_policy | — |
| output_artifact_types | `("answer",)` |
| examples | — |

## Input Schema
```json
{
  "observations": "list",
  "assumptions": ["string"]
}
```

## Output / Observation
```json
{
  "answer_markdown": "## Kết quả\n\n| # | Cột 1 | Cột 2 |\n|---|-------|-------|\n| 1 | val1  | val2  |\n\n**Giả định:** ...\n\n**Câu hỏi tiếp theo:** ...",
  "assumptions": ["Giả định 1"],
  "follow_ups": ["Câu hỏi gợi ý 1"]
}
```
Observation: Vietnamese markdown answer with numbered rows, metrics, assumptions, follow-ups.

## Runtime Integration

### Harness (v3.0)
- Called by: `PlanExecutor` via `ToolRegistry`
- Node type in PlanGraph: `tool`
- Used by `_compose_plan_answer()` for final answer generation

### LangGraph (Legacy)
- Node: `summarize_answer`
- Final node in the answer pipeline

## Error Handling
- Always returns `ok=True`
- Empty rows → canned "no data" response

## Example
**Input:**
```json
{
  "observations": [
    {"rows": [{"product": "A", "revenue": 1000}, {"product": "B", "revenue": 2000}]}
  ],
  "assumptions": ["Doanh thu tính theo tháng hiện tại"]
}
```
**Output:**
```json
{
  "answer_markdown": "## Kết quả truy vấn\n\n| # | product | revenue |\n|---|---------|----------|\n| 1 | A       | 1,000    |\n| 2 | B       | 2,000    |\n\n**Giả định:** Doanh thu tính theo tháng hiện tại",
  "assumptions": ["Doanh thu tính theo tháng hiện tại"],
  "follow_ups": ["Bạn muốn xem chi tiết theo ngày không?"]
}
```
