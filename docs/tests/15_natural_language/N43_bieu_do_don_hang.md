# Test Result — N43: Biểu đồ phân bổ đơn hàng

## Thông tin
- **Câu hỏi:** Cho mình xem biểu đồ tròn đơn hàng chia theo kênh bán
- **Nhóm:** natural_language
- **Intent dự kiến:** `system_data_chart`
- **Ngày test:** 17/05/2026 21:28:37
- **Thời gian phản hồi:** 9836ms
- **Trạng thái:** ✅ Pass

## Response từ AI
**Trả lời:**

Biểu đồ tròn thể hiện số lượng đơn hàng theo kênh bán: Wholesale chiếm 60 đơn hàng và Retail chiếm 11 đơn hàng.

Biểu đồ này cho thấy sự phân bố đơn hàng giữa các kênh bán lẻ và bán buôn. Có thể thấy rằng phần lớn đơn hàng đến từ kênh bán buôn (Wholesale), chiếm 84,5% tổng số đơn hàng, trong khi kênh bán lẻ (Retail) chỉ chiếm 15,5%.

Bạn có thể thử:
- Phân tích xu hướng đơn hàng theo thời gian để xác định mùa vụ hoặc xu hướng tăng trưởng.
- So sánh biểu đồ này với các kỳ trước để đánh giá hiệu suất kinh doanh.
- Tìm hiểu nguyên nhân tại sao kênh bán buôn lại chiếm tỷ lệ cao hơn và xem xét các chiến lược để tăng cường kênh bán lẻ.

**Chart spec:**

```json
{
  "chartType": "pie",
  "xKey": "order_channel",
  "series": [
    {
      "dataKey": "count",
      "name": "Đơn hàng theo kênh bán"
    }
  ],
  "title": "Đơn hàng theo kênh bán",
  "data": [
    {
      "order_channel": "Wholesale",
      "count": 60
    },
    {
      "order_channel": "Retail",
      "count": 11
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
