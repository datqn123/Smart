# Test Result — Q72: Doanh thu quỹ

## Thông tin
- **Câu hỏi:** Biểu đồ doanh thu theo từng quỹ
- **Nhóm:** system_data_chart (bar)
- **Intent dự kiến:** `system_data_chart`
- **Ngày test:** 17/05/2026 17:40:01
- **Thời gian phản hồi:** 11527ms
- **Trạng thái:** ✅ Pass

## Response từ AI
**Trả lời:**

Dữ liệu chỉ có duy nhất một quỹ là 'Tiền mặt quỹ chính' với doanh thu 1047700.0. Điều này cho thấy toàn bộ doanh thu được ghi nhận vào quỹ này trong khoảng thời gian đã chọn. Bạn có thể thử điều chỉnh khoảng thời gian hoặc thêm các quỹ khác vào báo cáo để có cái nhìn toàn diện hơn về phân bố doanh thu.

**Chart spec:**

```json
{
  "chartType": "pie",
  "xKey": "quá»¹",
  "series": [
    {
      "dataKey": "doanh_thu",
      "name": "Biá»u Äá» doanh thu theo tá»«ng quá»¹"
    }
  ],
  "title": "Biá»u Äá» doanh thu theo tá»«ng quá»¹",
  "data": [
    {
      "quỹ": "Tiền mặt quỹ chính",
      "doanh_thu": 1047700.0
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
- **Bảng liên quan:** financeledger, cash_funds

