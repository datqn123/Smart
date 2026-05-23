# Test Result — Q74b: Biểu đồ cột

## Thông tin
- **Câu hỏi:** Chuyển sang biểu đồ cột được không?
- **Nhóm:** multi_turn (chart type change)
- **Intent dự kiến:** `system_data_chart`
- **Ngày test:** 17/05/2026 17:40:30
- **Thời gian phản hồi:** 8183ms
- **Trạng thái:** ✅ Pass

## Response từ AI
**Trả lời:**

Dưới đây là biểu đồ cột thể hiện doanh thu qua các tháng:

- Tháng 2: 0
- Tháng 3: 0
- Tháng 4: 397700

Biểu đồ này cho thấy doanh thu của tháng 4 là 397700, trong khi tháng 2 và tháng 3 không có doanh thu.

Bạn có thể thử tạo biểu đồ cột bằng cách sử dụng các công cụ như Excel hoặc Google Sheets. Chỉ cần nhập dữ liệu vào bảng và chọn loại biểu đồ cột để hiển thị.

**Chart spec:**

```json
{
  "chartType": "bar",
  "xKey": "month",
  "series": [
    {
      "dataKey": "doanh_thu",
      "name": "Giá trị"
    }
  ],
  "title": "",
  "data": [
    {
      "month": "01/03/2026 00:00:00",
      "doanh_thu": 0.0
    },
    {
      "month": "01/04/2026 00:00:00",
      "doanh_thu": 0.0
    },
    {
      "month": "01/05/2026 00:00:00",
      "doanh_thu": 397700.0
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
- **Bảng liên quan:** financeledger

