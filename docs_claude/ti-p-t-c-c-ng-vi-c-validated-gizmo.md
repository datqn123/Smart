# Trạng thái thiết kế giao diện Custom Builder & Bước tiếp theo

## Context

Người dùng muốn biết giao diện Custom Builder Settings đã hoàn thiện đến đâu và cần làm gì tiếp theo. Đây là dự án đồ án tốt nghiệp — hệ thống mini-ERP với tính năng cho phép admin tự xây dựng giao diện tùy chỉnh (Custom Builder).

---

## Trạng thái hiện tại: **GẦN HOÀN THIỆN**

### ✅ Đã hoàn thiện (toàn bộ các stage có spec)

| Stage | Nội dung | File |
|-------|----------|------|
| S1 | Builder list page (search, filter, table, empty state) | CustomBuilderPage.tsx:1096–1244 |
| S2–S3 | Create wizard 5 bước (basic info → menu → fields → display → review) | CustomBuilderPage.tsx:1246–1679 |
| S3–S4 | Edit settings 6 tab (overview, data, display, permissions, check, advanced) | CustomBuilderPage.tsx:1681–2112 |
| S4A | Field logic settings (validation rules, defaults, options, readonly/hidden, conditional visibility) | CustomBuilderPage.tsx:424–629 |
| S5 | Usability + publish readiness (grouped errors, "Sửa lỗi đầu tiên", publish gate) | CustomBuilderPage.tsx:2113–2299 |
| 014 | Workflow Designer (states, transitions, roles, preview) | CustomBuilderPage.tsx:652–844 |
| **015** | **Logic Connector Builder (rules, 5-step wizard, dry-run, JSON preview)** | CustomBuilderPage.tsx:861–1094 |

**Tổng: 2,299 dòng — tất cả spec từ S1 đến 015 đã được code.**

---

## ⚠️ Công việc đang dở (từ git status)

```
M  customBuilderMockAdapter.ts   ← có thay đổi chưa commit
M  CustomBuilderPage.tsx          ← có thay đổi chưa commit
?? docs/frontend/qa/015_custom-builder-logic-connector-builder.md
?? docs/frontend/tech_lead/015_custom-builder-logic-connector-builder.md
```

**Stage 015 (Logic Connector Builder) đã được implement nhưng chưa commit.** Spec docs cũng đã viết xong nhưng chưa được tracked.

---

## 🔲 Stubs / placeholder (chưa làm & đúng theo kế hoạch)

| Item | Vị trí | Lý do |
|------|---------|-------|
| Inventory Effect | Advanced tab | Out of scope giai đoạn hiện tại |
| AI Copilot | Advanced tab | Out of scope giai đoạn hiện tại |
| Computed field | FieldLogicSettings | Placeholder — cần spec riêng |
| "Xem thử" (live preview) | List row action | Chưa có runtime page |
| "Nhân bản" (duplicate) | List row action | Chưa có handler |
| Publish thật | publish() | Mock 409 conflict — chưa có backend |
| Backend API | Toàn bộ | Tất cả đang dùng mock adapter |
| Multi-section form builder | Display tab | Chỉ edit `formSections[0]` |

---

## Khuyến nghị: Bước tiếp theo

### Bước 1 — Verify & commit stage 015 (NGAY BÂY GIỜ)

1. Xem diff của 2 file đang modified để xác nhận stage 015 hoàn chỉnh
2. Kiểm tra Logic Connector Builder UI có khớp với wireframe `.codex-artifacts/custom-builder-logic-connector-desktop.png` không
3. Commit cả 4 file (2 code + 2 docs) vào git

### Bước 2 — Kiểm tra display tab còn thiếu

Theo spec nhưng chưa có UI:
- Column width/alignment/format editor (`BuilderViewColumn.width/align/format` có trong type nhưng không có UI)
- Filter field configuration panel (filterFields hiện set tự động)
- Default sort picker (defaultSort chưa có UI chỉnh)

### Bước 3 — Multi-section form builder (tùy chọn)

Hiện tại chỉ edit `formSections[0]`. Nếu muốn đầy đủ cần thêm UI add/remove/reorder sections.

---

## Các file cần đọc khi implement

- [CustomBuilderPage.tsx](frontend/mini-erp/src/features/custom-builder/pages/CustomBuilderPage.tsx) — toàn bộ UI
- [customBuilderMockAdapter.ts](frontend/mini-erp/src/features/custom-builder/api/customBuilderMockAdapter.ts) — types + mock data
- [docs/frontend/tech_lead/015_custom-builder-logic-connector-builder.md](docs/frontend/tech_lead/015_custom-builder-logic-connector-builder.md) — spec stage 015
- [docs/frontend/qa/015_custom-builder-logic-connector-builder.md](docs/frontend/qa/015_custom-builder-logic-connector-builder.md) — QA spec stage 015
- `.codex-artifacts/custom-builder-logic-connector-desktop.png` — wireframe tham chiếu

---

## Verification

1. Chạy `npm run dev` tại `frontend/mini-erp/`
2. Đăng nhập → vào `/settings/custom-builder`
3. Kiểm tra list page, wizard, và edit settings
4. Mở Advanced tab → kiểm tra Logic Connector Builder
5. So sánh với wireframe desktop/mobile trong `.codex-artifacts/`
6. Chạy `npm run lint` để đảm bảo không có lỗi TypeScript
