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

Dá»¯ liá»u chá» cÃ³ duy nháº¥t má»t quá»¹ lÃ  'Tiá»n máº·t quá»¹ chÃ­nh' vá»i doanh thu 1047700.0. Äiá»u nÃ y cho tháº¥y toÃ n bá» doanh thu ÄÆ°á»£c ghi nháº­n vÃ o quá»¹ nÃ y trong khoáº£ng thá»i gian ÄÃ£ chá»n. Báº¡n cÃ³ thá» thá»­ Äiá»u chá»nh khoáº£ng thá»i gian hoáº·c thÃªm cÃ¡c quá»¹ khÃ¡c vÃ o bÃ¡o cÃ¡o Äá» cÃ³ cÃ¡i nhÃ¬n toÃ n diá»n hÆ¡n vá» phÃ¢n bá» doanh thu.

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
      "quá»¹": "Tiá»n máº·t quá»¹ chÃ­nh",
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

