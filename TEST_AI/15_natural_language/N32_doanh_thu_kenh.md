# Test Result — N32: Doanh thu theo kênh

## Thông tin
- **Câu hỏi:** Bán tại quầy với bán sỉ thì kênh nào doanh thu cao hơn?
- **Nhóm:** natural_language
- **Intent dự kiến:** `system_data_query`
- **Ngày test:** 17/05/2026 21:25:16
- **Thời gian phản hồi:** 9616ms
- **Trạng thái:** ✅ Pass

## Response từ AI
**Trả lời:**

Kênh bán sỉ (Wholesale) có doanh thu cao hơn kênh bán lẻ (Retail) với tỷ lệ lần lượt là 99,9% và 0,1%. Điều này cho thấy doanh thu chủ yếu đến từ các đơn hàng bán sỉ.

Bạn có thể thử:
- Tăng cường khuyến mãi cho khách hàng bán lẻ để tăng doanh thu từ kênh này
- Mở rộng mạng lưới khách hàng bán sỉ để tăng doanh thu
- Cải thiện chất lượng sản phẩm để thu hút khách hàng bán lẻ

**Chart spec:**

```json
{
  "chartType": "pie",
  "xKey": "order_channel",
  "series": [
    {
      "dataKey": "total_revenue",
      "name": "Tỷ lệ doanh thu bán sỉ và bán lẻ"
    }
  ],
  "title": "Tỷ lệ doanh thu bán sỉ và bán lẻ",
  "data": [
    {
      "order_channel": "Wholesale",
      "total_revenue": 310254552.0
    },
    {
      "order_channel": "Retail",
      "total_revenue": 540000.0
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
