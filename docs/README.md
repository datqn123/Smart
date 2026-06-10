# Project Documentation

## Structure

```
docs/
├── reference/              # Active reference docs — agent PHẢI đọc
│   ├── ai-knowledge/       #   K1–K15 knowledge base cho AI agent
│   ├── guides/             #   Hướng dẫn nghiệp vụ (GUID_ERP, Custom Builder)
│   ├── api-contracts/      #   API contracts từng module
│   └── tables/             #   DB schema — auto-generated bởi scripts/db-docs.py
│
├── dev/                    # Dev reference (architecture cũ, component design) — KHÔNG đọc
│
├── tests/                  # AI test suite (200+ test cases) — KHÔNG đọc
│
└── archive/                # Docs cũ, task đã hoàn thành — KHÔNG đọc
```

## Nguyên tắc

| Thư mục | Agent đọc? | Mục đích |
|----------|-----------|----------|
| `reference/` | ✅ **PHẢI đọc** | Tài liệu tham khảo active — single source of truth |
| `dev/` | ❌ **Không** | Tài liệu kiến trúc/thiết kế cũ, chỉ tham khảo khi cần |
| `tests/` | ❌ Không | Test cases |
| `archive/` | ❌ **Không** | Docs đã hoàn thành, lưu giữ lịch sử |

## Khi codebase thay đổi

- **DB schema thay đổi** → chạy `python scripts/db-docs.py` để refresh `docs/reference/tables/`
- **Business logic thay đổi** → cập nhật `docs/reference/guides/` tương ứng
- **API thay đổi** → cập nhật file trong `docs/reference/api-contracts/`
