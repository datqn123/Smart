# Test Result — Q67: DT vs CP

## Thông tin
- **Câu hỏi:** Vẽ biểu đồ doanh thu và chi phí theo từng tháng
- **Nhóm:** system_data_chart (bar/line)
- **Intent dự kiến:** `system_data_chart`
- **Ngày test:** 17/05/2026 17:39:13
- **Thời gian phản hồi:** 10639ms
- **Trạng thái:** ✅ Pass

## Response từ AI
**Trả lời:**

Biá»u Äá» thá» hiá»n sá»± thay Äá»i cá»§a doanh thu vÃ  chi phÃ­ qua cÃ¡c thÃ¡ng trong nÄm 2026. Dá»±a trÃªn dá»¯ liá»u nÃ y, báº¡n cÃ³ thá» nháº­n tháº¥y xu hÆ°á»ng tÄng trÆ°á»ng cá»§a doanh nghiá»p vÃ  ÄÆ°a ra cÃ¡c quyáº¿t Äá»nh kinh doanh phÃ¹ há»£p. VÃ­ dá»¥, náº¿u doanh thu tÄng máº¡nh vÃ o quÃ½ III, báº¡n cÃ³ thá» xem xÃ©t tÄng cÆ°á»ng quáº£ng cÃ¡o hoáº·c má» rá»ng sáº£n xuáº¥t. NgÆ°á»£c láº¡i, náº¿u chi phÃ­ tÄng cao vÃ o quÃ½ IV, báº¡n cáº§n tÃ¬m cÃ¡ch tá»i Æ°u hÃ³a chi phÃ­ Äá» Äáº£m báº£o lá»£i nhuáº­n.

**Chart spec:**

```json
{
  "chartType": "line",
  "xKey": "month",
  "series": [
    {
      "dataKey": "revenue",
      "name": "Biá»u Äá» doanh thu vÃ  chi phÃ­ theo tá»«ng thÃ¡ng"
    }
  ],
  "title": "Biá»u Äá» doanh thu vÃ  chi phÃ­ theo tá»«ng thÃ¡ng",
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

