# Agent Instructions — Docs Management

## Quy tắc tìm kiếm bắt buộc

Dùng MCP CodeGraph (`codegraph`) cho mọi truy vấn tìm kiếm trong codebase. Không dùng grep thuần (bash rg/grep) khi cần phân tích dependency, call graph, hoặc structure.

## Cấu trúc docs

- `docs/reference/` — Tài liệu active, agent **PHẢI đọc** trước khi làm việc
  - `ai-knowledge/` (K1-K15 knowledge base)
  - `ai-knowledge/tools/` (Tool reference docs — auto-update khi code thay đổi)
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

## Quy tắc cập nhật reference khi code thay đổi

Khi bạn thay đổi code trong `ai_python/`:

1. **Tool thay đổi** (thêm/sửa/xóa tool trong `app/graph/tools/` hoặc `app/harness/tool_registry.py`):
   - Cập nhật file tương ứng trong `docs/reference/ai-knowledge/tools/`
   - Nếu thêm tool mới: tạo file mới + cập nhật `index.md`
   - Nếu xóa tool: xóa file + cập nhật `index.md`

2. **Prompt thay đổi** (sửa file trong `app/prompts/agents/`):
   - Cập nhật section "Prompt" trong file tool tương ứng

3. **Graph structure thay đổi** (sửa `app/graph/main_graph.py`, `app/graph/sql_subgraph.py`, v.v.):
   - Cập nhật section "LangGraph (Legacy)" trong file tool tương ứng

4. **Harness integration thay đổi** (sửa `app/harness/orchestrator.py`, `app/harness/plan_graph.py`):
   - Cập nhật section "Harness (v3.0)" trong file tool tương ứng

Mọi conversation đều PHẢI tuân thủ rule này. Không được bỏ qua.

## Cách chạy

```bash
# Windows
python scripts\db-docs.py

# Linux/Mac
python scripts/db-docs.py
```
