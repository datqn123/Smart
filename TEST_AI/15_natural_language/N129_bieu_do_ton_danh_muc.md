# Test Result — N129: Hỏi về biểu đồ tồn kho theo danh mục

## Thông tin
- **Câu hỏi:** Vẽ biểu đồ tồn kho theo từng nhóm sản phẩm
- **Nhóm:** natural_language
- **Intent dự kiến:** `system_data_chart`
- **Ngày test:** 17/05/2026 19:25:28
- **Thời gian phản hồi:** 10ms
- **Trạng thái:** ❌ Fail

## Response từ AI
**Trả lời:**

Biểu đồ dạng bánh (pie) thể hiện tổng số lượng tồn kho theo nhóm sản phẩm. Đồ uống có tổng số lượng tồn kho là 350, Thực phẩm khô là 126, Hóa phẩm là 22, Đồ ăn liền là 18, Bánh kẹo là 7 và Gia vị là 3.

Bạn có thể thử:
- So sánh biểu đồ tồn kho theo từng nhóm sản phẩm trong các tháng khác nhau để xem xu hướng tồn kho.
- Tạo biểu đồ cột để so sánh số lượng tồn kho giữa các nhóm sản phẩm.
- Sử dụng biểu đồ đường để theo dõi sự thay đổi số lượng tồn kho theo thời gian.

**Chart spec:**

```json
{
  "chartType": "pie",
  "xKey": "category_name",
  "series": [
    {
      "dataKey": "total_stock",
      "name": "Tổng số lượng tồn kho theo nhóm sản phẩm"
    }
  ],
  "title": "Tổng số lượng tồn kho theo nhóm sản phẩm",
  "data": [
    {
      "category_name": "Đồ uống",
      "total_stock": 350
    },
    {
      "category_name": "Thực phẩm khô",
      "total_stock": 126
    },
    {
      "category_name": "Hóa phẩm",
      "total_stock": 22
    },
    {
      "category_name": "Đồ ăn liền",
      "total_stock": 18
    },
    {
      "category_name": "Bánh kẹo",
      "total_stock": 7
    },
    {
      "category_name": "Gia vị",
      "total_stock": 3
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
