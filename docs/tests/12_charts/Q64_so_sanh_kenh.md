# Test Result — Q64: So sánh kênh

## Thông tin
- **Câu hỏi:** Biểu đồ cột so sánh số đơn bán sỉ và bán lẻ theo tháng
- **Nhóm:** system_data_chart (bar)
- **Intent dự kiến:** `system_data_chart`
- **Ngày test:** 17/05/2026 17:38:43
- **Thời gian phản hồi:** 9397ms
- **Trạng thái:** ✅ Pass

## Response từ AI
**Trả lời:**

Biểu đồ cột thể hiện số đơn bán lẻ theo tháng cho thấy tất cả các tháng đều có 0 đơn bán lẻ. Điều này cho thấy toàn bộ đơn hàng đều là đơn bán sỉ. Có thể do chính sách bán hàng chỉ tập trung vào khách hàng sỉ hoặc chưa có khách hàng lẻ quan tâm đến sản phẩm. Bạn có thể thử tìm hiểu thêm về thị trường khách hàng lẻ, hoặc xem xét việc mở rộng kênh bán lẻ thông qua các sàn thương mại điện tử hoặc cửa hàng vật lý.

**Chart spec:**

```json
{
  "chartType": "bar",
  "xKey": "month",
  "series": [
    {
      "dataKey": "retail_orders",
      "name": "Số đơn bán lẻ theo tháng"
    }
  ],
  "title": "Số đơn bán lẻ theo tháng",
  "data": [
    {
      "month": "2026-03",
      "retail_orders": 0
    },
    {
      "month": "2026-04",
      "retail_orders": 0
    },
    {
      "month": "2026-05",
      "retail_orders": 0
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
- **Bảng liên quan:** salesorders

