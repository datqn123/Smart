# Test Result — Q70: Đơn theo kênh

## Thông tin
- **Câu hỏi:** Biểu đồ tròn phân bổ đơn hàng theo kênh bán
- **Nhóm:** system_data_chart (pie)
- **Intent dự kiến:** `system_data_chart`
- **Ngày test:** 17/05/2026 17:39:39
- **Thời gian phản hồi:** 7523ms
- **Trạng thái:** ✅ Pass

## Response từ AI
**Trả lời:**

Biá»u Äá» trÃ²n thá» hiá»n phÃ¢n bá» ÄÆ¡n hÃ ng theo kÃªnh bÃ¡n. KÃªnh Wholesale chiáº¿m 87,0%, Retail chiáº¿m 13,0%. Äiá»u nÃ y cho tháº¥y pháº§n lá»n ÄÆ¡n hÃ ng Äáº¿n tá»« kÃªnh bÃ¡n sá». Báº¡n cÃ³ thá» thá»­ tÄng cÆ°á»ng chiáº¿n lÆ°á»£c bÃ¡n láº» Äá» cáº£i thiá»n doanh sá» tá»« kÃªnh nÃ y.

**Chart spec:**

```json
{
  "chartType": "pie",
  "xKey": "order_channel",
  "series": [
    {
      "dataKey": "total_orders",
      "name": "GiÃ¡ trá»"
    }
  ],
  "title": "",
  "data": [
    {
      "order_channel": "Wholesale",
      "total_orders": 60
    },
    {
      "order_channel": "Retail",
      "total_orders": 9
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

