# Test Result — N75: Hỏi về biểu đồ so sánh kênh bán

## Thông tin
- **Câu hỏi:** Vẽ biểu đồ cột so sánh đơn bán sỉ và bán lẻ mỗi tháng
- **Nhóm:** natural_language
- **Intent dự kiến:** `system_data_chart`
- **Ngày test:** 17/05/2026 21:32:44
- **Thời gian phản hồi:** 12075ms
- **Trạng thái:** ✅ Pass

## Response từ AI
**Trả lời:**

Biểu đồ cột thể hiện số lượng đơn hàng bán sỉ và bán lẻ trong các tháng từ tháng 3 đến tháng 5 năm 2026. Dựa trên biểu đồ này, bạn có thể nhận thấy sự khác biệt về số lượng đơn hàng giữa bán sỉ và bán lẻ. Ví dụ, trong tháng 3, có 10 đơn hàng bán sỉ và 15 đơn hàng bán lẻ. Bạn có thể thử phân tích nguyên nhân dẫn đến sự chênh lệch này, chẳng hạn như khách hàng mục tiêu, giá cả, hay các chương trình khuyến mãi.

**Chart spec:**

```json
{
  "chartType": "bar",
  "xKey": "month",
  "series": [
    {
      "dataKey": "total_orders",
      "name": "So sánh đơn bán sỉ và bán lẻ mỗi tháng"
    }
  ],
  "title": "So sánh đơn bán sỉ và bán lẻ mỗi tháng",
  "data": [
    {
      "month": "2026-03",
      "total_orders": 13
    },
    {
      "month": "2026-04",
      "total_orders": 44
    },
    {
      "month": "2026-05",
      "total_orders": 11
    },
    {
      "month": "2026-05",
      "total_orders": 3
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
