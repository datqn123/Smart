# Test Result — Q73a: Doanh thu tháng 3

## Thông tin
- **Câu hỏi:** Doanh thu tháng 3 là bao nhiêu?
- **Nhóm:** multi_turn (thread context)
- **Intent dự kiến:** `system_data_query`
- **Ngày test:** 17/05/2026 17:40:07
- **Thời gian phản hồi:** 6825ms
- **Trạng thái:** ✅ Pass

## Response từ AI
**Trả lời:**

- Hiá»n khÃ´ng tÃ­nh ÄÆ°á»£c doanh thu thÃ¡ng 3 (káº¿t quáº£ NULL). ThÆ°á»ng do:
 - KhÃ´ng cÃ³ dÃ²ng tá»n khá»p JOIN vá»i `receipt_detail` vÃ  `productpricehistory`
 - ChÆ°a cÃ³ giÃ¡ vá»n trong `productpricehistory` cho ÄÆ¡n vá» cÆ¡ sá» (`productunits.is_base_unit = TRUE`)
- VÃ­ dá»¥ cÃ¡c trÆ°á»ng há»£p cÃ³ thá» xáº£y ra:
 - Sáº£n pháº©m A (SKU: A123) cÃ³ receipt_code R001 nhÆ°ng chÆ°a cÃ³ giÃ¡ vá»n
 - Sáº£n pháº©m B (SKU: B456) cÃ³ receipt_code R002 nhÆ°ng khÃ´ng khá»p ÄÆ¡n vá» cÆ¡ sá»
- Báº¡n cÃ³ thá» há»i:
 - "CÃ³ bao nhiÃªu sáº£n pháº©m chÆ°a cÃ³ giÃ¡ vá»n trong thÃ¡ng 3?"
 - "Danh sÃ¡ch cÃ¡c receipt_code khÃ´ng khá»p vá»i productpricehistory?"



## Kiểm tra
- [ ] Intent đúng với dự kiến
- [ ] Response không rỗng
- [ ] Nội dung liên quan đến câu hỏi
- [ ] Không hallucination/bịa số liệu

## Ghi chú
- **Bảng liên quan:** financeledger

