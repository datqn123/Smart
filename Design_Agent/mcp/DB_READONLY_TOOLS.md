## MCP Tool Contract Pack — `db-readonly`

### Scope
- **Purpose**: safe read-only analytics/reporting directly from DB when REST endpoints are missing.
- **Consumers**: Chart Agent (preferred), Chat Agent (only for approved report templates).
- **Non-goals**: ad-hoc SQL from LLM; any write operation.

### Connection & roles
- **DB user**: dedicated `agent_readonly` role.
- **Permissions**: SELECT on allowlisted **views** (preferred) or tables; no DDL/DML.
- **Timeouts**: statement timeout (e.g. 2–5s), max rows, max bytes.

### Global guardrails (hard)
- Only **single statement**.
- Only **SELECT** (no `INSERT/UPDATE/DELETE/MERGE`, no `COPY`, no `CALL`, no `DO`).
- Disallow `;` inside query templates.
- Enforce `LIMIT` (server adds if missing).
- Enforce allowed schemas: e.g. `reporting.*` views.

### Error model (shared)
Same as `spring-erp` pack, with DB-specific `code` values:
- `DB_QUERY_REJECTED`
- `DB_TIMEOUT`
- `DB_UPSTREAM_ERROR`

### Strategy: template-first (recommended)
LLM chooses a `template_id` + `params`, not raw SQL.

#### Tool 1) `sql.query_readonly`
- **Input**
```json
{
  "template_id": "sales_by_day_v1",
  "params": {
    "date_from": "YYYY-MM-DD",
    "date_to": "YYYY-MM-DD",
    "channel": "string|null"
  }
}
```
- **Output**
```json
{
  "columns": [{ "name": "day", "type": "date" }, { "name": "revenue", "type": "number" }],
  "rows": [["2026-05-01", 1230000]],
  "row_count": 1,
  "summary": "string",
  "correlation_id": "string"
}
```

#### Tool 2) `sql.describe`
- **Intent**: schema introspection for allowlisted objects (views/tables).
- **Input**
```json
{ "object_name": "reporting.sales_by_day_v1" }
```
- **Output**
```json
{
  "object_name": "reporting.sales_by_day_v1",
  "columns": [{ "name": "day", "type": "date", "nullable": false }],
  "summary": "string",
  "correlation_id": "string"
}
```

### Optional (only if needed): `sql.query_readonly_raw`
If your MCP implementation must support raw SQL, it must still enforce:
- SELECT-only, single-statement, allowlisted schemas, mandatory LIMIT, timeout, and a SQL parser.

