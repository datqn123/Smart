# Test Result — Q55: Giá trị NCC

## Thông tin
- **Câu hỏi:** Tổng giá trị nhập hàng từ nhà cung cấp có mã NCC0001?
- **Nhóm:** system_data_query (suppliers)
- **Intent dự kiến:** `system_data_query`
- **Ngày test:** 17/05/2026 17:37:51
- **Thời gian phản hồi:** 5142ms
- **Trạng thái:** ✅ Pass

## Response từ AI
**Trả lời:**

Hiện không tính được tổng giá trị nhập hàng từ nhà cung cấp có mã NCC0001 (kết quả NULL). Thường do không có dòng tồn khớp JOIN hoặc chưa có giá vốn `productpricehistory` cho đơn vị cơ sở (`productunits.is_base_unit = TRUE`).



## Kiểm tra
- [ ] Intent đúng với dự kiến
- [ ] Response không rỗng
- [ ] Nội dung liên quan đến câu hỏi
- [ ] Không hallucination/bịa số liệu

## Ghi chú
- **Bảng liên quan:** stockreceipts, suppliers

