# SRS - Stock Interface Functional Implementation

> **File**: `docs/srs/SRS_Task017_stock-interface-functional-implementation.md`
> **Người viết**: Agent BA
> **Ngày tạo**: 26/04/2026
> **Phiên bản**: 1.0
> **Trạng thái**: Completed ✅
> **Task**: Task017

---

## 1. Tóm tắt

- **Vấn đề**: Giao diện quản lý phiếu nhập kho hiện tại chỉ có Read (xem danh sách), chưa có khả năng tạo, sửa, xóa, gửi duyệt, phê duyệt/từ chối trên UI.
- **Mục tiêu**: Implement đầy đủ UI CRUD + workflow phê duyệt cho phiếu nhập kho (stock receipts) — bao gồm nút xóa, submit, approve, reject và form tạo/sửa.
- **Đối tượng**: Owner (xóa, phê duyệt, từ chối), Staff (tạo, sửa Draft, submit).

---

## 2. Phạm vi

### 2.1 In-scope

- Nút "Xóa phiếu" trên ReceiptTable (chỉ Owner, chỉ Draft/Pending)
- Nút "Gửi duyệt" — Draft → Pending
- Nút "Phê duyệt" / "Từ chối" trên DetailPanel (chỉ Owner, chỉ Pending)
- Form tạo/sửa phiếu nhập (Draft)
- Confirm dialog trước các hành động xóa, approve, reject
- Toast thông báo kết quả
- TanStack Query cache invalidation sau mutation
- RBAC — ẩn nút nếu không đủ quyền

### 2.2 Out-of-scope

- Tính năng xuất kho (Dispatch) — Task039
- OCR, notifications
- Báo cáo

---

## 3. Persona & Quyền (RBAC)

| Hành động | Owner | Staff |
| :--- | :---: | :---: |
| Tạo phiếu mới | ✅ | ✅ |
| Sửa phiếu Draft | ✅ | ✅ (chỉ phiếu mình tạo) |
| Xóa phiếu (Draft/Pending) | ✅ | ❌ |
| Gửi duyệt (Draft → Pending) | ✅ | ✅ (chỉ phiếu mình tạo) |
| Phê duyệt (Pending → Approved) | ✅ | ❌ |
| Từ chối (Pending → Rejected) | ✅ | ❌ |

---

## 4. User Stories

- **US1**: Là một Owner, tôi muốn xóa phiếu nhập (Draft/Pending) để loại bỏ phiếu không hợp lệ.
- **US2**: Là một Staff, tôi muốn gửi phiếu nhập lên Owner duyệt để cập nhật tồn kho.
- **US3**: Là một Owner, tôi muốn phê duyệt/từ chối phiếu nhập để kiểm soát hàng nhập.

---

## 5. Business Flow

```mermaid
flowchart TD
    List([Dashboard/List]) --> Select[Chọn phiếu]
    Select --> Detail[DetailPanel]
    Detail -->|Owner + Draft/Pending| Delete{Delete?}
    Detail -->|Owner + Pending| Approve{Approve/Reject?}
    Detail -->|Draft| Submit{Submit?}
    Delete -->|Confirm| Deleted[Toast: "Đã xóa"]
    Delete -->|Cancel| Detail
    Approve -->|Approve| Approved[Toast + Refresh]
    Approve -->|Reject| Rejected[Toast + Refresh]
    Submit -->|Confirm| Submitted[Toast + Refresh]
```

---

## 6. Acceptance Criteria (BDD/Gherkin)

### 6.1 Happy paths

```gherkin
Given User là Owner
And Phiếu nhập có status = "Draft"
When Click nút "Xóa phiếu"
And Xác nhận trong dialog
Then Phiếu bị xóa khỏi DB
And Hiển thị toast "Đã xóa phiếu nhập kho"
And Danh sách refresh

Given User là Owner
And Phiếu nhập có status = "Pending"
When Click nút "Phê duyệt"
And Xác nhận trong dialog
Then Status đổi thành "Approved"
And Inventory tăng
And Toast "Phê duyệt thành công"

Given User là Owner
And Phiếu nhập có status = "Pending"
When Click nút "Từ chối"
And Nhập lý do từ chối
Then Status đổi thành "Rejected"
And Toast "Từ chối phiếu nhập"
```

### 6.2 Unhappy paths

```gherkin
Given User là Staff
And Phiếu nhập có status = "Draft"
When Click nút "Xóa phiếu"
Then Nút bị ẩn (invisible)
And Không thể xóa

Given User là Staff
And Phiếu nhập có status = "Pending"
When Click nút "Phê duyệt"
Then Nút bị ẩn
And Toast "Bạn không có quyền"

Given Phiếu nhập đã "Approved"
When Click nút "Xóa phiếu"
Then API trả 409
And Toast "Chỉ được xóa phiếu ở trạng thái Nháp"
```

---

## 7. UI/UX Spec

### 7.1 Layout

- **Desktop**: Table + Detail Panel (Sheet) bên phải
- **Mobile/Tablet**: Card view, Sheet full màn hình

### 7.2 Components

- `ReceiptTable.tsx` — bảng danh sách, cột Actions chứa nút xóa
- `ReceiptDetailPanel.tsx` — Sheet chi tiết, chứa action buttons
- `Button` (Shadcn) — với variant `ghost`/`destructive`
- `Dialog` (Shadcn) — confirm dialog trước khi xóa
- `Toast` (Sonner) — thông báo kết quả

### 7.3 States

| State | UI |
|-------|-----|
| Loading | Skeleton rows |
| Empty | EmptyState "Chưa có phiếu nhập" |
| Error | Toast + retry |
| Submitting | Loading state trên button |

---

## 8. Technical Mapping

- **Route**: `/inventory/inbound`
- **Pages**: `InboundPage.tsx`
- **Components**: `ReceiptTable.tsx`, `ReceiptDetailPanel.tsx`
- **API**: `stockReceiptsApi.ts` — `deleteStockReceipt(id)`
- **State**:
  - Server: TanStack Query v5 (key `["stock-receipts", "v1", "list"]`)
  - Form: React Hook Form + Zod

---

## 9. Data & Database Mapping

- **Bảng ảnh hưởng**: `stock_receipts`, `stock_receipt_details`, `system_logs`
- **Transaction**: DELETE cascade details, insert system log
- **Audit**: `SystemLogs` (INFO, INVENTORY, DELETE)

---

## 10. Open Questions

- [x] Xóa Pending? — **Có**, PO đã chốt OQ-1 (cho phép xóa cả Pending)

---

> **Status**: ✅ SRS Complete
