# DataValidatorTool

> Source: `ai_python/app/graph/tools/data_validator.py`
> Prompt: —

## Tổng quan
Kiểm tra dữ liệu kết quả truy vấn theo quy tắc nghiệp vụ trước khi ghi. Kiểm tra cột bắt buộc bị thiếu và giá trị âm. Dùng làm cổng kiểm tra trước ghi (pre-write validation gate).

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

## Schema đầu vào
```json
{
  "rows": [{"col1": "val1", "col2": "val2"}],
  "required_data": ["col1", "col2"],
  "result_ref": "string"
}
```
Cần cung cấp `rows` hoặc `result_ref`. `required_data` là danh sách tên cột phải có mặt.

## Đầu ra / Quan sát
**Đạt:**
```json
{
  "ok": true,
  "issues": [],
  "severity": "pass"
}
```
Quan sát: `"Dữ liệu đạt kiểm tra nghiệp vụ."`

**Không đạt:**
```json
{
  "ok": false,
  "issues": ["Missing column: price", "Negative value in column: quantity"],
  "severity": "fail"
}
```
Quan sát: `"Dữ liệu không đạt kiểm tra nghiệp vụ: Missing column: price, Negative value in column: quantity"`

## Tích hợp Runtime

### Harness (v3.0)
- Gọi bởi: `PlanExecutor` qua `ToolRegistry`
- Node type trong PlanGraph: `tool`
- Kiểm tra trước ghi trong plan execution

### LangGraph (Legacy)
- Node: `validate_result`
- Kiểm tra dữ liệu trước khi persist

## Xử lý lỗi
- Kiểm tra cột thiếu từ `required_data`
- Kiểm tra giá trị âm trong cột số liệu
- `severity="fail"` nếu có lỗi, `severity="pass"` nếu không

## Ví dụ
**Đầu vào:**
```json
{
  "rows": [
    {"product": "A", "quantity": 10, "price": 1000},
    {"product": "B", "quantity": -5, "price": 2000}
  ],
  "required_data": ["product", "quantity", "price"]
}
```
**Đầu ra:**
```json
{
  "ok": false,
  "issues": ["Negative value in column: quantity (row 2)"],
  "severity": "fail"
}
```
Quan sát: `"Dữ liệu không đạt kiểm tra nghiệp vụ: Negative value in column: quantity (row 2)"`
