# 🧠 ARCHITECTURE DECISION RECORD (ADR) - ADR-0002

**Mã ADR:** `ADR-0002_master-table-pattern-standardization`
**Trạng thái:** 🟢 Accepted
**Quyết định:** Chuẩn hóa toàn bộ Table Layout trong Inventory theo mô hình Standalone Header & Scroll Context.

---

## 1. Context (Bối cảnh)
Hệ thống Mini-ERP cần sự nhất quán cao trong trải nghiệm người dùng. Hiện tại các trang như DispatchPage và StockPage có cách quản lý header và scroll khác nhau, dẫn đến trải nghiệm không đồng bộ khi cuộn dữ liệu.

## 2. Decision (Quyết định)

1. **Scroll context:** Toàn bộ trang dùng `overflow-hidden`. Một vùng danh sách có `overflow-y-auto` + `[scrollbar-gutter:stable]` + `min-h-0` (flex).
2. **Một `<table>` cho mỗi danh sách:** `TableHeader` + `TableBody` nằm trong **cùng** `<Table>` trong cùng vùng cuộn; **không** dùng hai `<Table>` (header strip + body) vì wrapper `overflow-x-auto` của shadcn làm **lệch cột** khi `table-fixed`.
3. **Sticky header hàng tiêu đề:** `sticky top-0` trên `<TableHeader>` bên trong bảng đó.
4. **Typography:** Mã thực thể (SKU, mã phiếu) dùng font mono.
5. **Style wrapper:** `bg-white border-slate-200/60 rounded-xl shadow-md`.
6. **Token chung:** Width và class gốc tập trung tại `mini-erp/src/lib/data-table-layout.ts`; chi tiết UX/cột trong [RULES_UI_TABLE.md](../rules/RULES_UI_TABLE.md).

> **Ghi chú cập nhật (18/04/2026):** Pattern “Standalone Header” (hai bảng) được **thay thế** bởi quyết định mục 2–3 ở trên. ADR vẫn giữ mã để lịch sử; chuẩn hiện hành là `RULES_UI_TABLE.md`.

## 3. Non-Functional Requirements (NFR) - BẮT BUỘC

| NFR | Mô tả tác động |
| :--- | :--- |
| **Performance** | Không ảnh hưởng đáng kể. Cần đảm bảo `IntersectionObserver` được dọn dẹp (disconnect) đúng cách khi component unmount. |
| **Scalability** | Giúp việc bảo trì dễ dàng hơn khi áp dụng cho các module mới sau này. |
| **Security** | Không ảnh hưởng. |
| **Reliability** | Tránh lỗi trôi header trên các trình duyệt khác nhau khi cuộn. |
| **Observability** | Thêm data-testid cho Container cuộn để hỗ trợ E2E Testing. |

## 4. Guardrails cho Agent DEV
- **Rule 1:** Cột action `sticky right-0` — tránh bọc thêm `overflow-x-auto` **bên ngoài** cả khối bảng+scroll dọc làm hỏng sticky (wrapper `overflow-x-auto` **chỉ** nên là của component `Table` nếu cần cuộn ngang nội dung bảng).
- **Rule 2:** Width `th`/`td` cùng cột phải khớp — dùng token từ `data-table-layout.ts`, không magic number rải rác.
- **Rule 3:** Skeleton/spinner khi `isLoadingMore`.
- **Rule 4:** Không đặt `flex` trực tiếp trên `td`/`th`; nhóm nút trong `div` flex bên trong cell.

---
**Người lập:** Agent Tech Lead
**Ngày:** 17/04/2026
