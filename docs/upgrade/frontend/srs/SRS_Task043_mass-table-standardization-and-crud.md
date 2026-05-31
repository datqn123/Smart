# SRS - Chuẩn hóa toàn bộ Table và Hoàn thiện CRUD (Global Table Standardization)

> **File**: `docs/srs/SRS_Task043_mass-table-standardization-and-crud.md`
> **Người viết**: Agent BA
> **Ngày tạo**: 18/04/2026
> **Phiên bản**: 1.0
> **Trạng thái**: Pending Approval ⏳
> **Task**: Task043

---

## 1. Tầm nhìn (Vision)

Đảm bảo tính nhất quán UI/UX trên toàn hệ thống Mini-ERP bằng cách áp dụng **Master Table Pattern** cho tất cả các bảng danh sách. Đồng thời, hoàn thiện khả năng CRUD (Thêm, Sửa, Xóa, Xem) cho tất cả các thực thể nghiệp vụ cốt lõi, giúp người dùng quản lý dữ liệu hiệu quả và chuyên nghiệp.

---

## 2. Phạm vi (In-scope/Out-of-scope)

### 2.1 In-scope

- **Chuẩn hóa Layout**: Refactor tất cả các Table sang mô hình 1-Table-Architecture (Header + Body chung 1 scroll area).
- **Hoàn thiện CRUD**: Bổ sung các chức năng còn thiếu (thường là Thêm/Sửa/Xóa) cho:
  - Khách hàng (Customers)
  - Nhà cung cấp (Suppliers)
  - Sản phẩm (Products)
  - Danh mục (Categories)
  - Nhân viên (Users/Employees)
  - Đơn hàng (Orders) - Xem/Hủy
  - Giao dịch (Finance Ledger) - Xem/Xóa
  - Kho bãi (Warehouse Locations) - Mới
- **Bổ sung bảng log**:
  - Nhật ký kho (Inventory Logs) - View only
  - Nhật ký hệ thống (System Logs) - View only
- **Technical**: Cập nhật `mini-erp/src/lib/data-table-layout.ts` với các token width mới.

### 2.2 Out-of-scope

- Các logic nghiệp vụ phức tạp liên quan đến tính toán (đã có trong các task riêng).
- Tích hợp AI/OCR trong các form (đã có task riêng).
- Phân quyền chi tiết nâng cao (RBAC cơ bản vẫn áp dụng).

---

## 3. Danh sách Thực thể & Trạng thái CRUD

| Thực thể             | Table Component        | Status        | CRUD Cần Bổ sung           |
| :------------------- | :--------------------- | :------------ | :------------------------- |
| **Sản phẩm**         | `ProductTable.tsx`     | Cần Refactor  | Create, Edit, Delete       |
| **Danh mục**         | `CategoryTable.tsx`    | Cần Refactor  | Create, Edit, Delete       |
| **Khách hàng**       | `CustomerTable.tsx`    | Cần Refactor  | Create, Edit, Delete       |
| **Nhà cung cấp**     | `SupplierTable.tsx`    | Cần Refactor  | Create, Edit, Delete       |
| **Đơn hàng**         | `OrderTable.tsx`       | Cần Refactor  | View Details, Cancel       |
| **Giao dịch**        | `TransactionTable.tsx` | Cần Refactor  | View Details               |
| **Nhân viên**        | `EmployeesPage.tsx`    | Chưa có Table | Create, View, Edit, Delete |
| **Vị trí kho**       | (Mới)                  | Chưa có Table | Create, View, Edit, Delete |
| **Nhật ký kho**      | (Mới)                  | Chưa có Table | View                       |
| **Nhật ký hệ thống** | (Mới)                  | Chưa có Table | View                       |

---

## 4. Tiêu chuẩn Thiết kế (Master Table Pattern)

Tất cả các bảng sau khi refactor PHẢI tuân thủ:

