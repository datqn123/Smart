# Test Result — N08: Vẽ biểu đồ doanh thu

## Thông tin
- **Câu hỏi:** Vẽ cho mình cái biểu đồ doanh thu mấy tháng gần đây
- **Nhóm:** natural_language
- **Intent dự kiến:** `system_data_chart`
- **Ngày test:** 17/05/2026 21:09:28
- **Thời gian phản hồi:** 10559ms
- **Trạng thái:** ✅ Pass

## Response từ AI
**Trả lời:**

Dữ liệu biểu đồ doanh thu chỉ có thông tin cho tháng 4 năm 2026 với giá trị 353.700. Điều này cho thấy dữ liệu chưa đầy đủ để phân tích xu hướng doanh thu qua nhiều tháng. Bạn có thể thử yêu cầu dữ liệu cho các tháng khác hoặc kiểm tra lại nguồn dữ liệu để đảm bảo có đầy đủ thông tin cần thiết.

**Chart spec:**

```json
{
  "chartType": "bar",
  "xKey": "month",
  "series": [
    {
      "dataKey": "total_revenue",
      "name": "Giá trị"
    }
  ],
  "title": "",
  "data": [
    {
      "month": "01/05/2026 00:00:00",
      "total_revenue": 353700.0
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
