## MCP Tool Contract Pack — `files-storage`

### Scope
- **Purpose**: provide signed URLs + lifecycle for temporary files (Excel import/export, error reports).
- **Consumers**: Chat Agent (M-02), Excel tools (parse/validate/export compute), FE upload/download UI.
- **Non-goals**: long-term archival; arbitrary file browsing.

### Global guardrails
- **Allowlist MIME**:
  - `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
  - (optional) `application/vnd.ms-excel`
- **Caps**:
  - `max_upload_size_bytes = 5_000_000`
  - `max_ttl_seconds = 900` (15 min)
- **Namespacing**: store under `ai-chat/<tenant>/<session>/<file_id>`.
- **Lifecycle**: auto-delete after TTL + grace window.

### Common types
#### `SignedUploadSpec`
```json
{
  "file_id": "string",
  "upload_url": "string",
  "expires_at": "ISO-8601",
  "headers": { "Content-Type": "string" }
}
```

#### `SignedDownloadSpec`
```json
{
  "file_id": "string",
  "download_url": "string",
  "filename": "string",
  "mime": "string",
  "expires_at": "ISO-8601",
  "size_bytes": 123
}
```

### Tools

#### 1) `files.put_signed_upload_url`
- **Input**
```json
{ "mime": "string", "size_bytes": 123, "filename": "string|null" }
```
- **Output**: `SignedUploadSpec` + `correlation_id`.

#### 2) `files.get_signed_download_url`
- **Input**
```json
{ "file_id": "string", "ttl_seconds": 600 }
```
- **Output**: `SignedDownloadSpec` + `correlation_id`.

#### 3) `files.delete`
- **Input**: `{ "file_id": "string" }`
- **Output**: `{ "ok": true, "correlation_id": "string" }`

### Security notes
- The tool must not accept arbitrary URLs; it only generates URLs for internally managed objects.
- Prefer short-lived pre-signed URLs; never expose bucket keys.
- Do not log file bytes; log only `file_id`, `size_bytes`, `mime`, `session_id`.

