# Agent Instructions — Docs Management

## Cấu trúc docs

- `docs/reference/` — Tài liệu active, cần đọc để hiểu codebase
- `docs/dev/` — Tài liệu kiến trúc, API contracts
- `docs/archive/` — Docs cũ, task đã hoàn thành, **KHÔNG đọc**
- `docs/tests/` — Test cases, không cần đọc

## Khi bạn thay đổi codebase

1. **DB schema** (thêm/sửa migration Flyway):
   - Chạy `python scripts/db-docs.py` để cập nhật `docs/reference/tables/`

2. **Business logic** lớn:
   - Cập nhật `docs/reference/guides/` tương ứng

3. **API endpoints**:
   - Cập nhật hoặc tạo file trong `docs/reference/api-contracts/`

## Cách chạy

```bash
# Windows
python scripts\db-docs.py

# Linux/Mac
python scripts/db-docs.py
```
