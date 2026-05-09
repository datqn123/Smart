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

## 3. Kiểm tra nhanh (pytest)

```powershell
pytest -q tests/unit/test_smart_erp_mcp_*.py
```

## 4. Ghi chú an toàn

- `sql_execute_read` chỉ chạy trên SQLite **in-memory** seeded — không kết nối Postgres/Spring trong slice này.
- `write_commit` là **stub**; không gọi backend.
