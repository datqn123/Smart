# Test Result — N81: Hỏi về doanh thu theo quý

## Thông tin
- **Câu hỏi:** Mỗi quý mình bán được bao nhiêu tiền?
- **Nhóm:** natural_language
- **Intent dự kiến:** `system_data_query`
- **Ngày test:** 17/05/2026 21:33:22
- **Thời gian phản hồi:** 11343ms
- **Trạng thái:** ✅ Pass

## Response từ AI
**Trả lời:**

Dựa trên dữ liệu đã cho, quý 4 năm 2025 có tổng doanh thu là 0 đồng, trong khi quý 1 năm 2026 có tổng doanh thu là 453.700 đồng. Điều này cho thấy quý 1 năm 2026 là quý có doanh thu cao hơn so với quý 4 năm 2025. Bạn có thể thử phân tích nguyên nhân của sự chênh lệch này để có thể đưa ra các quyết định kinh doanh phù hợp.

**Chart spec:**

```json
{
  "chartType": "bar",
  "xKey": "quarter",
  "series": [
    {
      "dataKey": "total_revenue",
      "name": "Giá trị"
    }
  ],
  "title": "",
  "data": [
    {
      "quarter": "01/01/2026 00:00:00",
      "total_revenue": 0.0
    },
    {
      "quarter": "01/04/2026 00:00:00",
      "total_revenue": 453700.0
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
