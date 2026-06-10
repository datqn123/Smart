# Test Result — Q23: Retail đã paid

## Thông tin
- **Câu hỏi:** Tổng doanh thu từ các đơn bán lẻ (Retail) đã thanh toán (Paid)?
- **Nhóm:** system_data_query (sales_orders)
- **Intent dự kiến:** `system_data_query`
- **Ngày test:** 17/05/2026 17:34:47
- **Thời gian phản hồi:** 5010ms
- **Trạng thái:** ✅ Pass

## Response từ AI
**Trả lời:**

Hiện không tính được tổng doanh thu từ đơn bán lẻ đã thanh toán (trong tháng này). Thường do không có dòng tồn khớp JOIN hoặc chưa có giá vốn `productpricehistory` cho đơn vị cơ sở (`productunits.is_base_unit = TRUE`).



## Kiểm tra
- [ ] Intent đúng với dự kiến
- [ ] Response không rỗng
- [ ] Nội dung liên quan đến câu hỏi
- [ ] Không hallucination/bịa số liệu

## Ghi chú
- **Bảng liên quan:** salesorders

