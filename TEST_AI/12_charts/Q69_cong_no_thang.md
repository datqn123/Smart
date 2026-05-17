# Test Result — Q69: Công nợ tháng

## Thông tin
- **Câu hỏi:** Vẽ biểu đồ đường xu hướng công nợ theo tháng
- **Nhóm:** system_data_chart (line)
- **Intent dự kiến:** `system_data_chart`
- **Ngày test:** 17/05/2026 17:39:31
- **Thời gian phản hồi:** 9437ms
- **Trạng thái:** ✅ Pass

## Response từ AI
**Trả lời:**

Biá»u Äá» ÄÆ°á»ng thá» hiá»n xu hÆ°á»ng cÃ´ng ná»£ theo thÃ¡ng cho tháº¥y giÃ¡ trá» cÃ´ng ná»£ khÃ´ng Äá»i lÃ  0 trong suá»t cÃ¡c thÃ¡ng tá»« thÃ¡ng 1 Äáº¿n thÃ¡ng 5 nÄm 2026. Äiá»u nÃ y cÃ³ nghÄ©a lÃ  trong khoáº£ng thá»i gian nÃ y, khÃ´ng cÃ³ cÃ´ng ná»£ nÃ o ÄÆ°á»£c ghi nháº­n. Báº¡n cÃ³ thá» thá»­ phÃ¢n tÃ­ch dá»¯ liá»u cÃ´ng ná»£ theo quÃ½ hoáº·c nÄm Äá» cÃ³ cÃ¡i nhÃ¬n tá»ng quan hÆ¡n vá» tÃ¬nh hÃ¬nh cÃ´ng ná»£ cá»§a doanh nghiá»p.

**Chart spec:**

```json
{
  "chartType": "line",
  "xKey": "month",
  "series": [
    {
      "dataKey": "metric_value",
      "name": "Xu hÆ°á»ng cÃ´ng ná»£ theo thÃ¡ng"
    }
  ],
  "title": "Xu hÆ°á»ng cÃ´ng ná»£ theo thÃ¡ng",
  "data": [
    {
      "month": "2026-01-01",
      "metric_value": 0
    },
    {
      "month": "2026-02-01",
      "metric_value": 0
    },
    {
      "month": "2026-03-01",
      "metric_value": 0
    },
    {
      "month": "2026-04-01",
      "metric_value": 0
    },
    {
      "month": "2026-05-01",
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
- **Bảng liên quan:** partnerdebts

