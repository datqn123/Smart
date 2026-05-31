# ELCITATION SUMMARY - CRUD Phiếu Nhập Kho & Xuất Kho

> **File**: `docs/ba/elicitation/ELICITATION_Task039_inbound-dispatch-crud.md`
> **Người viết**: Agent BA
> **Ngày tạo**: 18/04/2026
> **Phiên bản**: 1.0
> **Trạng thái**: Approved ✅ (Đã xác nhận bởi User)
> **Nguồn**: Phân tích code hiện tại từ InboundPage.tsx và DispatchPage.tsx

---

## 1. Tóm tắt Yêu cầu (Executive Summary)

### 1.1 Bối cảnh

- **Nguồn yêu cầu**: Phân tích code hiện tại của `InboundPage.tsx` và `DispatchPage.tsx` trong `mini-erp/src/features/inventory/pages/`
- **Vấn đề**: Giao diện Danh sách (Table) đã có, nhưng thiếu các chức năng CRUD đầy đủ:
  - Chỉ có Read (xem danh sách + chi tiết)
  - Button "Tạo mới" chỉ hiện `alert()` chưa có logic
  - Chưa có Update/Selete/Workflow actions

### 1.2 Mục tiêu Elicitation

Xác định đầy đủ các chức năng CRUD cần triển khai cho:

1. **Phiếu Nhập Kho (Inbound)** - Workflow: Draft → Pending → Approved/Rejected
2. **Phiếu Xuất Kho (Dispatch)** - Workflow: Pending → Full/Partial → Backorder

---

## 2. Thông tin Hiện trạng (AS-IS Analysis)

### 2.1 Phiếu Nhập Kho (Inbound)

| Chức năng     | Trạng thái   | Ghi chú                          |
| ------------- | ------------ | -------------------------------- |
| Xem danh sách | ✅ Có        | Table + Infinite Scroll          |
| Xem chi tiết  | ✅ Có        | ReceiptDetailPanel (Sheet)       |
| Tạo mới       | ⚠️ Button có | Chỉ `alert("Form tạo phiếu...")` |
| Sửa           | ❌ Chưa      |                                  |
| Xóa           | ❌ Chưa      |                                  |
| Gửi phê duyệt | ❌ Chưa      |                                  |
| Phê duyệt     | ⚠️ UI có     | `canApprove={true}` hardcoded    |
| Từ chối       | ❌ Chưa      |                                  |
| Export/Import | ⚠️ Button có | Chỉ `alert()`                    |
| Scan OCR      | ⚠️ Button có |                                  |

### 2.2 Phiếu Xuất Kho (Dispatch)

| Chức năng         | Trạng thái   | Ghi chú                     |
| ----------------- | ------------ | --------------------------- |
| Xem danh sách     | ✅ Có        | Table + Infinite Scroll     |
| Xem chi tiết      | ✅ Có        | DispatchDetailPanel (Sheet) |
| Tạo mới           | ⚠️ Button có | Chỉ `alert("Form tạo...")`  |
| Sửa số lượng      | ❌ Chưa      |                             |
| Xác nhận xuất     | ❌ Chưa      |                             |
| Xem Picking List  | ❌ Chưa      |                             |
| Hủy phiếu         | ❌ Chưa      |                             |
| Export/Import     | ⚠️ Button có | Chỉ `alert()`               |
| Partial/Backorder | ❌ Chưa      |                             |

### 2.3 Data Models Hiện tại

```typescript
// StockReceipt (Inbound)
interface StockReceipt {
  id: number;
  receiptCode: string; // PN-2026-0001
  supplierId: number;
  supplierName: string;
  staffId: number;
  staffName: string;
  receiptDate: string;
  status: "Draft" | "Pending" | "Approved" | "Rejected";
  invoiceNumber?: string;
  totalAmount: number;
  notes?: string;
  approvedBy?: number;
  approvedByName?: string;
  approvedAt?: string;
  createdAt: string;
  updatedAt: string;
  details: ReceiptDetailItem[];
}

// StockDispatch (Dispatch)
interface StockDispatch {
  id: number;
  dispatchCode: string; // PX-2026-0001
  orderId: number;
  orderCode: string;
  customerName: string;
  userId: number;
  userName: string;
  dispatchDate: string;
  status: "Pending" | "Full" | "Partial" | "Cancelled";
  notes?: string;
  createdAt: string;
  updatedAt: string;
  items: DispatchItem[];
}
```

