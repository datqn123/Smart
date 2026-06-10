# Project Documentation

## Structure

```
docs/
├── reference/              # Active reference docs — agent sẽ đọc để hiểu hệ thống
│   ├── ai-knowledge/       #   K1–K15 knowledge base cho AI agent
│   ├── guides/             #   Hướng dẫn nghiệp vụ (GUID_ERP, Custom Builder)
│   ├── api-contracts/      #   API contracts frontend ↔ backend (từ dev/frontend/api/)
│   ├── use-cases/          #   UC specs & diagrams
│   └── tables/             #   DB schema — auto-generated bởi scripts/db-docs.py
│
├── dev/                    # Dev reference (frontend ADR, database docs, project overview)
│   └── frontend/
│
├── tests/                  # AI test suite (200+ test cases)
│
└── archive/                # Docs cũ, task đã hoàn thành — agent KHÔNG đọc
    ├── frontend/           #   SRS, tech_lead task001-028
    ├── superpowers/        #   Superpowers plans & specs
    ├── upgrade-ai-python/  #   SRS, tech_lead, QA, ADR upgrades
    ├── fix-bug/            #   Bug reports & fix plans
    ├── backend/            #   Backend SRS, task artifacts
    ├── claude/             #   Docs Claude cũ
    ├── dev-ai-python/      #   ADR, PRD, SRS AI Python tasks
    ├── dev-backend/        #   Backend setup & task docs
    ├── dev-common/         #   Custom builder overview
    ├── dev-frontend/       #   Frontend analysis & old SRS
    ├── dev-requires/       #   Requirement docs
    ├── table-description/  #   Schema docs cũ (V1–V52)
    └── sql/                #   Full schema doc cũ
```

## Nguyên tắc

| Thư mục | Agent đọc? | Mục đích |
|----------|-----------|----------|
| `reference/` | ✅ **Có** | Tài liệu tham khảo active, cần thiết để hiểu codebase |
| `dev/` | ✅ Có | Tài liệu kiến trúc, API contracts, project overview |
| `tests/` | ❌ Không | Test cases, không cần đọc để hiểu logic |
| `archive/` | ❌ **Không** | Docs đã hoàn thành, lưu giữ lịch sử |

## Khi codebase thay đổi

- **DB schema thay đổi** → chạy `python scripts/db-docs.py` để refresh `docs/reference/tables/`
- **Business logic thay đổi** → cập nhật `docs/reference/guides/` tương ứng
- **API thay đổi** → cập nhật `docs/reference/api-contracts/`
