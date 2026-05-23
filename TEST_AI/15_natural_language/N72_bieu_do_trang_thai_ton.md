# Test Result — N72: Hỏi về biểu đồ trạng thái tồn kho

## Thông tin
- **Câu hỏi:** Cho mình xem biểu đồ cột hàng tồn theo trạng thái
- **Nhóm:** natural_language
- **Intent dự kiến:** `system_data_chart`
- **Ngày test:** 17/05/2026 21:32:15
- **Thời gian phản hồi:** 14122ms
- **Trạng thái:** ✅ Pass

## Response từ AI
**Trả lời:**

Dữ liệu chỉ có 1 trạng thái 'Active' với số lượng 65. Không đủ dữ liệu để vẽ biểu đồ tròn.

Để có biểu đồ cột hàng tồn kho theo trạng thái, bạn cần có dữ liệu về nhiều trạng thái khác nhau như 'Hết hạn', 'Bảo hành', 'Đang đặt hàng', v.v. Bạn có thể thử hỏi lại với câu lệnh SQL đã được sửa đổi để lấy dữ liệu từ bảng 'Inventory' và 'Status' với các điều kiện cụ thể.

**Chart spec:**

```json
{
  "chartType": "pie",
  "xKey": "status",
  "series": [
    {
      "dataKey": "quantity",
      "name": "Giá trị"
    }
  ],
  "title": "",
  "data": [
    {
      "status": "Active",
      "quantity": 65
    }
  ]
}
```


## Kiểm tra
- [ ] Intent đúng với dự kiến
- [ ] Response không rỗng
- [ ] Nội dung liên quan đến câu hỏi
- [ ] Không hallucination/bịa số liệu

## Ghi chú
