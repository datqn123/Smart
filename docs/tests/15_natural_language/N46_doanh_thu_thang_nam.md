# Test Result — N46: Doanh thu năm nay theo tháng

## Thông tin
- **Câu hỏi:** Mỗi tháng năm nay mình bán được bao nhiêu?
- **Nhóm:** natural_language
- **Intent dự kiến:** `system_data_query`
- **Ngày test:** 17/05/2026 21:29:15
- **Thời gian phản hồi:** 17444ms
- **Trạng thái:** ✅ Pass

## Response từ AI
**Trả lời:**

Dựa trên dữ liệu đã có, chỉ có thông tin về tháng 05-2026 với số lượng bán được là 453700. Các tháng khác không có thông tin cụ thể. Bạn có thể thử tìm kiếm thông tin về các tháng còn lại hoặc kiểm tra lại nguồn dữ liệu để có được thông tin đầy đủ hơn.

**Chart spec:**

```json
{
  "chartType": "line",
  "xKey": "month",
  "series": [
    {
      "dataKey": "metric_value",
      "name": "Số lượng bán được mỗi tháng năm nay"
    }
  ],
  "title": "Số lượng bán được mỗi tháng năm nay",
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
      "metric_value": 0.0
    },
    {
      "month": "2026-04-01",
      "metric_value": 0.0
    },
    {
      "month": "2026-05-01",
      "metric_value": 453700.0
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
