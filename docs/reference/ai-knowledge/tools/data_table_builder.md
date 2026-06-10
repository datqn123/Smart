# DataTableBuilderTool

> Source: `ai_python/app/graph/tools/data_table_builder.py`
> Prompt: —

## Tổng quan
Xây dựng hiển thị bảng dữ liệu từ kết quả truy vấn. Định dạng rows thành bảng có cấu trúc với tiêu đề và số lượng dòng cho frontend render.

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
Quan sát: `"Đã tạo bảng dữ liệu với N dòng."`

## Tích hợp Runtime

### Harness (v3.0)
- Gọi bởi: `PlanExecutor` qua `ToolRegistry`
- Node type trong PlanGraph: `tool`
- Dùng để hiển thị bảng kết quả truy vấn

### LangGraph (Legacy)
- Node: `emit_query_table`
- Phát bảng có cấu trúc cho frontend

## Xử lý lỗi
- `rows_from_args_or_ref()` trả về lỗi nếu không có rows và không có `result_ref` hợp lệ

## Ví dụ
**Đầu vào:**
```json
{
  "rows": [
    {"product": "A", "quantity": 10},
    {"product": "B", "quantity": 20}
  ],
  "title": "Danh sách sản phẩm"
}
```
**Đầu ra:**
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
Quan sát: `"Đã tạo bảng dữ liệu với 2 dòng."`
