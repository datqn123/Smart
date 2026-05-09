# Task005 — db_rag_agent_context (Option B)

This module ships the **batch corpus pipeline** for ERP RAG context (`ai_python/`
only — no Chat Agent HTTP/SSE/UI in v1).

## Layout

```text
app/
  agents/task005_corpus_job.py     # Pipeline orchestrator (CorpusJobContext)
  cli/task005_config.py            # JSON config loader (objects + templates)
  cli/task005_corpus_job.py        # CLI entrypoint (argparse + asyncio.run)
  contracts/task005.py             # Pydantic models (SqlDescribe*, McpToolError, ...)
  mcp/db_readonly_port.py          # `Protocol` for the `db-readonly` MCP client
  rag/task005_ingest.py            # Local RAG ingest stub + readback
  registry/task005_templates.py    # Template registry loader
  tools/task005_artifacts.py       # Catalog / health artifact view-models
  tools/task005_corpus_fs.py       # Corpus path layout + atomic writes
  tools/task005_describe.py        # `sql.describe` batch loop
  tools/task005_logging.py         # Structured JSON logger
  tools/task005_smoke.py           # `sql.query_readonly` smoke loop
data/
  rag_corpus/                      # output (catalog/health/index per corpus_version)
  config/task005_objects.example.json
  config/task005_templates.example.json
```

## Daily refresh entrypoint

```bash
python -m app.cli.task005_corpus_job \
  --objects ai_python/data/config/task005_objects.example.json \
  --templates ai_python/data/config/task005_templates.example.json \
  --corpus-root ai_python/data/rag_corpus
```

The CLI emits structured JSON log lines to stderr (events: `run.started`,
`describe.ok` / `describe.error` / `describe.transport_error`, `smoke.ok`
/ `smoke.error` / `smoke.transport_error`, `run.finished`, `run.crashed`).

### Exit codes

| Code | Meaning |
| :---: | :--- |
| `0` | All describe + smoke calls succeeded; index written. |
| `1` | At least one describe or smoke step failed (see `health.json` / log). |
| `2` | Fatal error before completion (e.g. config file missing). |

## Output namespaces

- `erp_schema/catalog__<corpus_version>.json` — describe catalog (column metadata).
- `erp_template_health/health__<corpus_version>.json` — smoke status (no rows).
- `index/index__<corpus_version>.json` — local RAG index built from the above.

`corpus_version` is the run's UTC start time formatted as `YYYY-MM-DDTHH-MM-SSZ`.

## Safety invariants (SRS §7 AC4)

- Read-only MCP only — pipeline never issues writes.
- No SQL row payloads land in artifacts (smoke surface is summary + ok + code).
- No DB credentials in logs or artifacts; logs use `correlation_id` for tracing.

## Wiring a real MCP client

The pipeline depends on the structural type
`app.mcp.db_readonly_port.DbReadonlyMcpClient`. To go live, write a transport
adapter (e.g. JSON-RPC over stdio) that satisfies the protocol and inject it
through `run_cli(client=...)` or call `run_corpus_job` directly.
