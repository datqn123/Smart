# Test Result — Q66: Tồn theo DM

## Thông tin
- **Câu hỏi:** Biểu đồ tồn kho theo danh mục sản phẩm
- **Nhóm:** system_data_chart (bar)
- **Intent dự kiến:** `system_data_chart`
- **Ngày test:** 17/05/2026 17:39:03
- **Thời gian phản hồi:** 8294ms
- **Trạng thái:** ✅ Pass

## Response từ AI
**Trả lời:**

Danh mục Đồ uống chiếm tỷ lệ lớn nhất với tổng số lượng 350, tiếp theo là Thực phẩm khô với 126 và Đồ ăn liền với 18. Bạn có thể thử phân tích nguyên nhân tại sao Đồ uống lại chiếm tỷ lệ cao nhất, hoặc tìm hiểu các sản phẩm cụ thể trong từng danh mục để có cái nhìn chi tiết hơn.

**Chart spec:**

```json
{
  "chartType": "pie",
  "xKey": "category_name",
  "series": [
    {
      "dataKey": "total_quantity",
      "name": "Biá»u Äá» tá»n kho theo danh má»¥c sáº£n pháº©m"
    }
  ],
  "title": "Biá»u Äá» tá»n kho theo danh má»¥c sáº£n pháº©m",
  "data": [
    {
      "category_name": "Äá» Än liá»n",
      "total_quantity": 18
    },
    {
      "category_name": "Bánh kẹo",
      "total_quantity": 7
    },
    {
      "category_name": "Hóa phẩm",
      "total_quantity": 22
    },
    {
      "category_name": "Äá» uá»ng",
      "total_quantity": 350
    },
    {
      "category_name": "Gia vá»",
      "total_quantity": 3
    },
    {
      "category_name": "Thực phẩm khô",
      "total_quantity": 126
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
- **Bảng liên quan:** inventory, categories

