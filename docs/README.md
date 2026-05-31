# Project Documentation

Central home for project documentation, task artifacts, plans, guides, and manual AI test cases.

## Structure

```
docs/
├── dev/                          # Phát triển tính năng MỚI
│   ├── ai-python/                #   PRD, SRS, ADR, Tasks AI (Task001-006)
│   ├── backend/                  #   SRS backend, task artifacts, Postman
│   └── frontend/                 #   SRS, API contracts, ADR, BA, database...
│
├── fix-bug/                      # SỬA LỖI
│   ├── ai-python/                #   Progress bar fix plan
│   ├── backend/                  #   Bug reports
│   └── frontend/                 #   Bug reports, SRS fix, QA fix
│
├── upgrade/                      # NÂNG CẤP TÍNH NĂNG
│   ├── ai-python/                #   SQL factory upgrade, improvement plans
│   ├── backend/                  #   (chưa có)
│   └── frontend/                 #   UI enhancement, standardization, sync
│
├── guides/                       # Hướng dẫn nghiệp vụ (GUID_ERP.md)
├── table-description/            # Schema database (30 tables)
└── test-ai/                      # 200+ AI test cases (15 categories)
```

### Tiêu chí phân loại

| Category | Định nghĩa | Ví dụ |
|----------|-----------|-------|
| `dev/` | Xây dựng tính năng mới | Task017 (stock interface), Task039 (inbound dispatch CRUD), backend APIs |
| `fix-bug/` | Sửa lỗi | Task016 (fix dropdown), Task030 (fix parse error), Task079 (fix white screen) |
| `upgrade/` | Cải tiến / chuẩn hóa | Task033 (standardization), Task036 (polish), AI improvement plans |
