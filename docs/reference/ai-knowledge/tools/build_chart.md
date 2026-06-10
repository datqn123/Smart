# BuildChartTool

> Source: `ai_python/app/graph/tools/build_chart.py`
> Prompt: —

## Tổng quan
Xây dựng spec biểu đồ từ kết quả truy vấn. Suy luận loại biểu đồ (bar, line, pie, v.v.) bằng heuristic và tạo chart spec cho frontend render.

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

## Schema đầu vào
```json
{
  "rows": [{"col1": "val1", "col2": "val2"}],
  "result_ref": "string",
  "title": "string"
}
```
Cần cung cấp `rows` hoặc `result_ref`. `title` không bắt buộc.

## Đầu ra / Quan sát
```json
{
  "chartType": "bar",
  "title": "Doanh thu theo tháng",
  "data": {...},
  "config": {...}
}
```
Quan sát: `"Đã tạo biểu đồ {chartType}."`

## Tích hợp Runtime

### Harness (v3.0)
- Gọi bởi: `PlanExecutor` qua `ToolRegistry`
- Node type trong PlanGraph: `tool`
- Dùng để trực quan hóa kết quả truy vấn

### LangGraph (Legacy)
- Node: `agent_chart`
- Tạo chart spec từ kết quả truy vấn

## Xử lý lỗi
- `rows_from_args_or_ref()` trả về lỗi nếu không có rows và không có `result_ref` hợp lệ
- Suy luận loại biểu đồ qua `_infer_chart()` heuristic dựa trên hình dạng dữ liệu và kiểu cột

## Ví dụ
**Đầu vào:**
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
**Đầu ra:**
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
Quan sát: `"Đã tạo biểu đồ bar."`
