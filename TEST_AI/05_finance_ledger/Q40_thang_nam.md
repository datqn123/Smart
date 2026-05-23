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

Doanh thu tháng 4 năm 2026 là 750.000 đồng và tháng 5 năm 2026 là 297.700 đồng. Đây là những thông tin quan trọng để đánh giá hiệu suất kinh doanh hàng tháng. Bạn có thể thử phân tích xu hướng doanh thu và chi phí để có cái nhìn toàn diện hơn về tình hình tài chính của doanh nghiệp.

**Chart spec:**

```json
{
  "chartType": "line",
  "xKey": "month",
  "series": [
    {
      "dataKey": "revenue",
      "name": "Doanh thu theo tháng trong năm nay"
    }
  ],
  "title": "Doanh thu theo tháng trong năm nay",
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

