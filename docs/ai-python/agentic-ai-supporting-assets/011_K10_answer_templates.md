# K10 - Answer Templates

```yaml
asset_id: K10
version: "2026.06.07"
source_of_truth: manual
refresh_policy: manual_review
consumers: [answer_composer]
must_log_version_in_trace: true
```

## Purpose

Khung soạn câu trả lời tiếng Việt cho từng loại kết quả, đảm bảo nhất quán, giàu thông tin, và không leak nội bộ.

## Language Rules

- Toàn bộ text hướng user: **vi-VN**
- Không expose: SQL, stack trace, tên bảng DB, lỗi provider, class name Python
- Số tiền theo K14 (VND compact)
- Ngày tháng theo K14 (dd/MM/yyyy)
- Dùng nhãn nghiệp vụ từ K3, không dùng raw code

---

## Templates

### T1 — data_query_summary (Trả lời truy vấn dữ liệu)
```
**Kết quả:** [Câu trả lời trực tiếp 1-2 câu, nêu số liệu chính xác với đơn vị]

📊 **Chi tiết:**
[Bảng hoặc danh sách bullet điểm nổi bật nếu nhiều dòng]

ℹ️ **Dữ liệu từ:** [Nguồn nghiệp vụ, ví dụ: "Sổ cái tài chính"] | [Khoảng thời gian nếu có]

💡 **Giả định:** [Chỉ hiện khi tự suy luận - ví dụ: "Bán chạy tính theo số lượng, không phải doanh thu"]

❓ **Bạn có thể hỏi tiếp:**
- [Câu gợi ý liên quan 1]
- [Câu gợi ý liên quan 2]
- [Câu gợi ý liên quan 3]
```

**Ví dụ thực:**
```
**Kết quả:** Doanh thu tháng 06/2026 là **45,2 triệu đồng**.

📊 **Chi tiết:**
- Tổng giao dịch ghi sổ: 89 lượt
- Ngày cao nhất: 12/06/2026 — 4,1 triệu đồng

ℹ️ **Dữ liệu từ:** Sổ cái tài chính | Từ 01/06/2026 đến 30/06/2026

❓ **Bạn có thể hỏi tiếp:**
- So sánh với doanh thu tháng trước thế nào?
- Kênh bán lẻ hay bán sỉ đóng góp nhiều hơn?
- Lợi nhuận gộp tháng này là bao nhiêu?
```

---

### T2 — chart_report (Báo cáo biểu đồ)
```
📈 **[Tiêu đề biểu đồ]** — [Khoảng thời gian]

[Biểu đồ được hiển thị phía trên]

🔍 **Nhận xét nhanh:**
- [Điểm cao nhất / thấp nhất / xu hướng]
- [Bất thường nếu có]

ℹ️ **Đơn vị:** [VND / sản phẩm / đơn hàng] | **Nguồn:** [Tên bảng nghiệp vụ]

❓ **Bạn có thể hỏi tiếp:**
- [Gợi ý drill-down hoặc so sánh]
```

---

### T3 — draft_preview_hitl (Nháp chờ xác nhận)
```
📝 **Xem lại trước khi xác nhận**

Trợ lý đã chuẩn bị [loại nháp] sau đây. Vui lòng kiểm tra và xác nhận để tiếp tục.

**[Loại thực thể]:**
[Bảng thông tin nháp với các trường đã điền]

⚠️ **Lưu ý:** Sau khi xác nhận, dữ liệu sẽ được ghi vào hệ thống và không thể hoàn tác tự động.

Bạn muốn:
✅ **Xác nhận** — Ghi vào hệ thống
✏️ **Chỉnh sửa** — Thay đổi thông tin
❌ **Hủy** — Không thực hiện
```

**Ví dụ thực:**
```
📝 **Xem lại trước khi xác nhận**

Trợ lý đã chuẩn bị nháp **Sản phẩm mới** sau đây:

**Sản phẩm mới:**
| Trường | Giá trị |
|---|---|
| Tên sản phẩm | Nước suối Aquafina 500ml |
| Mã SKU | SP-NUA-001 |
| Danh mục | Đồ uống |
| Giá bán | 8.000 đ |

⚠️ **Lưu ý:** Sau khi xác nhận, sản phẩm sẽ được thêm vào danh mục.

Bạn muốn: ✅ Xác nhận | ✏️ Chỉnh sửa | ❌ Hủy
```

---

### T4 — draft_confirmed (Nháp đã xác nhận thành công)
```
✅ **Đã xác nhận thành công!**

[Loại thực thể] **[Tên/mã]** đã được ghi vào hệ thống.

📋 **Tóm tắt:**
[Thông tin chính đã ghi]

❓ **Bạn có thể hỏi tiếp:**
- [Gợi ý bước tiếp theo liên quan]
```

---

### T5 — clarification_hitl (Hỏi lại làm rõ)
```
🤔 **Cần thêm thông tin để xử lý**

[Mô tả ngắn tại sao cần làm rõ]

[Câu hỏi 1]:
→ [Option A] | [Option B] | [Option C]

[Câu hỏi 2 nếu có]:
→ [Option A] | [Option B]

Hoặc bạn có thể nhập trực tiếp câu trả lời.
```

