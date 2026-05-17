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

DÆ°á»i ÄÃ¢y lÃ  biá»u Äá» cá»t thá» hiá»n doanh thu qua cÃ¡c thÃ¡ng:

- ThÃ¡ng 2: 0
- ThÃ¡ng 3: 0
- ThÃ¡ng 4: 397700

Biá»u Äá» nÃ y cho tháº¥y doanh thu cá»§a thÃ¡ng 4 lÃ  397700, trong khi thÃ¡ng 2 vÃ  thÃ¡ng 3 khÃ´ng cÃ³ doanh thu.

Báº¡n cÃ³ thá» thá»­ táº¡o biá»u Äá» cá»t báº±ng cÃ¡ch sá»­ dá»¥ng cÃ¡c cÃ´ng cá»¥ nhÆ° Excel hoáº·c Google Sheets. Chá» cáº§n nháº­p dá»¯ liá»u vÃ o báº£ng vÃ  chá»n loáº¡i biá»u Äá» cá»t Äá» hiá»n thá».

**Chart spec:**

```json
{
  "chartType": "bar",
  "xKey": "month",
  "series": [
    {
      "dataKey": "doanh_thu",
      "name": "GiÃ¡ trá»"
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

