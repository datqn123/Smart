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

Dá»±a trÃªn dá»¯ liá»u ÄÃ£ cho, ta cÃ³ thá» váº½ biá»u Äá» doanh thu theo thÃ¡ng tá»« Äáº§u nÄm Äáº¿n nay. Tuy nhiÃªn, dá»¯ liá»u chá» cung cáº¥p thÃ´ng tin vá» hai thÃ¡ng cuá»i nÄm 2026 lÃ  thÃ¡ng 4 vÃ  thÃ¡ng 5. Äá» cÃ³ thá» váº½ biá»u Äá» Äáº§y Äá»§, ta cáº§n cÃ³ thÃªm dá»¯ liá»u vá» doanh thu cá»§a cÃ¡c thÃ¡ng cÃ²n láº¡i trong nÄm.

**Chart spec:**

```json
{
  "chartType": "line",
  "xKey": "month",
  "series": [
    {
      "dataKey": "revenue",
      "name": "Biá»u Äá» doanh thu theo thÃ¡ng"
    }
  ],
  "title": "Biá»u Äá» doanh thu theo thÃ¡ng",
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

