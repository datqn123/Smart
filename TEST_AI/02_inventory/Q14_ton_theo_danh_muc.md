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

Äá» uá»ng chiáº¿m 60,3%, Thá»±c pháº©m khÃ´ chiáº¿m 21,6%, HÃ³a pháº©m chiáº¿m 3,8%, Äá» Än liá»n chiáº¿m 3,1%, BÃ¡nh káº¹o chiáº¿m 1,2%, vÃ  Gia vá» chiáº¿m 0,5% tá»ng sá» lÆ°á»£ng tá»n kho. Báº¡n cÃ³ thá» thá»­ phÃ¢n tÃ­ch xu hÆ°á»ng tá»n kho qua cÃ¡c thÃ¡ng hoáº·c so sÃ¡nh vá»i doanh sá» bÃ¡n hÃ ng Äá» tá»i Æ°u hÃ³a quáº£n lÃ½ hÃ ng tá»n kho.

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
      "category_name": "Thá»±c pháº©m khÃ´",
      "total_quantity": 126
    },
    {
      "category_name": "HÃ³a pháº©m",
      "total_quantity": 22
    },
    {
      "category_name": "Äá» Än liá»n",
      "total_quantity": 18
    },
    {
      "category_name": "BÃ¡nh káº¹o",
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

