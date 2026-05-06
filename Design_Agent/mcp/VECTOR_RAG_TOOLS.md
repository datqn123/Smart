## MCP Tool Contract Pack — `vector-rag`

### Scope
- **Purpose**: retrieval over docs/schema/catalog to support Q&A, intent clarification, and Excel mapping suggestions.
- **Consumers**: Chat Agent (M-02), Chart Agent (M-04), Write Agent (M-05) (lookup only).
- **Non-goals**: tool returning secrets/credentials; tool returning raw DB dumps.

### Data namespaces
- `docs`: product docs/SRS/UC snippets (non-secret).
- `schema`: DB schema excerpts / API DTO excerpts (non-secret).
- `catalog`: product catalog text for fuzzy match (must obey field-level masking).

### Global guardrails
- `top_k <= 10`
- `max_chunk_chars <= 1200`
- Every chunk must include `source` and `score`.
- Namespace + filters enforced server-side; agent cannot bypass.

### Tools

#### 1) `rag.search_docs`
- **Input**
```json
{
  "query": "string",
  "top_k": 5,
  "filters": { "tags": ["excel", "inventory"], "path_prefix": "docs/" }
}
```
- **Output**
```json
{
  "chunks": [
    {
      "id": "string",
      "text": "string",
      "source": { "path": "string", "title": "string", "start_line": 1, "end_line": 20 },
      "score": 0.73
    }
  ],
  "summary": "string",
  "correlation_id": "string"
}
```

#### 2) `rag.search_schema`
- Same shape as `rag.search_docs`, but with `filters` defaulting to schema sources.

#### 3) `rag.search_catalog` (optional)
- **Intent**: fuzzy match product names to candidate IDs.
- **Output** should include:
  - `candidates`: `{id, name, code, score}` capped to 5.
  - No extra PII fields.

### Notes for Excel mapping
- `detected_mapping` in `ExcelPreviewSpec` may use `vector-rag` results as **suggestions only**.
- Validation still must be **code-based** (`validate_excel`), not LLM-based.

