# Test Result — N120: Hỏi về biểu đồ doanh thu quý

## Thông tin
- **Câu hỏi:** Vẽ biểu đồ doanh thu theo từng quý
- **Nhóm:** natural_language
- **Intent dự kiến:** `system_data_chart`
- **Ngày test:** 17/05/2026 19:25:28
- **Thời gian phản hồi:** 15ms
- **Trạng thái:** ❌ Fail

## Response từ AI
**Trả lời:**

Dữ liệu chỉ có 1 quý trong năm 2026 với doanh thu là 1.103.700.000 đồng. Để vẽ biểu đồ doanh thu theo từng quý, bạn cần có dữ liệu của các quý khác trong năm. Bạn có thể thử hỏi về doanh thu của các quý khác trong năm 2026 hoặc các năm tiếp theo.

**Chart spec:**

```json
{
  "chartType": "pie",
  "xKey": "quarter",
  "series": [
    {
      "dataKey": "total_revenue",
      "name": "Biểu đồ doanh thu theo quý"
    }
  ],
  "title": "Biểu đồ doanh thu theo quý",
  "data": [
    {
      "quarter": 2,
      "total_revenue": 1103700.0
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
