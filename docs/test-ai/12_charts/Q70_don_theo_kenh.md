# Test Result — Q70: Đơn theo kênh

## Thông tin
- **Câu hỏi:** Biểu đồ tròn phân bổ đơn hàng theo kênh bán
- **Nhóm:** system_data_chart (pie)
- **Intent dự kiến:** `system_data_chart`
- **Ngày test:** 17/05/2026 17:39:39
- **Thời gian phản hồi:** 7523ms
- **Trạng thái:** ✅ Pass

## Response từ AI
**Trả lời:**

Biểu đồ tròn thể hiện phân bổ đơn hàng theo kênh bán. Kênh Wholesale chiếm 87,0%, Retail chiếm 13,0%. Điều này cho thấy phần lớn đơn hàng đến từ kênh bán sỉ. Bạn có thể thử tăng cường chiến lược bán lẻ để cải thiện doanh số từ kênh này.

**Chart spec:**

```json
{
  "chartType": "pie",
  "xKey": "order_channel",
  "series": [
    {
      "dataKey": "total_orders",
      "name": "Giá trị"
    }
  ],
  "title": "",
  "data": [
    {
      "order_channel": "Wholesale",
      "total_orders": 60
    },
    {
      "order_channel": "Retail",
      "total_orders": 9
    }
  ]
}
```



## Kiểm tra
- [ ] Intent đúng với dự kiến
- [ ] Response không rỗng
- [ ] Nội dung liên quan đến câu hỏi
- [ ] Không hallucination/bịa số liệu
- [ ] (chart) Có chart_spec hợp lệ

## Ghi chú
- **Bảng liên quan:** salesorders

