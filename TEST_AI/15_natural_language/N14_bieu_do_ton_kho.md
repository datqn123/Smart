# Test Result — N14: Biểu đồ tồn kho

## Thông tin
- **Câu hỏi:** Cho mình xem biểu đồ tồn kho theo nhóm hàng
- **Nhóm:** natural_language
- **Intent dự kiến:** `system_data_chart`
- **Ngày test:** 17/05/2026 21:23:09
- **Thời gian phản hồi:** 10727ms
- **Trạng thái:** ✅ Pass

## Response từ AI
**Trả lời:**

Biểu đồ dạng bánh (pie) thể hiện tồn kho theo nhóm hàng. Đồ uống chiếm tỷ lệ cao nhất với 350 đơn vị, tiếp theo là Thực phẩm khô với 126 đơn vị, Hóa phẩm với 22 đơn vị, Đồ ăn liền với 18 đơn vị, Bánh kẹo với 7 đơn vị và Gia vị với 3 đơn vị.

Bạn có thể thử:
- So sánh tồn kho của từng nhóm hàng với mức tồn kho tối thiểu để xác định nhóm hàng nào cần bổ sung hàng hóa.
- Phân tích xu hướng tồn kho của từng nhóm hàng trong một khoảng thời gian nhất định để dự báo nhu cầu hàng hóa.
- Tìm hiểu nguyên nhân của sự chênh lệch lớn giữa tồn kho của nhóm hàng Đồ uống và các nhóm hàng khác.

**Chart spec:**

```json
{
  "chartType": "pie",
  "xKey": "group_name",
  "series": [
    {
      "dataKey": "total_stock",
      "name": "Tồn kho theo nhóm hàng"
    }
  ],
  "title": "Tồn kho theo nhóm hàng",
  "data": [
    {
      "group_name": "Đồ uống",
      "total_stock": 350
    },
    {
      "group_name": "Thực phẩm khô",
      "total_stock": 126
    },
    {
      "group_name": "Hóa phẩm",
      "total_stock": 22
    },
    {
      "group_name": "Đồ ăn liền",
      "total_stock": 18
    },
    {
      "group_name": "Bánh kẹo",
      "total_stock": 7
    },
    {
      "group_name": "Gia vị",
      "total_stock": 3
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
