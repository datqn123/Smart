## MCP Tool Contract Pack — `spring-erp`

### Scope
- **Purpose**: Read-only access to internal Mini-ERP via Spring REST (no direct DB access).
- **Consumers**: Chat Agent (M-02), Chart Agent (M-04), Write Agent (M-05) (lookup only).
- **Non-goals**: Any mutation/commit endpoints; any “approve” tool.

### Auth & context
- **Auth**: Bearer JWT from FE → forwarded as `Authorization` header to Spring REST.
- **Required context fields (every call)**:
  - `session_id` (string)
  - `user_id` (string)
  - `correlation_id` (string, new per tool call)
  - `tenant_id` (string, if multi-tenant)

### Global guardrails (enforced server-side)
- **Allowlist**: only `/api/v1/**` read endpoints (GET/POST search patterns if used).
- **Limits**:
  - `limit <= 200`
  - `page_size <= 50`
  - `date_range_days <= 366` (unless admin role)
- **Field security**: response must be **role-filtered** (no “LLM decides what’s sensitive”).
- **PII**: omit or mask where applicable; return minimal fields needed for UI.

### Error model (shared)
```json
{
  "ok": false,
  "code": "ERP_UPSTREAM_ERROR",
  "message": "Human readable",
  "retryable": true,
  "details": { "status": 502 },
  "correlation_id": "..."
}
```

### Tools

#### 1) `products.search`
- **Intent**: product list for table, lookup for write proposals, analytics dimensions.
- **Input**
```json
{
  "query": "string|null",
  "filters": {
    "category_id": "string|null",
    "brand": "string|null",
    "stock_min": "number|null",
    "stock_max": "number|null",
    "price_min": "number|null",
    "price_max": "number|null",
    "status": "ACTIVE|INACTIVE|null"
  },
  "page": 1,
  "page_size": 20,
  "sort": [{ "field": "name", "direction": "asc|desc" }]
}
```
- **Output**
```json
{
  "items": [{ "id": "string", "code": "string", "name": "string", "stock": 10 }],
  "page": 1,
  "page_size": 20,
  "total": 123,
  "summary": "string",
  "correlation_id": "string"
}
```

#### 2) `orders.search`
- **Input**: `filters` include `date_from`, `date_to`, `status`, `customer_id`, `channel`.
- **Output**: list + pagination + `summary`.

#### 3) `customers.search`
- **Input**: `query`, `phone` (masked match), `group_id`, `status`, pagination.
- **Output**: list + pagination + `summary` (no raw PII beyond what UI already shows).

#### 4) `stock.search`
- **Input**: `product_id`, `warehouse_id`, `location_id`, `stock_min/max`, pagination.
- **Output**: list + pagination + `summary`.

#### 5) `reports.sales_summary`
- **Intent**: aggregated rows for Chart Agent / report table.
- **Input**
```json
{
  "date_from": "YYYY-MM-DD",
  "date_to": "YYYY-MM-DD",
  "group_by": "day|week|month|customer|product",
  "metrics": ["revenue", "gross_profit", "order_count", "quantity"],
  "filters": { "channel": "string|null" }
}
```
- **Output**
```json
{
  "rows": [{ "key": "string", "revenue": 0, "order_count": 0 }],
  "summary": "string",
  "correlation_id": "string"
}
```

### Logging / audit
- Log one line per call with `tool_name`, `duration_ms`, `result_size_bytes`, `correlation_id`.
- Do **not** log raw row payloads; log only counts + high-level filters.

