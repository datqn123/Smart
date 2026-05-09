# RUNBOOK — Task004 — `smart-erp-ai` MCP (stdio)

## 1. Cài dependencies

Từ thư mục `ai_python/`:

```powershell
pip install -r requirements.txt
```

## 2. Chạy server (stdio)

```powershell
Set-Location d:\do_an_tot_nghiep\project\ai_python
python -m app.smart_erp_mcp
```

Cursor: thêm MCP server command trỏ tới `python` với args `-m app.smart_erp_mcp`, `cwd` = `.../ai_python`.

## 3. HTTP relay (FastAPI)

Chạy API (ví dụ port 9000):

```powershell
Set-Location d:\do_an_tot_nghiep\project\ai_python
python -m uvicorn app.main:app --host 0.0.0.0 --port 9000
```

Gọi một lượt intent + tool:

```powershell
curl -s -X POST http://localhost:9000/v1/smart-erp/turn -H "Content-Type: application/json" -d "{\"user_text\":\"tồn kho\"}"
```

- `SMART_ERP_MCP_STDIO=1` — mỗi request spawn MCP stdio (kết nối protocol thật).
- `SMART_ERP_MCP_INLINE=1` — in-process (mặc định khi không bật stdio).

## 4. Kiểm tra nhanh (pytest)

```powershell
pytest -q tests/unit -k smart_erp_mcp
```

## 5. Ghi chú an toàn

- `sql_execute_read` chỉ chạy trên SQLite **in-memory** seeded — không kết nối Postgres/Spring trong slice này.
- `write_commit` là **stub**; không gọi backend.
