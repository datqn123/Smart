# Test Result — Q71: Trạng thái tồn

## Thông tin
- **Câu hỏi:** Biểu đồ cột số lượng sản phẩm theo trạng thái tồn kho
- **Nhóm:** system_data_chart (bar)
- **Intent dự kiến:** `system_data_chart`
- **Ngày test:** 17/05/2026 17:39:49
- **Thời gian phản hồi:** 10349ms
- **Trạng thái:** ✅ Pass

## Response từ AI
**Trả lời:**

Biá»u Äá» cá»t thá» hiá»n sá» lÆ°á»£ng sáº£n pháº©m theo tráº¡ng thÃ¡i tá»n kho vá»i cÃ¡c sáº£n pháº©m nhÆ° NÆ°á»c suá»i 500ml (240), Gáº¡o táº» 5kg (120), HÃ ng seed demo #6 (115), Sá»¯a tÆ°Æ¡i tiá»t trÃ¹ng 1L (100), HÃ ng seed demo #44 (54), HÃ ng seed demo #43 (53), HÃ ng seed demo #42 (52), HÃ ng seed demo #41 (51). Báº¡n cÃ³ thá» thá»­ tÃ¬m hiá»u thÃªm vá» cÃ¡c sáº£n pháº©m khÃ¡c trong há» thá»ng hoáº·c phÃ¢n tÃ­ch xu hÆ°á»ng tá»n kho theo thá»i gian.

**Chart spec:**

```json
{
  "chartType": "bar",
  "xKey": "product_name",
  "series": [
    {
      "dataKey": "quantity",
      "name": "Sá» lÆ°á»£ng sáº£n pháº©m theo tráº¡ng thÃ¡i tá»n kho"
    }
  ],
  "title": "Sá» lÆ°á»£ng sáº£n pháº©m theo tráº¡ng thÃ¡i tá»n kho",
  "data": [
    {
      "product_name": "NÆ°á»c suá»i 500ml",
      "quantity": 240
    },
    {
      "product_name": "Gáº¡o táº» 5kg",
      "quantity": 120
    },
    {
      "product_name": "HÃ ng seed demo #6",
      "quantity": 115
    },
    {
      "product_name": "Sá»¯a tÆ°Æ¡i tiá»t trÃ¹ng 1L",
      "quantity": 100
    },
    {
      "product_name": "HÃ ng seed demo #44",
      "quantity": 54
    },
    {
      "product_name": "HÃ ng seed demo #43",
      "quantity": 53
    },
    {
      "product_name": "HÃ ng seed demo #42",
      "quantity": 52
    },
    {
      "product_name": "HÃ ng seed demo #41",
      "quantity": 51
    },
    {
      "product_name": "HÃ ng seed demo #40",
      "quantity": 50
    },
    {
      "product_name": "HÃ ng seed demo #39",
      "quantity": 49
    },
    {
      "product_name": "HÃ ng seed demo #38",
      "quantity": 48
    },
    {
      "product_name": "HÃ ng seed demo #37",
      "quantity": 47
    },
    {
      "product_name": "HÃ ng seed demo #36",
      "quantity": 46
    },
    {
      "product_name": "HÃ ng seed demo #35",
      "quantity": 45
    },
    {
      "product_name": "HÃ ng seed demo #34",
      "quantity": 44
    },
    {
      "product_name": "HÃ ng seed demo #33",
      "quantity": 43
    },
    {
      "product_name": "HÃ ng seed demo #32",
      "quantity": 42
    },
    {
      "product_name": "HÃ ng seed demo #31",
      "quantity": 41
    },
    {
      "product_name": "HÃ ng seed demo #30",
      "quantity": 40
    },
    {
      "product_name": "HÃ ng seed demo #29",
      "quantity": 39
    },
    {
      "product_name": "HÃ ng seed demo #28",
      "quantity": 38
    },
    {
      "product_name": "HÃ ng seed demo #27",
      "quantity": 37
    },
    {
      "product_name": "HÃ ng seed demo #26",
      "quantity": 36
    },
    {
      "product_name": "HÃ ng seed demo #25",
      "quantity": 35
    },
    {
      "product_name": "HÃ ng seed demo #24",
      "quantity": 34
    },
    {
      "product_name": "HÃ ng seed demo #22",
      "quantity": 32
    },
    {
      "product_name": "HÃ ng seed demo #21",
      "quantity": 31
    },
    {
      "product_name": "HÃ ng seed demo #23",
      "quantity": 30
    },
    {
      "product_name": "HÃ ng seed demo #20",
      "quantity": 30
    },
    {
      "product_name": "HÃ ng seed demo #19",
      "quantity": 29
    },
    {
      "product_name": "HÃ ng seed demo #18",
      "quantity": 28
    },
    {
      "product_name": "HÃ ng seed demo #17",
      "quantity": 27
    },
    {
      "product_name": "HÃ ng seed demo #16",
      "quantity": 26
    },
    {
      "product_name": "NÆ°á»c rá»­a chÃ©n 1.5L",
      "quantity": 22
    },
    {
      "product_name": "HÃ ng seed demo #12",
      "quantity": 21
    },
    {
      "product_name": "HÃ ng seed demo #11",
      "quantity": 21
    },
    {
      "product_name": "HÃ ng seed demo #14",
      "quantity": 20
    },
    {
      "product_name": "HÃ ng seed demo #15",
      "quantity": 19
    },
    {
      "product_name": "HÃ ng seed demo #9",
      "quantity": 19
    },
    {
      "product_name": "Tokboki",
      "quantity": 18
    },
    {
      "product_name": "HÃ ng seed demo #8",
      "quantity": 18
    },
    {
      "product_name": "HÃ ng seed demo #7",
      "quantity": 16
    },
    {
      "product_name": "HÃ ng seed demo #13",
      "quantity": 16
    },
    {
      "product_name": "HÃ ng seed demo #50",
      "quantity": 15
    },
    {
      "product_name": "HÃ ng seed demo #5",
      "quantity": 15
    },
    {
      "product_name": "HÃ ng seed demo #49",
      "quantity": 14
    },
    {
      "product_name": "HÃ ng seed demo #4",
      "quantity": 14
    },
    {
      "product_name": "HÃ ng seed demo #3",
      "quantity": 13
    },
    {
      "product_name": "HÃ ng seed demo #48",
      "quantity": 13
    },
    {
      "product_name": "HÃ ng seed demo #2",
      "quantity": 12
    },
    {
      "product_name": "HÃ ng seed demo #47",
      "quantity": 12
    },
    {
      "product_name": "HÃ ng seed demo #10",
      "quantity": 12
    },
    {
      "product_name": "HÃ ng seed demo #46",
      "quantity": 11
    },
    {
      "product_name": "Coca 330ml thÃ¹ng 24",
      "quantity": 10
    },
    {
      "product_name": "HÃ ng seed demo #45",
      "quantity": 10
    },
    {
      "product_name": "BÃ¡nh quy socola 137g",
      "quantity": 7
    },
    {
      "product_name": "MÃ¬ gÃ³i hÆ°Æ¡ng vá» gÃ ",
      "quantity": 6
    },
    {
      "product_name": "HÃ ng seed demo #1",
      "quantity": 6
    },
    {
      "product_name": "NÆ°á»c máº¯m 40Â°N 500ml",
      "quantity": 3
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
- **Bảng liên quan:** inventory

