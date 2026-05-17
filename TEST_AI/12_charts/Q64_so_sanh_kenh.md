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

Biá»u Äá» cá»t thá» hiá»n sá» ÄÆ¡n bÃ¡n láº» theo thÃ¡ng cho tháº¥y táº¥t cáº£ cÃ¡c thÃ¡ng Äá»u cÃ³ 0 ÄÆ¡n bÃ¡n láº». Äiá»u nÃ y cho tháº¥y toÃ n bá» ÄÆ¡n hÃ ng Äá»u lÃ  ÄÆ¡n bÃ¡n sá». CÃ³ thá» do chÃ­nh sÃ¡ch bÃ¡n hÃ ng chá» táº­p trung vÃ o khÃ¡ch hÃ ng sá» hoáº·c chÆ°a cÃ³ khÃ¡ch hÃ ng láº» quan tÃ¢m Äáº¿n sáº£n pháº©m. Báº¡n cÃ³ thá» thá»­ tÃ¬m hiá»u thÃªm vá» thá» trÆ°á»ng khÃ¡ch hÃ ng láº», hoáº·c xem xÃ©t viá»c má» rá»ng kÃªnh bÃ¡n láº» thÃ´ng qua cÃ¡c sÃ n thÆ°Æ¡ng máº¡i Äiá»n tá»­ hoáº·c cá»­a hÃ ng váº­t lÃ½.

**Chart spec:**

```json
{
  "chartType": "bar",
  "xKey": "month",
  "series": [
    {
      "dataKey": "retail_orders",
      "name": "Sá» ÄÆ¡n bÃ¡n láº» theo thÃ¡ng"
    }
  ],
  "title": "Sá» ÄÆ¡n bÃ¡n láº» theo thÃ¡ng",
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

