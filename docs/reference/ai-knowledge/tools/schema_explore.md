# SchemaExploreTool

> Source: `ai_python/app/graph/tools/schema_explore.py`
> Prompt: schema_explore.md

## Tổng quan
Khám phá và truy xuất thông tin schema database cho một chủ đề nhất định. Tạo ra schema plan hoặc runtime schema artifact dùng cho các bước sinh SQL phía sau.

## Manifest (ToolRegistry)
| Field | Value |
|-------|-------|
| name | `schema_explore` |
| capability | `data_read` |
| side_effect_class | `read_only` |
| has_hitl | `false` |
| risk_level | `low` |
| produces | `("schema",)` |
| consumes | — |
| result_ref_policy | — |
| examples | — |

## Schema đầu vào
```json
{
  "topic": "string"
}
```

## Đầu ra / Quan sát
**Schema plan mode:**
```json
{
  "schema_plan": {
    "tables": ["table_a", "table_b"],
    "columns": {"table_a": ["col1", "col2"]}
  }
}
```
Quan sát: `"Schema plan: {JSON truncated to 800 chars}"`

**Runtime artifact mode:**
```json
{
  "runtime_schema_artifact": {
    "tables": {...},
    "relationships": {...}
  }
}
```
Quan sát: `"Schema artifact loaded."`

## Tích hợp Runtime

### Harness (v3.0)
- Gọi bởi: `PlanExecutor` qua `ToolRegistry`
- Node type trong PlanGraph: `tool`
- Dùng để khám phá schema trước khi sinh SQL

### LangGraph (Legacy)
- Subgraph: `sql_subgraph`
- Nodes: `schema_explore`
- Node đầu tiên trong SQL pipeline, cung cấp context schema

## Xử lý lỗi
- Ủy thác cho `make_schema_explore_node`
- Kiểm tra thành công: `ok = not bool(error_payload)`
- Trả về error payload nếu khám phá schema thất bại

## Ví dụ
**Đầu vào:**
```json
{
  "topic": "customer orders"
}
```
**Đầu ra:**
```json
{
  "schema_plan": {
    "tables": ["customers", "orders", "order_items"],
    "columns": {
      "customers": ["customer_id", "customer_name", "email"],
      "orders": ["order_id", "customer_id", "order_date", "total"],
      "order_items": ["item_id", "order_id", "product_id", "quantity"]
    }
  }
}
```
Quan sát: `"Schema plan: {\"tables\": [\"customers\", \"orders\", \"order_items\"], ...}"`
