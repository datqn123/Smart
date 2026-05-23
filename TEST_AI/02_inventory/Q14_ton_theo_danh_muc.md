# Test Result — Q14: Tồn theo danh mục

## Thông tin
- **Câu hỏi:** Tổng số lượng tồn kho theo từng danh mục sản phẩm?
- **Nhóm:** system_data_query (inventory)
- **Intent dự kiến:** `system_data_query`
- **Ngày test:** 17/05/2026 17:33:38
- **Thời gian phản hồi:** 9215ms
- **Trạng thái:** ✅ Pass

## Response từ AI
**Trả lời:**

Đồ uống chiếm 60,3%, Thực phẩm khô chiếm 21,6%, Hóa phẩm chiếm 3,8%, Đồ ăn liền chiếm 3,1%, Bánh kẹo chiếm 1,2%, và Gia vị chiếm 0,5% tổng số lượng tồn kho. Bạn có thể thử phân tích xu hướng tồn kho qua các tháng hoặc so sánh với doanh số bán hàng để tối ưu hóa quản lý hàng tồn kho.

**Chart spec:**

```json
{
  "chartType": "pie",
  "xKey": "category_name",
  "series": [
    {
      "dataKey": "total_quantity",
      "name": "Tá»ng sá» lÆ°á»£ng tá»n kho theo tá»«ng danh má»¥c sáº£n pháº©m"
    }
  ],
  "title": "Tá»ng sá» lÆ°á»£ng tá»n kho theo tá»«ng danh má»¥c sáº£n pháº©m",
  "data": [
    {
      "category_name": "Äá» uá»ng",
      "total_quantity": 350
    },
    {
      "category_name": "Thực phẩm khô",
      "total_quantity": 126
    },
    {
      "category_name": "Hóa phẩm",
      "total_quantity": 22
    },
    {
      "category_name": "Äá» Än liá»n",
      "total_quantity": 18
    },
    {
      "category_name": "Bánh kẹo",
      "total_quantity": 7
    },
    {
      "category_name": "Gia vá»",
      "total_quantity": 3
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
- **Bảng liên quan:** inventory, products, categories

