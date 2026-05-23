# Test Result — Q74a: Biểu đồ doanh thu

## Thông tin
- **Câu hỏi:** Vẽ biểu đồ doanh thu theo tháng
- **Nhóm:** multi_turn (chart type change)
- **Intent dự kiến:** `system_data_chart`
- **Ngày test:** 17/05/2026 17:40:21
- **Thời gian phản hồi:** 10969ms
- **Trạng thái:** ✅ Pass

## Response từ AI
**Trả lời:**

Dựa trên dữ liệu hiện có, biểu đồ sẽ chỉ bao gồm một đường nằm ngang trên trục y tại mức 0 cho cả 4 tháng đầu năm 2025. Điều này cho thấy không có doanh thu nào được ghi nhận trong khoảng thời gian này. Bạn có thể thử hỏi về các tháng khác hoặc các năm khác để có thông tin chi tiết hơn.

**Chart spec:**

```json
{
  "chartType": "line",
  "xKey": "month",
  "series": [
    {
      "dataKey": "metric_value",
      "name": "Biểu đồ doanh thu theo tháng"
    }
  ],
  "title": "Biểu đồ doanh thu theo tháng",
  "data": [
    {
      "month": "2025-01-01",
      "metric_value": 0
    },
    {
      "month": "2025-02-01",
      "metric_value": 0
    },
    {
      "month": "2025-03-01",
      "metric_value": 0
    },
    {
      "month": "2025-04-01",
      "metric_value": 0
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
- **Bảng liên quan:** financeledger

