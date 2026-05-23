# Test Result — Q73a: Doanh thu tháng 3

## Thông tin
- **Câu hỏi:** Doanh thu tháng 3 là bao nhiêu?
- **Nhóm:** multi_turn (thread context)
- **Intent dự kiến:** `system_data_query`
- **Ngày test:** 17/05/2026 17:40:07
- **Thời gian phản hồi:** 6825ms
- **Trạng thái:** ✅ Pass

## Response từ AI
**Trả lời:**

- Hiện không tính được doanh thu tháng 3 (kết quả NULL). Thường do:
 - Không có dòng tồn khớp JOIN với `receipt_detail` và `productpricehistory`
 - Chưa có giá vốn trong `productpricehistory` cho đơn vị cơ sở (`productunits.is_base_unit = TRUE`)
- Ví dụ các trường hợp có thể xảy ra:
 - Sản phẩm A (SKU: A123) có receipt_code R001 nhưng chưa có giá vốn
 - Sản phẩm B (SKU: B456) có receipt_code R002 nhưng không khớp đơn vị cơ sở
- Bạn có thể hỏi:
 - "Có bao nhiêu sản phẩm chưa có giá vốn trong tháng 3?"
 - "Danh sách các receipt_code không khớp với productpricehistory?"



## Kiểm tra
- [ ] Intent đúng với dự kiến
- [ ] Response không rỗng
- [ ] Nội dung liên quan đến câu hỏi
- [ ] Không hallucination/bịa số liệu

## Ghi chú
- **Bảng liên quan:** financeledger

