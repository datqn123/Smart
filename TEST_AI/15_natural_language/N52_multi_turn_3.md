# Test Result — N52: Multi-turn đổi biểu đồ

## Thông tin
- **Câu hỏi:** Vẽ biểu đồ cột thay vì đường được không?
- **Nhóm:** natural_language
- **Intent dự kiến:** `system_data_chart`
- **Ngày test:** 17/05/2026 21:29:53
- **Thời gian phản hồi:** 8980ms
- **Trạng thái:** ✅ Pass

## Response từ AI
**Trả lời:**

Biểu đồ cột thể hiện tổng doanh thu là 353700.0. Biểu đồ cột thường được sử dụng để so sánh các giá trị trong cùng một khoảng thời gian hoặc giữa các khoảng thời gian khác nhau. Bạn có thể thử tạo biểu đồ cột để xem sự khác biệt về doanh thu giữa các tháng hoặc quý.

**Chart spec:**

```json
{
  "chartType": "bar",
  "xKey": "total_revenue",
  "series": [
    {
      "dataKey": "total_revenue",
      "name": "Biểu đồ cột tổng doanh thu"
    }
  ],
  "title": "Biểu đồ cột tổng doanh thu",
  "data": [
    {
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
