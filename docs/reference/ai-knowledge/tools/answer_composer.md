# AnswerComposerTool

> Source: `ai_python/app/graph/tools/answer_composer.py`
> Prompt: —

## Tổng quan
Soạn câu trả lời markdown tiếng Việt từ observations và kết quả truy vấn. Logic Python thuần, không gọi LLM — định dạng row, metrics, giả định, và câu hỏi gợi ý.

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

## Schema đầu vào
```json
{
  "observations": "list",
  "assumptions": ["string"]
}
```

## Đầu ra / Quan sát
```json
{
  "answer_markdown": "## Kết quả\n\n| # | Cột 1 | Cột 2 |\n|---|-------|-------|\n| 1 | val1  | val2  |\n\n**Giả định:** ...\n\n**Câu hỏi tiếp theo:** ...",
  "assumptions": ["Giả định 1"],
  "follow_ups": ["Câu hỏi gợi ý 1"]
}
```
Quan sát: Câu trả lời markdown tiếng Việt với row đánh số, metrics, giả định, gợi ý.

## Tích hợp Runtime

### Harness (v3.0)
- Gọi bởi: `PlanExecutor` qua `ToolRegistry`
- Node type trong PlanGraph: `tool`
- Dùng bởi `_compose_plan_answer()` để tạo câu trả lời cuối cùng

### LangGraph (Legacy)
- Node: `summarize_answer`
- Node cuối cùng trong answer pipeline

## Xử lý lỗi
- Luôn trả về `ok=True`
- Rows rỗng → trả lời "không có dữ liệu"

## Ví dụ
**Đầu vào:**
```json
{
  "observations": [
    {"rows": [{"product": "A", "revenue": 1000}, {"product": "B", "revenue": 2000}]}
  ],
  "assumptions": ["Doanh thu tính theo tháng hiện tại"]
}
```
**Đầu ra:**
```json
{
  "answer_markdown": "## Kết quả truy vấn\n\n| # | product | revenue |\n|---|---------|----------|\n| 1 | A       | 1,000    |\n| 2 | B       | 2,000    |\n\n**Giả định:** Doanh thu tính theo tháng hiện tại",
  "assumptions": ["Doanh thu tính theo tháng hiện tại"],
  "follow_ups": ["Bạn muốn xem chi tiết theo ngày không?"]
}
```
