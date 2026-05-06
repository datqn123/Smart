## MCP Tool Contract Pack — `google-drive-sheets`

### Scope
- **Purpose**: let users pick files from Drive and export reports to Google Sheets.
- **Consumers**: Chat Agent (M-02) (routing + UI), Excel flows (optional).
- **Non-goals**: full Drive admin, domain-wide delegation (unless explicitly required).

### Auth
- OAuth **user-consent**.
- Store refresh token per `user_id` (and `tenant_id` if multi-tenant).
- Scopes (minimal):
  - Drive: readonly (list + download)
  - Sheets: write only when exporting

### Guardrails
- Limit file listing (`page_size <= 50`).
- Restrict to supported MIME types (xlsx, google sheet) depending on tool.
- Never return file content unless explicitly requested and size-limited.

### Tools

#### 1) `drive.list_files`
- **Input**
```json
{ "query": "string|null", "page_token": "string|null", "page_size": 20 }
```
- **Output**
```json
{
  "files": [{ "id": "string", "name": "string", "mime": "string", "modified_at": "ISO-8601" }],
  "next_page_token": "string|null",
  "summary": "string",
  "correlation_id": "string"
}
```

#### 2) `drive.get_file`
- **Intent**: download a Drive file into `files-storage` as a `file_id` (preferred), or return a byte stream reference.
- **Input**: `{ "file_id": "string" }`
- **Output**: `{ "storage_file_id": "string", "summary": "string", "correlation_id": "string" }`

#### 3) `sheets.export`
- **Input**
```json
{ "title": "string", "columns": [{ "key": "string", "label": "string" }], "rows": [["..."]] }
```
- **Output**: `{ "spreadsheet_id": "string", "url": "string", "summary": "string", "correlation_id": "string" }`

#### 4) `sheets.import` (optional)
- **Intent**: read a sheet into a `files-storage` file_id or structured rows with caps.

