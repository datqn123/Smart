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

Danh má»¥c Äá» uá»ng chiáº¿m tá»· lá» lá»n nháº¥t vá»i tá»ng sá» lÆ°á»£ng 350, tiáº¿p theo lÃ  Thá»±c pháº©m khÃ´ vá»i 126 vÃ  Äá» Än liá»n vá»i 18. Báº¡n cÃ³ thá» thá»­ phÃ¢n tÃ­ch nguyÃªn nhÃ¢n táº¡i sao Äá» uá»ng láº¡i chiáº¿m tá»· lá» cao nháº¥t, hoáº·c tÃ¬m hiá»u cÃ¡c sáº£n pháº©m cá»¥ thá» trong tá»«ng danh má»¥c Äá» cÃ³ cÃ¡i nhÃ¬n chi tiáº¿t hÆ¡n.

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
      "category_name": "BÃ¡nh káº¹o",
      "total_quantity": 7
    },
    {
      "category_name": "HÃ³a pháº©m",
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
      "category_name": "Thá»±c pháº©m khÃ´",
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

