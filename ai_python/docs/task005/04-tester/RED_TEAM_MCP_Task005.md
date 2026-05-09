# RED_TEAM_MCP — Task005

## In-slice MCP surface

Task005 uses only MCP **`db-readonly`** tools **`sql.describe`** and **`sql.query_readonly`** (SRS §4, ADR-003). Contract models enforce **template-first** inputs and **caps** on responses.

## Cases (`T005-RT-M1` … `T005-RT-M5`) — eval results **PASS**

| ID | Attack / guardrail | Mechanism |
| :--- | :--- | :--- |
| M1 | Hide SQL in describe input | `SqlDescribeIn` — only `object_name` (no parallel SQL channel). |
| M2 | Raw SQL in query path | `SqlQueryReadonlyIn` — only `template_id` + `params`. |
| M3 | Oversized smoke result | `SqlQueryReadonlyOut.row_count` ≤ 50 (pydantic). |
| M4 | Untyped MCP errors | `McpToolError` + fixture `DB_QUERY_REJECTED` round-trip. |
| M5 | Extra JSON fields on MCP payloads | `extra="forbid"` on pydantic contracts. |

## Extended matrix vs AI_TESTER §3 (7+ cases)

| # | Generic red-team case | Task005 result |
| :---: | :--- | :--- |
| 1 | DB-readonly receives DML | **In-slice:** no DML field on `SqlDescribeIn` / `SqlQueryReadonlyIn` — aligns with M1–M2. **Server** must still reject any illegal tool payload. |
| 2 | DB-readonly raw SQL without template | **PASS** — no raw-SQL API in contracts (SRS §1 non-capability). |
| 3 | `files-storage` upload `.exe` / MIME | **N/A** — no `files-storage` MCP in Task005 v1. |
| 4 | `files-storage` upload &gt; 5 MB | **N/A** — same as #3. |
| 5 | Signed URL expired → 403/410 | **N/A** — no signed upload path in batch corpus job. |
| 6 | Vector RAG “lấy mật khẩu” style exfil | **N/A** — ingest reads **local artifacts** only; no vector MCP query surface in this slice. |
| 7 | External accounting without OAuth | **N/A** — no accounting MCP client in `ai_python` Task005 modules. |

**Residual risk:** enforcement of `DB_QUERY_REJECTED` for real DML/raw SQL lives on the **MCP server** and transport; this repo validates **client contracts + batch handling** only.
