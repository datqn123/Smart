# Project Documentation

Central home for project documentation, task artifacts, plans, guides, and manual AI test cases.

## Structure

```
docs/
├── dev/                          # Phát triển tính năng MỚI
│   ├── ai-python/                #   PRD, SRS, ADR, Tasks AI (Task001-006)
│   ├── backend/                  #   SRS backend, task artifacts, Postman
│   └── frontend/                 #   SRS, API contracts, ADR, database...
│
├── fix-bug/                      # SỬA LỖI
│   ├── ai-python/                #   Progress bar fix plan
│   ├── backend/                  #   Bug reports
│   └── frontend/                 #   Bug reports, SRS fix, QA fix
│
├── upgrade/                      # NÂNG CẤP TÍNH NĂNG (AI-Python)
│   └── ai-python/                #   SQL factory upgrade (Task007)
│
├── frontend/                     # Workflow chính (S/RS, Tech Lead, QA, Code Review)
│
├── guides/                       # Hướng dẫn nghiệp vụ (GUID_ERP.md)
├── table-description/            # Schema database (30 tables)
└── test-ai/                      # 200+ AI test cases (15 categories)
```

### Tiêu chí phân loại

| Category | Định nghĩa | Ví dụ |
|----------|-----------|-------|
| `dev/` | Xây dựng tính năng mới | Backend SRS, frontend API contracts, database docs |
| `fix-bug/` | Sửa lỗi | Bug reports, SRS fix, QA fix |
| `upgrade/` | Cải tiến / chuẩn hóa | AI-Python SQL factory upgrade |
