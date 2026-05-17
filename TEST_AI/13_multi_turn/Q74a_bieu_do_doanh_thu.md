# Test Result — Q74a: Biểu đồ doanh thu

## Thông tin
- **Câu hỏi:** Vẽ biểu đồ doanh thu theo tháng
- **Nhóm:** multi_turn (chart type change)
- **Intent dự kiến:** `system_data_chart`
- **Ngày test:** 17/05/2026 17:40:21
- **Thời gian phản hồi:** 10969ms
- **Trạng thái:** ✅ Pass

## Response từ AI
**Trả lời:**

Dá»±a trÃªn dá»¯ liá»u hiá»n cÃ³, biá»u Äá» sáº½ chá» bao gá»m má»t ÄÆ°á»ng náº±m ngang trÃªn trá»¥c y táº¡i má»©c 0 cho cáº£ 4 thÃ¡ng Äáº§u nÄm 2025. Äiá»u nÃ y cho tháº¥y khÃ´ng cÃ³ doanh thu nÃ o ÄÆ°á»£c ghi nháº­n trong khoáº£ng thá»i gian nÃ y. Báº¡n cÃ³ thá» thá»­ há»i vá» cÃ¡c thÃ¡ng khÃ¡c hoáº·c cÃ¡c nÄm khÃ¡c Äá» cÃ³ thÃ´ng tin chi tiáº¿t hÆ¡n.

**Chart spec:**

```json
{
  "chartType": "line",
  "xKey": "month",
  "series": [
    {
      "dataKey": "metric_value",
      "name": "Biá»u Äá» doanh thu theo thÃ¡ng"
    }
  ],
  "title": "Biá»u Äá» doanh thu theo thÃ¡ng",
  "data": [
    {
      "month": "2025-01-01",
      "metric_value": 0
    },
    {
      "month": "2025-02-01",
      "metric_value": 0
    },
    {
      "month": "2025-03-01",
      "metric_value": 0
    },
    {
      "month": "2025-04-01",
      "metric_value": 0
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

