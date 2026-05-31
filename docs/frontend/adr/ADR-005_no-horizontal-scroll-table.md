# ADR-005: Loại bỏ thanh cuộn ngang cho Table Layout danh sách

**Status: Proposed**
**Date: 18/04/2026**
**Deciders: Agent TECH_LEAD, Owner**

## Context

Hiện tại, `Master Table Pattern` quy định `min-width: 1024px` cho thẻ `Table`, dẫn đến việc xuất hiện thanh cuộn ngang trên các màn hình nhỏ hơn 1024px hoặc khi trình duyệt không mở toàn màn hình. Owner yêu cầu loại bỏ thanh cuộn ngang này, đảm bảo bảng luôn khớp với 1 khung hình window và các cột có kích thước thích hợp.

## Decision

1. **Loại bỏ `min-width` cố định**: Gỡ bỏ `min-w-[1024px]` khỏi `DATA_TABLE_ROOT_CLASS` trong `data-table-layout.ts`.
2. **Cấu trúc Width linh hoạt**:
   - Các cột mã hiệu, ngày tháng, trạng thái: Giữ nguyên width pixel cố định (vừa đủ dùng).
   - Các cột mô tả dài (Tên, Email, Địa chỉ): Chuyển sang `min-width` tối thiểu nhưng cho phép co giãn linh hoạt (`flex-1` logic trong context của table).
   - Sử dụng `truncate` cho toàn bộ các text dài để tránh làm vỡ layout dòng.
3. **Cột Thao tác (Action/NV)**:
   - Tiếp tục giữ `sticky right-0` để đảm bảo luôn truy cập được actions.
   - Giảm shadow nếu bảng không có overflow (vì không còn cuộn ngang).
4. **Responsive Strategy**: Khi màn hình quá hẹp (< 768px), bắt buộc chuyển sang Card List vì không thể hiển thị nhiều cột theo chiều ngang mà vẫn đảm bảo tính thẩm mỹ.

## Consequences

- **Tích cực**: Trải nghiệm người dùng liền mạch hơn, không cần thao tác cuộn ngang trên các màn hình tiêu chuẩn.
- **Tiêu cực**: Các cột tên dài sẽ bị cắt bớt (truncate) nhiều hơn. Cần công cụ Tooltip để xem đầy đủ nội dung khi hover.
- **Rủi ro**: Nếu thực thể có quá nhiều cột quan trọng (> 8 cột), giao diện sẽ trở nên chật chội. Cần ưu tiên ẩn các cột ít quan trọng trên màn hình nhỏ.

## NFR Compliance (5 NFRs)
- **Usability**: Tăng tính tập trung, không bị phân tâm bởi thao tác cuộn.
- **Maintainability**: Centralized tokens trong `data-table-layout.ts` giúp quản lý width dễ dàng.
- **Performance**: Giảm thiểu tính toán layout của browser do không có overflow phức tạp.
- **Reliability**: Layout ổn định trên đa dạng kích thước cửa sổ.
- **Accessibility**: Touch targets vẫn được đảm bảo ≥ 44px.
