# SqlQueryTool

> Source: `ai_python/app/graph/tools/sql_query.py`
> Prompts: gen_sql.md, sql_review.md, verify_sql_intent.md, analyze_empty_result.md, schema_explore.md

## Tổng quan
Thực thi truy vấn SQL với cơ chế tự sửa lỗi. Xử lý toàn bộ pipeline: khám phá schema, sinh SQL, kiểm duyệt, thực thi, phân tích kết quả với retry budget.

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
| examples | — |

## Schema đầu vào
```json
{
  "query": "string"
}
```

## Đầu ra / Quan sát
```json
{
  "query_result": {
    "rows": [
      {"col1": "val1", "col2": "val2"}
    ]
  },
  "generated_sql": "SELECT ..."
}
```
Quan sát: `"SQL rows: [first 5 rows JSON] ... N rows total"`

## Tích hợp Runtime

### Harness (v3.0)
- Gọi bởi: `PlanExecutor` qua `ToolRegistry`
- Node type trong PlanGraph: `tool`
- Dùng `SelfCorrectingSqlRunner` với retry budget để tự sửa lỗi

### LangGraph (Legacy)
- Subgraph: `sql_subgraph`
- Nodes: `schema_explore`, `gen_sql`, `verify_sql_intent`, `sql_review`, `validate_sql`, `execute_sql`, `analyze_empty_result`, `validate_result`, `chart_readiness`
- Thực thi SQL qua multi-stage validation và correction loop

## Xử lý lỗi
- **Self-correction loop**: gen_sql → sql_review → execute_sql với retry budget
- **Phát hiện lỗi trùng lặp**: Ngăn vòng lặp vô hạn khi lỗi lặp lại
- **Phân tích kết quả rỗng**: Kích hoạt prompt `analyze_empty_result` khi query không trả về dòng nào
- **Che cột nhạy cảm theo role**: Lọc cột dữ liệu nhạy cảm dựa trên quyền user
- **sanitize_user_data**: Thoát và kiểm tra dữ liệu đầu vào để ngăn SQL injection

## Ví dụ
**Đầu vào:**
```json
{
  "query": "Show me top 10 products by revenue this month"
}
```
**Đầu ra:**
```json
{
  "query_result": {
    "rows": [
      {"product_name": "Product A", "revenue": 1500000},
      {"product_name": "Product B", "revenue": 1200000}
    ]
  },
  "generated_sql": "SELECT product_name, SUM(revenue) as revenue FROM sales WHERE month = CURRENT_MONTH GROUP BY product_name ORDER BY revenue DESC LIMIT 10"
}
```
Quan sát: `"SQL rows: [{\"product_name\": \"Product A\", \"revenue\": 1500000}, ...] ... 10 rows total"`
