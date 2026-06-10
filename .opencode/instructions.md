# Agent Instructions — Docs Management

## Cấu trúc docs

- `docs/reference/` — Tài liệu active, agent **PHẢI đọc** trước khi làm việc
  - `ai-knowledge/` (K1-K15 knowledge base)
  - `guides/` (GUID_ERP, Custom Builder guide)
  - `api-contracts/` (API contracts từng module)
  - `tables/` (DB schema — auto-generated)
- `docs/dev/` — Tài liệu kiến trúc/thiết kế cũ, **KHÔNG đọc** (chỉ tham khảo khi cần thiết)
- `docs/archive/` — Docs cũ, task đã hoàn thành, **KHÔNG đọc**
- `docs/tests/` — Test cases, **KHÔNG đọc**

## Khi bạn thay đổi codebase

1. **DB schema** (thêm/sửa migration Flyway):
   - Chạy `python scripts/db-docs.py` để cập nhật `docs/reference/tables/`
2. **Business logic** lớn:
   - Cập nhật `docs/reference/guides/` tương ứng
3. **API endpoints**:
   - Cập nhật file tương ứng trong `docs/reference/api-contracts/`

## Cách chạy

```bash
# Windows
python scripts\db-docs.py

# Linux/Mac
python scripts/db-docs.py
```
