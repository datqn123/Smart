# Test Result — Q63: Doanh thu tháng

## Thông tin
- **Câu hỏi:** Vẽ biểu đồ doanh thu theo tháng từ đầu năm đến nay
- **Nhóm:** system_data_chart (line)
- **Intent dự kiến:** `system_data_chart`
- **Ngày test:** 17/05/2026 17:38:34
- **Thời gian phản hồi:** 8957ms
- **Trạng thái:** ✅ Pass

## Response từ AI
**Trả lời:**

Dựa trên dữ liệu đã cho, ta có thể vẽ biểu đồ doanh thu theo tháng từ đầu năm đến nay. Tuy nhiên, dữ liệu chỉ cung cấp thông tin về hai tháng cuối năm 2026 là tháng 4 và tháng 5. Để có thể vẽ biểu đồ đầy đủ, ta cần có thêm dữ liệu về doanh thu của các tháng còn lại trong năm.

**Chart spec:**

```json
{
  "chartType": "line",
  "xKey": "month",
  "series": [
    {
      "dataKey": "revenue",
      "name": "Biểu đồ doanh thu theo tháng"
    }
  ],
  "title": "Biểu đồ doanh thu theo tháng",
  "data": [
    {
      "month": "2026-04",
      "revenue": 750000.0
    },
    {
      "month": "2026-05",
      "revenue": 297700.0
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

