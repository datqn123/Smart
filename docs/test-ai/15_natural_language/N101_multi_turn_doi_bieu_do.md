# Test Result — N101: Multi-turn đổi loại biểu đồ

## Thông tin
- **Câu hỏi:** Chuyển sang biểu đồ cột được không?
- **Nhóm:** natural_language
- **Intent dự kiến:** `system_data_chart`
- **Ngày test:** 17/05/2026 21:09:54
- **Thời gian phản hồi:** 11027ms
- **Trạng thái:** ✅ Pass

## Response từ AI
**Trả lời:**

Biểu đồ cột thể hiện doanh thu qua các tháng: Tháng 4 - 353.700, Tháng 3 - 750.000. Bạn có thể thử thêm các tháng khác vào biểu đồ hoặc so sánh với các chỉ tiêu khác như lợi nhuận, số lượng sản phẩm bán ra.

**Chart spec:**

```json
{
  "chartType": "bar",
  "xKey": "month",
  "series": [
    {
      "dataKey": "revenue",
      "name": "Giá trị"
    }
  ],
  "title": "",
  "data": [
    {
      "month": "01/05/2026 00:00:00",
      "revenue": 353700.0
    },
    {
      "month": "01/04/2026 00:00:00",
      "revenue": 750000.0
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