1. **Một `<table>` duy nhất**: Không tách header/body ra 2 thẻ `<Table>` khác nhau.
2. **Sticky Header**: Dùng `sticky top-0 z-20 bg-slate-50` trên `th`.
3. **Width đồng bộ**: Sử dụng các constant từ `lib/data-table-layout.ts`.
4. **Cột Thao tác (Action)**:
   - Sticky bên phải (`right-0`).
   - Shadow khi cuộn ngang.
   - Chiều rộng chuẩn (`w-[168px]` cho 3 nút, `w-[96px]` cho 1 nút).
5. **Responsive**:
   - Desktop/Tablet ngang: Dạng bảng đầy đủ.
   - Mobile: Dạng Card List.
6. **Optimistic Updates**: Dùng TanStack Query cho các lệnh Xóa/Sửa.

---

## 5. Acceptance Criteria (BDD/Gherkin)

### 5.1 AC01: Chuẩn hóa Table Layout

```gherkin
Given Tôi đang ở trang Danh sách Sản phẩm/Khách hàng/NCC
When Tôi cuộn bảng theo chiều dọc
Then Header của bảng phải luôn hiển thị (sticky)
And Header và Body phải luôn thẳng hàng (cùng width)
```

### 5.2 AC02: Sticky Action Column

```gherkin
Given Tôi đang xem bảng trên màn hình tablet hẹp
When Tôi cuộn bảng theo chiều ngang
Then Cột "Thao tác" (NV) phải luôn hiển thị ở bên phải màn hình
And Có shadow ngăn cách cột Thao tác với dữ liệu đang cuộn
```

**Loại bỏ thanh cuộn ngang, các cột phải có kích thước thích hợp sao cho phù hợp với 1 khung hình window. Không cần phải có thanh cuộn ngang**

### 5.3 AC03: CRUD Completeness

```gherkin
Given Tôi là Owner
When Tôi vào bất kỳ module quản lý nào (Sản phẩm, Khách hàng...)
Then Tôi phải thấy nút "Thêm mới" ở đầu trang
And Mỗi dòng dữ liệu phải có nút "Sửa" và "Xóa"
And Hành động Xóa phải có Dialog xác nhận "Human-in-the-Loop"
```

---

## 6. Technical Mapping

### 6.1 Token Width Mới (Cần bổ sung vào `data-table-layout.ts`)

- `CUSTOMER_TABLE_COL`: `select`, `code`, `name`, `phone`, `email`, `loyalty`, `spending`, `orders`, `status`.
- `SUPPLIER_TABLE_COL`: `select`, `code`, `name`, `contact`, `email`, `address`, `status`.
- `ORDER_TABLE_COL`: `select`, `code`, `customer`, `date`, `items`, `total`, `payment`, `status`.
- `USER_TABLE_COL`: `select`, `avatar`, `name`, `role`, `email`, `phone`, `status`.

---

## 7. Kế Hoạch Thực Hiện (Agent Workflow)

1. **BA**: Hoàn thiện SRS (file này) và chờ Approve.
2. **PM**:
   - Cấp phát Task043 (UNIT), Task044 (FEATURE), Task045 (E2E).
   - Tách nhỏ các task theo từng cụm (Product Management, Finance, Settings).
3. **TECH_LEAD**: Kiểm tra tính đồng bộ của `data-table-layout.ts`.
4. **DEV**:
   - Red: Viết test cho các tính năng CRUD mới.
   - Green: Implement refactor layout và logic CRUD.
5. **CODEBASE_ANALYST**: Kiểm tra sự chồng chéo logic giữa các feature.
6. **DOC_SYNC**: Cập nhật `FUNCTIONAL_SUMMARY.md`.

---

## 8. QA Checklist (Dành cho BA)

- [ ] Toàn bộ 24 bảng DB đã được scan và ánh xạ?
- [ ] Quy tắc Master Table Pattern được dẫn chiếu đúng?
- [ ] Chức năng Xóa có Confirm Dialog?
- [ ] 100% Tiếng Việt?
- [ ] Mobile-first card list được yêu cầu?

---

> **Gate G0**: Output BA đạt QA nội bộ. Sẵn sàng trình Owner duyệt.
