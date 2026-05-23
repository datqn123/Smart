# Test Result — N100: Multi-turn hỏi doanh thu rồi vẽ biểu đồ cột

## Thông tin
- **Câu hỏi:** Vẽ biểu đồ doanh thu theo tháng
- **Nhóm:** natural_language
- **Intent dự kiến:** `system_data_chart`
- **Ngày test:** 17/05/2026 21:09:42
- **Thời gian phản hồi:** 11052ms
- **Trạng thái:** ✅ Pass

## Response từ AI
**Trả lời:**

Dựa trên dữ liệu đã cho, ta có thể vẽ biểu đồ doanh thu theo tháng như sau:

- Trục X: Tháng
- Trục Y: Doanh thu

Điểm A: Tháng 3 năm 2026, doanh thu là 750.000.
Điểm B: Tháng 4 năm 2026, doanh thu là 353.700.

Biểu đồ sẽ thể hiện sự giảm sút của doanh thu từ tháng 3 sang tháng 4 năm 2026.

Bạn có thể thử:
- Phân tích nguyên nhân của sự giảm sút doanh thu.
- So sánh doanh thu với các tháng khác trong cùng kỳ.
- Đánh giá hiệu quả của các chiến lược kinh doanh.

**Chart spec:**

```json
{
  "chartType": "line",
  "xKey": "month",
  "series": [
    {
      "dataKey": "total_revenue",
      "name": "Biểu đồ doanh thu theo tháng"
    }
  ],
  "title": "Biểu đồ doanh thu theo tháng",
  "data": [
    {
      "month": "01/04/2026 00:00:00",
      "total_revenue": 750000.0
    },
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
