# Test Result — Q11: Tồn theo vị trí

## Thông tin
- **Câu hỏi:** Tồn kho của sản phẩm có SKU là SP0001 ở những vị trí nào?
- **Nhóm:** system_data_query (inventory)
- **Intent dự kiến:** `system_data_query`
- **Ngày test:** 17/05/2026 17:33:22
- **Thời gian phản hồi:** 8396ms
- **Trạng thái:** ✅ Pass

## Response từ AI
**Trả lời:**

Không tìm thấy dữ liệu tồn kho cho SKU SP0001. Có thể do: (1) SKU này chưa được nhập kho, (2) đã hết tồn, hoặc (3) có lỗi nhập liệu. Bạn có thể thử:

- Kiểm tra lại SKU có chính xác không, - Tìm sản phẩm gần giống với SP0001, - Kiểm tra xem sản phẩm này có tồn ở các kho khác không.



## Kiểm tra
- [ ] Intent đúng với dự kiến
- [ ] Response không rỗng
- [ ] Nội dung liên quan đến câu hỏi
- [ ] Không hallucination/bịa số liệu

## Ghi chú
- **Bảng liên quan:** inventory, products, warehouselocations

