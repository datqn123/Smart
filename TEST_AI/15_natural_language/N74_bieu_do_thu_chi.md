# Test Result — N74: Hỏi về biểu đồ doanh thu chi phí

## Thông tin
- **Câu hỏi:** Vẽ cho mình biểu đồ doanh thu và chi phí theo từng tháng
- **Nhóm:** natural_language
- **Intent dự kiến:** `system_data_chart`
- **Ngày test:** 17/05/2026 21:32:32
- **Thời gian phản hồi:** 10689ms
- **Trạng thái:** ✅ Pass

## Response từ AI
**Trả lời:**

Biểu đồ cột thể hiện tổng doanh thu và chi phí theo tháng với 2 tháng trong năm 2026. Biểu đồ này giúp bạn dễ dàng so sánh và phân tích xu hướng doanh thu và chi phí qua từng tháng. Bạn có thể thử thêm các tháng khác vào biểu đồ để có cái nhìn toàn diện hơn về tình hình tài chính của doanh nghiệp. Ngoài ra, bạn cũng có thể thử tạo biểu đồ đường để xem xu hướng thay đổi của doanh thu và chi phí theo thời gian.

**Chart spec:**

```json
{
  "chartType": "bar",
  "xKey": "month",
  "series": [
    {
      "dataKey": "revenue",
      "name": "Biểu đồ cột tổng doanh thu và chi phí theo tháng"
    }
  ],
  "title": "Biểu đồ cột tổng doanh thu và chi phí theo tháng",
  "data": [
    {
      "month": "01/04/2026 00:00:00",
      "revenue": 750000.0
    },
    {
      "month": "01/05/2026 00:00:00",
      "revenue": 353700.0
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
