# Test Result — N97: Multi-turn yêu cầu vẽ biểu đồ

## Thông tin
- **Câu hỏi:** Vẽ biểu đồ cho số liệu đó
- **Nhóm:** natural_language
- **Intent dự kiến:** `system_data_chart`
- **Ngày test:** 17/05/2026 21:35:14
- **Thời gian phản hồi:** 15300ms
- **Trạng thái:** ✅ Pass

## Response từ AI
**Trả lời:**

Biểu đồ dạng饼 thể hiện giá trị tổng doanh thu là 353700.0. Biểu đồ này giúp bạn dễ dàng nhìn nhận được sự phân bố của các khoản mục trong tổng doanh thu. Bạn có thể thử thêm các loại biểu đồ khác như biểu đồ cột hoặc biểu đồ đường để so sánh và phân tích dữ liệu từ nhiều góc độ khác nhau.

**Chart spec:**

```json
{
  "chartType": "pie",
  "xKey": "total_revenue",
  "series": [
    {
      "dataKey": "total_revenue",
      "name": "Giá trị"
    }
  ],
  "title": "",
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
