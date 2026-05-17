# Test Result — Q40: Tháng trong năm

## Thông tin
- **Câu hỏi:** Doanh thu và chi phí theo từng tháng trong năm nay?
- **Nhóm:** system_data_query (finance_ledger)
- **Intent dự kiến:** `system_data_query`
- **Ngày test:** 17/05/2026 17:36:28
- **Thời gian phản hồi:** 9844ms
- **Trạng thái:** ✅ Pass

## Response từ AI
**Trả lời:**

Doanh thu thÃ¡ng 4 nÄm 2026 lÃ  750.000 Äá»ng vÃ  thÃ¡ng 5 nÄm 2026 lÃ  297.700 Äá»ng. ÄÃ¢y lÃ  nhá»¯ng thÃ´ng tin quan trá»ng Äá» ÄÃ¡nh giÃ¡ hiá»u suáº¥t kinh doanh hÃ ng thÃ¡ng. Báº¡n cÃ³ thá» thá»­ phÃ¢n tÃ­ch xu hÆ°á»ng doanh thu vÃ  chi phÃ­ Äá» cÃ³ cÃ¡i nhÃ¬n toÃ n diá»n hÆ¡n vá» tÃ¬nh hÃ¬nh tÃ i chÃ­nh cá»§a doanh nghiá»p.

**Chart spec:**

```json
{
  "chartType": "line",
  "xKey": "month",
  "series": [
    {
      "dataKey": "revenue",
      "name": "Doanh thu theo thÃ¡ng trong nÄm nay"
    }
  ],
  "title": "Doanh thu theo thÃ¡ng trong nÄm nay",
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

## Ghi chú
- **Bảng liên quan:** financeledger