**Ví dụ thực:**
```
🤔 **Cần thêm thông tin để xử lý**

Bạn hỏi về "doanh thu" nhưng chưa có khoảng thời gian.

Bạn muốn xem doanh thu của:
→ **Tháng này** (06/2026) | **Tháng trước** (05/2026) | **Quý 2/2026** | **Tự nhập khoảng thời gian**
```

---

### T6 — empty_result (Không có dữ liệu)
```
🔍 **Không tìm thấy dữ liệu phù hợp**

[Mô tả những gì đã tìm kiếm và điều kiện lọc]

Có thể do:
- [Lý do có thể 1 — ví dụ: khoảng thời gian chưa có dữ liệu]
- [Lý do có thể 2 — ví dụ: tên sản phẩm chưa khớp chính xác]

💡 **Thử lại với:**
- [Gợi ý hỏi khác hoặc bổ sung chi tiết]
```

**Ví dụ thực:**
```
🔍 **Không tìm thấy dữ liệu phù hợp**

Không có dữ liệu tồn kho cho sản phẩm "Pepsi Cola" trong hệ thống.

Có thể do:
- Sản phẩm chưa được nhập vào danh mục
- Tên sản phẩm khác với trong hệ thống

💡 **Thử lại với:**
- Kiểm tra danh sách sản phẩm: "Danh sách tất cả sản phẩm đồ uống"
- Hỏi về sản phẩm cụ thể hơn: "Tồn kho nước ngọt lon"
```

---

### T7 — partial_result_budget (Kết quả từng phần do hết budget)
```
⚡ **Kết quả từng phần**

Trợ lý đã hoàn thành một phần yêu cầu trong giới hạn cho phép.

**Đã có:**
[Thông tin đã thu thập được]

**Chưa hoàn thành:**
[Phần còn lại và lý do]

💡 **Để có kết quả đầy đủ hơn**, hãy thử hỏi từng phần nhỏ hơn:
- [Gợi ý câu hỏi chia nhỏ]
```

---

### T8 — out_of_scope (Ngoài phạm vi)
```
ℹ️ **Ngoài phạm vi hỗ trợ**

Câu hỏi này nằm ngoài khả năng của trợ lý ERP hiện tại.

Trợ lý có thể giúp bạn với:
- 📦 **Tồn kho & Kho hàng** — kiểm tra tồn, sắp hết hàng, hết hạn
- 🛒 **Đơn hàng bán** — theo dõi đơn, trạng thái, kênh bán
- 💰 **Tài chính** — doanh thu, chi phí, công nợ (chỉ Owner)
- 📋 **Sản phẩm & Danh mục** — tra cứu, thêm nháp
- 📊 **Biểu đồ & Báo cáo** — tổng hợp trực quan

❓ **Ví dụ câu hỏi:**
- "Doanh thu tháng này là bao nhiêu?"
- "Sản phẩm nào sắp hết hàng?"
- "Khách hàng nào đang còn nợ tiền?"
```

---

### T9 — permission_denied (Không có quyền)
```
🔒 **Bạn không có quyền xem thông tin này**

Thông tin bạn yêu cầu chỉ dành cho người có quyền truy cập phù hợp.

Nếu bạn cần xem thông tin này, vui lòng liên hệ **Owner** của cửa hàng để được cấp quyền.

❓ **Bạn có thể hỏi:**
- [Câu hỏi tương tự nhưng trong phạm vi quyền của bạn]
```

---

### T10 — tool_unavailable (Công cụ không khả dụng)
```
⚠️ **Tạm thời không thể xử lý**

Trợ lý gặp sự cố khi lấy dữ liệu. Vui lòng thử lại sau ít phút.

Nếu lỗi tiếp tục, hãy liên hệ quản trị viên hệ thống.

[Mã tham chiếu lỗi: {correlation_id}]
```

---

## Next Question Suggestions by Intent

```yaml
suggestions:
  revenue_by_period:
    - "So sánh với cùng kỳ tháng trước?"
    - "Doanh thu theo kênh bán lẻ/sỉ thế nào?"
    - "Lợi nhuận gộp tháng này là bao nhiêu?"
  low_stock_list:
    - "Xem tồn kho chi tiết của [sản phẩm cụ thể]?"
    - "Có phiếu nhập nào đang chờ duyệt không?"
    - "Nhà cung cấp nào cung cấp sản phẩm này?"
  customer_debt:
    - "Ai nợ quá hạn rồi?"
    - "Tổng công nợ nhà cung cấp là bao nhiêu?"
    - "Lịch sử thanh toán của khách [tên] thế nào?"
  top_products:
    - "Sản phẩm nào có tồn kho thấp nhất?"
    - "Doanh thu của [sản phẩm top 1] theo từng tháng?"
    - "Danh mục nào bán chạy nhất?"
  order_status:
    - "Chi tiết đơn [mã đơn] gồm những sản phẩm gì?"
    - "Đơn nào đã thanh toán rồi?"
    - "Đơn trễ bao lâu rồi?"
```
