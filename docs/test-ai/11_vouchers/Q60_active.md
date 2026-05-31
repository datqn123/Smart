# Test Result — Q60: Voucher active

## Thông tin
- **Câu hỏi:** Danh sách voucher đang còn hiệu lực (active)?
- **Nhóm:** system_data_query (vouchers)
- **Intent dự kiến:** `system_data_query`
- **Ngày test:** 17/05/2026 17:38:17
- **Thời gian phản hồi:** 5914ms
- **Trạng thái:** ✅ Pass

## Response từ AI
**Trả lời:**

Danh sách voucher đang còn hiệu lực (active):

- Giáº£m 10% (CODE: DISCOUNT10, ID: 1)
- Khách VIP 5% (CODE: VIP5, ID: 4)
- Cuá»i tuáº§n giáº£m 15% (CODE: WEEKEND15, ID: 3)
- Giáº£m 20.000Ä ÄÆ¡n tá»i thiá»u (CODE: SAVE20K, ID: 2)

Lưu ý: Hai voucher "Đã hết hạn" (CODE: EXPIRED1, ID: 5) và "Chưa đến hiệu lực" (CODE: FUTURE1, ID: 6) mặc dù có trạng thái active nhưng không đáp ứng điều kiện về thời gian.



## Kiểm tra
- [ ] Intent đúng với dự kiến
- [ ] Response không rỗng
- [ ] Nội dung liên quan đến câu hỏi
- [ ] Không hallucination/bịa số liệu

## Ghi chú
- **Bảng liên quan:** vouchers

