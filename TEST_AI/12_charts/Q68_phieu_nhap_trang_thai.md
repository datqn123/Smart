# Test Result — Q68: PN theo trạng thái

## Thông tin
- **Câu hỏi:** Biểu đồ số phiếu nhập kho theo trạng thái
- **Nhóm:** system_data_chart (bar)
- **Intent dự kiến:** `system_data_chart`
- **Ngày test:** 17/05/2026 17:39:22
- **Thời gian phản hồi:** 8263ms
- **Trạng thái:** ✅ Pass

## Response từ AI
**Trả lời:**

Biá»u Äá» phÃ¢n bá» sá» phiáº¿u nháº­p kho theo tráº¡ng thÃ¡i: Rejected (25), Draft (26), Pending (25), Approved (28). Äiá»u nÃ y cho tháº¥y cÃ³ 25 phiáº¿u nháº­p kho bá» tá»« chá»i, 26 phiáº¿u Äang á» dáº¡ng nhÃ¡p, 25 phiáº¿u Äang chá» xá»­ lÃ½ vÃ  28 phiáº¿u ÄÃ£ ÄÆ°á»£c phÃª duyá»t. Báº¡n cÃ³ thá» thá»­ tÃ¬m hiá»u nguyÃªn nhÃ¢n cá»§a viá»c tá»« chá»i phiáº¿u nháº­p kho hoáº·c xem xÃ©t cÃ¡c phiáº¿u Äang chá» xá»­ lÃ½ Äá» Äáº£m báº£o chÃºng ÄÆ°á»£c xá»­ lÃ½ ká»p thá»i.

**Chart spec:**

```json
{
  "chartType": "pie",
  "xKey": "status",
  "series": [
    {
      "dataKey": "count",
      "name": "Biá»u Äá» phÃ¢n bá» sá» phiáº¿u nháº­p kho theo tráº¡ng thÃ¡i"
    }
  ],
  "title": "Biá»u Äá» phÃ¢n bá» sá» phiáº¿u nháº­p kho theo tráº¡ng thÃ¡i",
  "data": [
    {
      "status": "Rejected",
      "count": 25
    },
    {
      "status": "Draft",
      "count": 26
    },
    {
      "status": "Pending",
      "count": 25
    },
    {
      "status": "Approved",
      "count": 28
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
- **Bảng liên quan:** stockreceipts

