# Test Result — Q69: Công nợ tháng

## Thông tin
- **Câu hỏi:** Vẽ biểu đồ đường xu hướng công nợ theo tháng
- **Nhóm:** system_data_chart (line)
- **Intent dự kiến:** `system_data_chart`
- **Ngày test:** 17/05/2026 17:39:31
- **Thời gian phản hồi:** 9437ms
- **Trạng thái:** ✅ Pass

## Response từ AI
**Trả lời:**

Biểu đồ đường thể hiện xu hướng công nợ theo tháng cho thấy giá trị công nợ không đổi là 0 trong suốt các tháng từ tháng 1 đến tháng 5 năm 2026. Điều này có nghĩa là trong khoảng thời gian này, không có công nợ nào được ghi nhận. Bạn có thể thử phân tích dữ liệu công nợ theo quý hoặc năm để có cái nhìn tổng quan hơn về tình hình công nợ của doanh nghiệp.

**Chart spec:**

```json
{
  "chartType": "line",
  "xKey": "month",
  "series": [
    {
      "dataKey": "metric_value",
      "name": "Xu hướng công nợ theo tháng"
    }
  ],
  "title": "Xu hướng công nợ theo tháng",
  "data": [
    {
      "month": "2026-01-01",
      "metric_value": 0
    },
    {
      "month": "2026-02-01",
      "metric_value": 0
    },
    {
      "month": "2026-03-01",
      "metric_value": 0
    },
    {
      "month": "2026-04-01",
      "metric_value": 0
    },
    {
      "month": "2026-05-01",
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
- **Bảng liên quan:** partnerdebts

