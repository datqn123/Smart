# Test Result — Q10: Giá trị tồn kho

## Thông tin
- **Câu hỏi:** Tổng giá trị tồn kho hiện tại là bao nhiêu?
- **Nhóm:** system_data_query (inventory)
- **Intent dự kiến:** `system_data_query`
- **Ngày test:** 17/05/2026 17:33:13
- **Thời gian phản hồi:** 3996ms
- **Trạng thái:** ✅ Pass

## Response từ AI
**Trả lời:**

Tổng giá trị tồn kho hiện tại là **30.554.000** (theo kết quả truy vấn SQL, bám đúng số liệu hệ thống).

Chỉ số này phản ánh tổng **số lượng tồn × giá vốn đơn vị cơ sở** (giá lấy từ lịch sử giá theo đơn vị `is_base_unit = TRUE`).

Bạn có thể hỏi tiếp, ví dụ:

- Tồn kho SKU cụ thể ở những vị trí nào?
- Sản phẩm nào có giá trị tồn cao nhất?
- Có bao nhiêu mặt hàng sắp hết hàng?



## Kiểm tra
- [ ] Intent đúng với dự kiến
- [ ] Response không rỗng
- [ ] Nội dung liên quan đến câu hỏi
- [ ] Không hallucination/bịa số liệu

## Ghi chú
- **Bảng liên quan:** inventory, productpricehistory

