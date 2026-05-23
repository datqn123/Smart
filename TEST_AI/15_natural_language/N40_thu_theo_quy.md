# Test Result — N40: Tổng thu theo quý

## Thông tin
- **Câu hỏi:** Mỗi quý mình thu được bao nhiêu tiền?
- **Nhóm:** natural_language
- **Intent dự kiến:** `system_data_query`
- **Ngày test:** 17/05/2026 21:28:02
- **Thời gian phản hồi:** 8251ms
- **Trạng thái:** ✅ Pass

## Response từ AI
**Trả lời:**

Tổng doanh thu quý này là 1.103.700 đồng. Đây là số tiền thu được từ tất cả các giao dịch bán hàng trong quý. Bạn có thể thử phân tích theo tháng để xem xu hướng tăng trưởng, hoặc so sánh với quý trước để đánh giá hiệu quả kinh doanh.

**Chart spec:**

```json
{
  "chartType": "pie",
  "xKey": "total_revenue_quarter",
  "series": [
    {
      "dataKey": "total_revenue_quarter",
      "name": "Giá trị"
    }
  ],
  "title": "",
  "data": [
    {
      "total_revenue_quarter": 1103700.0
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
