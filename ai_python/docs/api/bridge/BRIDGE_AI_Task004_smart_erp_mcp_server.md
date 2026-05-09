# BRIDGE_AI_Task004_smart_erp_mcp_server

| Field | Value |
| :--- | :--- |
| **Task** | Task004 |
| **SRS** | [`SRS_AI_Task004_smart_erp_mcp_server.md`](../srs/SRS_AI_Task004_smart_erp_mcp_server.md) |

## MCP tools (stdio host: `smart-erp-ai`)

| SRS § | MCP tool | Args (summary) | Response (summary) | Notes |
| :--- | :--- | :--- | :--- | :--- |
| 4.1 | `intent_analyze` | `user_text`, `session_id?` | `primary_intent`, `suggested_tools`, `hitl_required` | No SSE; JSON only |
| 4.2 | `rag_retrieve` | `query`, `top_k` | `chunks[]`, `rag_stale_warning` | Stub chunks |
| 4.3 | `read_catalog_snapshot` | — | `tables`, `data_as_of` | Demo catalog |
| 4.4 | `sql_propose_select` | `draft_sql`, `rag_table_hints?` | `normalized_sql`, `warnings` | sqlglot validate |
| 4.5 | `sql_execute_read` | `sql` | `columns`, `rows`, `data_as_of` | SQLite `:memory:` |
| 4.6 | `ui_build_form_spec` | `title`, `fields`, `defaults?` | `spec` | FE contract |
| 4.6 | `ui_build_table_spec` | `title`, `columns`, `rows` | `spec` | FE contract |
| 4.7 | `viz_build_chart_spec` | `chart_type`, `labels`, `series` | `spec` | FE contract |
| 4.8 | `write_commit` | `proposal_id`, `hitl_token`, `idempotency_key`, `payload_json` | `status` stub | No backend I/O |

## Task003 relation

- Task003 **chat** remains template-based `db-readonly` per ADR-001.
- Task004 MCP is **separate stdio server** per ADR-002; no change to Task003 SSE envelope required for minimal integration.
