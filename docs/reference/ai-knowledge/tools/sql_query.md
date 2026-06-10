# SqlQueryTool

> Source: `ai_python/app/graph/tools/sql_query.py`
> Prompt: gen_sql.md

## Tổng quan
Thực thi truy vấn SQL read-only, không có retry loop trong code — LLM tự quản lý retry qua conversation history. Tool load schema từ Postgres, gọi LLM sinh SQL (dùng gen_sql.md skill), kiểm tra safety, execute, mask cột nhạy cảm, trả về rows.

## Manifest (ToolRegistry)
| Field | Value |
|-------|-------|
| name | `sql_query` |
| capability | `data_read` |
| side_effect_class | `read_only` |
| has_hitl | `false` |
| risk_level | `low` |
| produces | `("rows",)` |
| consumes | — |
| result_ref_policy | `result_ref` |
| when_to_use | Cần dữ liệu thực tế từ ERP: số liệu, danh sách, dòng, aggregate từ database |
| when_not_to_use | Chỉ muốn xem schema/cấu trúc (dùng schema_explore) hoặc chỉ muốn tạo bản ghi |
| examples | `doanh thu tháng này`, `liệt kê sản phẩm sắp hết hàng` |

## Schema đầu vào
```json
{
  "question": "string"
}
```

## Đầu ra / Quan sát
```json
{
  "rows": [
    {"col1": "val1", "col2": "val2"}
  ],
  "generated_sql": "SELECT ...",
  "explanation": "Giải thích ngắn về query"
}
```
Quan sát: `"SQL trả về N dòng"` nếu có dữ liệu, `"Không có dữ liệu (0 dòng)"` nếu rỗng.

**SSE payload** (khi có rows): `{"_event": "data_table", "rows": [...]}`

## Tích hợp Runtime

### Harness (v3.0)
- Gọi bởi: `PlanExecutor` qua `ToolRegistry`
- Node type trong PlanGraph: `tool`
- Tool không tự retry — LLM đọc kết quả (error/empty/data) và quyết định retry qua conversation, max 3 lần tổng cộng tất cả các phase

### LangGraph (Legacy)
- Không còn subgraph riêng — sql_subgraph đã bị xóa trong đợt đơn giản hóa
- Tool được gọi trực tiếp từ `chat_normal` node

## Xử lý lỗi
- **Retry LLM-driven**: LLM quản lý retry qua skill gen_sql.md (3 loại: SQL error, empty result, data validation fail, max 3 lần tổng)
- **Che cột nhạy cảm theo role**: `CapabilityMatrix.mask_columns()` lọc `cost_price`, `margin`, `debt_balance`... cho non-owner khi `agentic_capability_guard_enabled = true`
- **SQL safety check**: `enforce_read_only_sql()` chặn DDL/DML trước khi execute
- **Schema load failure**: Trả về ToolResult với `ok=False` và error message

## Ví dụ
**Đầu vào:**
```json
{
  "question": "doanh thu tháng này theo sản phẩm"
}
```
**Đầu ra:**
```json
{
  "rows": [
    {"product_name": "Sản phẩm A", "revenue": 1500000},
    {"product_name": "Sản phẩm B", "revenue": 1200000}
  ],
  "generated_sql": "SELECT product_name, SUM(revenue) as revenue FROM sales WHERE month = CURRENT_MONTH GROUP BY product_name ORDER BY revenue DESC LIMIT 10",
  "explanation": "Truy vấn tổng doanh thu theo sản phẩm trong tháng hiện tại"
}
```
Quan sát: `"SQL trả về 2 dòng"`
