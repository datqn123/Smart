# ELICITATION SUMMARY — Task025: Nâng cấp giao diện Phiếu nhập kho (Dạng bảng)

> **File**: `docs/ba/elicitation/ELICITATION_Task025_inbound-table-layout.md`
> **Ngày**: 16/04/2026
> **Trạng thái**: Hoàn thành (yêu cầu đủ rõ — bỏ qua Q&A loop)

---

## 1. Bối cảnh & Vấn đề hiện tại (AS-IS)

Màn hình Phiếu nhập kho (`/inventory/inbound`) hiện dùng **dạng Card** (ReceiptCard component):
- Mỗi phiếu là một card riêng lẻ → **rời rạc về mặt thị giác**, khó so sánh nhiều phiếu.
- Dữ liệu sơ bộ (mã phiếu, NCC, ngày, trạng thái, tổng tiền) nằm rải rác trong card.
- Xem chi tiết phải click mở rộng từng card (accordion).
- Danh sách dùng infinite scroll (ổn) với scroll container riêng.

**Vấn đề Owner nêu**:
1. Thẻ thông tin "rời rạc so với bố cục giao diện" — cần sự thống nhất, nhất quán với các trang list khác.
2. Muốn chuyển sang **dạng bảng (Table)** để dễ quét thông tin, dễ so sánh.
3. **Header cố định** (sticky header) khi có nhiều dòng và scrollbar ngang/dọc.
4. Khi click hàng/nút → hiển thị **chi tiết** đầy đủ (slide-over hoặc modal).
5. **Bổ sung thêm data** (tăng số lượng mock records để kiểm tra scroll/pagination tốt hơn).

---

## 2. Actor & Role

| Actor | Vai trò | Quyền |
| :--- | :--- | :--- |
| **Staff** | Nhân viên kho | Xem phiếu, tạo phiếu Draft |
| **Owner** | Chủ cửa hàng | Xem tất cả, Approve/Reject phiếu |

---

## 3. Phân tích yêu cầu (MoSCoW)

| Độ ưu tiên | Yêu cầu | Ghi chú |
| :--- | :--- | :--- |
| **MUST** | Chuyển danh sách phiếu sang dạng **Data Table** | Thay thế ReceiptCard list |
| **MUST** | Header cột luôn cố định khi scroll dọc & ngang | Sticky header trong scroll container |
| **MUST** | Scrollbar riêng cho bảng (không ảnh hưởng layout trang) | Như Task022 đã có |
| **MUST** | Click hàng → xem chi tiết phiếu | Panel/modal/slide-over |
| **MUST** | Bổ sung thêm mock data (≥ 30 phiếu) | Để test scroll |
| **SHOULD** | Các cột hiển thị: Mã phiếu, NCC, Ngày nhập, Người tạo, Số hóa đơn, Số dòng SP, Tổng tiền, Trạng thái, Hành động | |
| **SHOULD** | Chi tiết khi xem: thông tin đầy đủ + danh sách sản phẩm (StockReceiptDetails) | |
| **COULD** | Highlight row khi hover | UX |
| **WON'T** | Thay đổi logic filter, sort, infinite scroll | Giữ nguyên Task022 |
| **WON'T** | Thay đổi workflow phê duyệt | Giữ nguyên nghiệp vụ |

---

## 4. Constraints (Ràng buộc)

- Giữ nguyên **scroll container riêng** (đã làm ở Task022).
- Không thay đổi **logic filter, sort, infinite scroll** (`inboundLogic.ts`).
- Không thay đổi **kiểu dữ liệu** `StockReceipt` trong `types.ts`.
- Không tạo bảng DB mới (dùng mock data hiện có + bổ sung).
- Tuân thủ Design System: Shadcn UI components, Tailwind CSS v4, Slate monochrome.
