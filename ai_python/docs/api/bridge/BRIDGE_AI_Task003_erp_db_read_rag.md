# BRIDGE — Task003 — erp_db_read_rag

- Mode: verify
- Date: 2026-05-09
- Path: `POST /v1/task003/stream` + MCP `vector-rag` / `db-readonly`

## Bridge table

| Item | SRS | ai_python | Spring relay | FE Chat | MCP doc | Notes / drift |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Endpoint turn | §2 stream contract | `app/api/task003_router.py` — `POST /v1/task003/stream` | n/a *(chưa thấy route relay)* — grep `backend/` | n/a *(chưa thấy client)* — grep FE | — | Spring/FE: **MISSING** — cần handoff relay/UI sau |
| SSE `token` | §2 | `orchestrator.py` / `task003_graph.py` | n/a | n/a | — | MATCH vs SRS trong scope Python |
| SSE `tool_call` / `tool_result` | §2 | `task003_graph.py` | n/a | n/a | — | MATCH |
| SSE `error` / `done` | §2 | `orchestrator.py`, contracts | n/a | n/a | — | MATCH |
| `rag.search_docs` / `rag.search_schema` | §4.1 | `in_memory_clients.py` (stub), ports | — | — | [`Design_Agent/mcp/VECTOR_RAG_TOOLS.md`](../../../../Design_Agent/mcp/VECTOR_RAG_TOOLS.md) | MATCH (stub conforms shape) |
| `sql.query_readonly` / templates | §4.2 | `db_readonly_tool.py`, `registry/templates.py` | — | — | [`Design_Agent/mcp/DB_READONLY_TOOLS.md`](../../../../Design_Agent/mcp/DB_READONLY_TOOLS.md) | MATCH conceptual; prod server là handoff MCP |

## Verdict

- **ai_python ↔ SRS:** MATCH  
- **ai_python ↔ Spring:** MISSING (relay path chưa map `task003` — expected ngoài scope Task003 slice)  
- **ai_python ↔ FE:** MISSING (UI chưa gọi `POST /v1/task003/stream`)  
- **ai_python ↔ MCP doc:** MATCH (I/O aligns; runtime wiring = MCP server handoff)

## Drift items (if any)

- Không có **Block** nội bộ Python. Thiếu Spring/FE là **MISSING**, có handoff — cho phép theo WORKFLOW_RULE (không sửa `backend/`/`frontend/` trong slice).

## Handoffs

- **Backend bridge:** Khi có relay Spring → đối chiếu SSE envelope JSON một dòng/`data:` giống `orchestrator._sse_data_line`. Xem [`backend/AGENTS/API_BRIDGE_AGENT_INSTRUCTIONS.md`](../../../../backend/AGENTS/API_BRIDGE_AGENT_INSTRUCTIONS.md) — Path: proxy `POST {pythonBase}/v1/task003/stream` + forward `Correlation-Id`.
- **FE bridge:** Consumer chat có thể mở rộng sau theo [`frontend/AGENTS/docs/FE_API_CONNECTION_GUIDE.md`](../../../../frontend/AGENTS/docs/FE_API_CONNECTION_GUIDE.md) — event names `token`|`tool_call`|`tool_result`|`error`|`done`.