---

## 3. Các Câu hỏi Elicitation (Q&A)

### Q1: Workflow Phê duyệt

**Câu hỏi**: Đối với Phiếu Nhập Kho, khi Owner phê duyệt thì có cần:

- Tự động cập nhật Inventory (tăng tồn kho)? Có
- Tự động tạo FinanceLedger entry? Có
- Gửi thông báo cho Staff đã tạo phiếu? Có

**Trả lời kỳ vọng**: Đây là nghiệp vụ quan trọng, cần Human-in-the-Loop confirm trước khi commit DB.

---

### Q2: Số lượng Xuất

**Câu hỏi**: Đối với Phiếu Xuất Kho:

- Khi xác nhận xuất kho, có trừ tồn kho ngay lập tức không? Có
- Có tạo Backorder tự động khi `dispatchQty < remainingQty` không? Có
- Picking List có cần hiển thị vị trí kho (warehouse + shelf) không? Có

**Trả lời kỳ vọng**: Cần theo nghiệp vụ thực tế - trừ tồn kho ngay khi xuất.

---

### Q3: Quyền hạn (RBAC)

**Câu hỏi**: Phân quyền chi tiết:

- Staff có được phép xóa phiếu Draft không? Như kỳ vọng
- Staff có được phép sửa phiếu Pending không? Như kỳ vọng
- Owner có được phép sửa phiếu Approved không? Như kỳ vọng

**Trả lời kỳ vọng**:

- Staff: Tạo/Sửa/Xóa Draft, Gửi phê duyệt, Xác nhận xuất
- Owner: Phê duyệt/Từ chối, Xem tất cả, Hủy phiếu

---

## 4. Gap Analysis (Khoảng trống cần lấp)

### 4.1 Phổ biến

| Gap                         | Module           | Priority  | Ảnh hưởng                    |
| --------------------------- | ---------------- | --------- | ---------------------------- |
| Không tạo được phiếu mới    | Inbound/Dispatch | 🔴 High   | Không thể nhập/xuất kho      |
| Không sửa được phiếu Draft  | Inbound          | 🔴 High   | Dữ liệu sai phải tạo mới     |
| Không xóa được phiếu Draft  | Inbound          | 🟡 Medium | Phiếu lỗi không xóa được     |
| Không gửi phê duyệt         | Inbound          | 🔴 High   | Không có workflow            |
| Không phê duyệt/từ chối     | Inbound          | 🔴 High   | Không có workflow            |
| Không xác nhận xuất         | Dispatch         | 🔴 High   | Không trừ tồn kho            |
| Không hiển thị Picking List | Dispatch         | 🟡 Medium | NV không biết lấy hàng ở đâu |

### 4.2 Kết luận Gap

**Cần triển khai đầy đủ các tính năng CRUD + Workflow cho cả 2 module.**

---

## 5. Stakeholder Requirements

| Stakeholder | Requirement                                      |
| ----------- | ------------------------------------------------ |
| **Owner**   | Xem và phê duyệt phiếu nhập, xem báo cáo tồn kho |
| **Staff**   | Tạo/sửa phiếu, giao hàng, cập nhật tồn kho       |
| **Kế toán** | Xem các khoản chi phí nhập hàng                  |

---

## 6. Input cho Bước Tiếp theo (PRD)

Sau khi Elicitation hoàn thành, cần tạo:

- **PRD**: Xác định đầy đủ In-scope/Out-of-scope
- **User Stories**: Cho từng tính năng CRUD
- **SRS**: Đặc tả kỹ thuật

---

## 7. Next Steps

- [ ] Review Elicitation Summary này
- [ ] Chuyển sang **Trụ 2: Gap Analysis & PRD**
- [ ] Tạo PRD với đầy đủ Use Cases
- [ ] Xác định ERD bị ảnh hưởng
- [ ] Tạo User Story Specs
- [ ] Tạo SRS

---

> **Status**: ✅ Elicitation Complete - Ready for PRD
