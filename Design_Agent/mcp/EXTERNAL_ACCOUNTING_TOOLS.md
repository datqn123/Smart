## MCP Tool Contract Pack — `external-accounting`

### Scope
- **Purpose**: connect to external ERP/accounting systems for reconciliation and syncing reference data.
- **Consumers**: Chat Agent (M-02) and Chart Agent (M-04) (read-first).
- **Non-goals**: write/commit without HITL; direct credential exposure.

### Auth
- Prefer OAuth / API key stored server-side (never returned to agent).
- Credentials keyed by `tenant_id` + `integration_id`.

### Guardrails
- **Phase 1 (read-only)** only.
- Rate limits and pagination enforced.
- Field minimization: only return fields needed for reconciliation views.
- Strong audit trail: store `integration_provider`, `endpoint`, `external_request_id`.

### Tools (Phase 1)

#### 1) `accounting.read_invoices`
- **Input**
```json
{ "date_from": "YYYY-MM-DD", "date_to": "YYYY-MM-DD", "status": "string|null", "page": 1, "page_size": 50 }
```
- **Output**
```json
{
  "items": [{ "id": "string", "number": "string", "total": 0, "currency": "VND", "issued_at": "ISO-8601" }],
  "total": 0,
  "summary": "string",
  "correlation_id": "string"
}
```

#### 2) `accounting.read_customers`
- Similar to `spring-erp.customers.search` but with provider-specific identifiers.

#### 3) `accounting.read_payments`
- For reconciliation of paid/unpaid amounts.

### Phase 2 (write) — gated
If later needed, add `accounting.propose_*` tools only, and require:
- Write Agent + HITL approval
- deterministic mapping rules (code)
- idempotency keys + rollback strategy

