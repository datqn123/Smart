# QA Test Plan — AI Chat (Smart ERP)

> **Ngày tạo:** 17/05/2026
> **Mục đích:** Kiểm thử chức năng chat AI (LangGraph + FastAPI relay qua Spring Boot)
> **Kiến trúc:** Frontend → Spring (`/api/v1/ai/chat/stream`) → Python FastAPI (`/api/v1/ai/chat/stream`) → LangGraph
> **3 Intent chính:** `general_chat`, `system_data_query`, `system_data_chart`

---

## Hướng dẫn test

1. Đảm bảo PostgreSQL + Spring Boot (`smart-erp`) đang chạy trên cổng `8080`
2. Đảm bảo Python FastAPI (`ai_python`) đang chạy trên cổng `9000`
3. Đăng nhập vào Mini-ERP với tài khoản có quyền `can_use_ai`
4. Mở màn AI Chat, lần lượt nhập từng câu hỏi bên dưới
5. Ghi nhận kết quả theo cột: **Intent dự kiến**, **Kết quả thực tế**, **Trạng thái**, **Ghi chú**

---

## 1. GENERAL_CHAT — Hội thoại thông thường (7 câu)

| # | Câu hỏi | Intent dự kiến | Kết quả thực tế | Trạng thái | Ghi chú |
|---|---------|:--------------:|:---------------:|:----------:|---------|
| 1 | Chào bạn, bạn làm được những gì? | `general_chat` | | ⬜ | Chào hỏi, mô tả chức năng AI |
| 2 | Quy trình nhập kho từ khi tạo phiếu đến khi duyệt hoạt động như thế nào? | `general_chat` | | ⬜ | Giải thích StockReceipts lifecycle |
| 3 | Hướng dẫn tôi cách tạo đơn bán lẻ tại quầy POS | `general_chat` | | ⬜ | Hướng dẫn retail checkout |
| 4 | Điểm tích lũy khách hàng (loyalty_points) hoạt động ra sao? | `general_chat` | | ⬜ | Giải thích khái niệm |
| 5 | Sự khác nhau giữa kênh bán Retail, Wholesale và Return? | `general_chat` | | ⬜ | Giải thích order_channel |
| 6 | Phiếu xuất kho (StockDispatch) dùng để làm gì? | `general_chat` | | ⬜ | Giải thích nghiệp vụ xuất kho |
| 7 | Sổ cái tài chính (FinanceLedger) ghi nhận những loại giao dịch nào? | `general_chat` | | ⬜ | Giải thích transaction_type |

---

## 2. SYSTEM_DATA_QUERY — Tồn kho (Inventory) (7 câu)

| # | Câu hỏi | Intent dự kiến | Kết quả thực tế | Trạng thái | Ghi chú |
|---|---------|:--------------:|:---------------:|:----------:|---------|
| 8 | Hiện tại có bao nhiêu mặt hàng đang sắp hết hàng (low_stock)? | `system_data_query` | | ⬜ | `inventory` — `quantity > 0 AND quantity <= min_quantity` |
| 9 | Danh sách sản phẩm sắp hết hạn sử dụng trong 30 ngày tới | `system_data_query` | | ⬜ | `inventory` — `expiry_date <= CURRENT_DATE + 30` |
| 10 | Tổng giá trị tồn kho hiện tại là bao nhiêu? | `system_data_query` | | ⬜ | `inventory.quantity` × `productpricehistory.cost_price` |
| 11 | Tồn kho của sản phẩm có SKU là SP0001 ở những vị trí nào? | `system_data_query` | | ⬜ | `inventory` JOIN `products` + `warehouselocations` |
| 12 | Sản phẩm nào có số lượng tồn kho cao nhất? | `system_data_query` | | ⬜ | `inventory` ORDER BY `quantity DESC` |
| 13 | Có bao nhiêu sản phẩm đang hết hàng (out_of_stock)? | `system_data_query` | | ⬜ | `inventory` — `quantity = 0` |
| 14 | Tổng số lượng tồn kho theo từng danh mục sản phẩm? | `system_data_query` | | ⬜ | `inventory` JOIN `products` JOIN `categories` |

---

## 3. SYSTEM_DATA_QUERY — Phiếu nhập kho (StockReceipts) (7 câu)

| # | Câu hỏi | Intent dự kiến | Kết quả thực tế | Trạng thái | Ghi chú |
|---|---------|:--------------:|:---------------:|:----------:|---------|
| 15 | Danh sách phiếu nhập kho đang chờ duyệt (Pending) | `system_data_query` | | ⬜ | `stockreceipts` — `status = 'Pending'` |
| 16 | Tổng số phiếu nhập kho đã được duyệt (Approved) trong tháng này? | `system_data_query` | | ⬜ | `stockreceipts` — `status = 'Approved'` |
| 17 | Phiếu nhập kho nào có tổng giá trị (total_amount) cao nhất? | `system_data_query` | | ⬜ | `stockreceipts` ORDER BY `total_amount DESC` |
| 18 | Nhà cung cấp nào có nhiều phiếu nhập nhất? | `system_data_query` | | ⬜ | `stockreceipts` JOIN `suppliers` |
| 19 | Phiếu nhập PN-2026-0001 có bao nhiêu dòng chi tiết? | `system_data_query` | | ⬜ | `stockreceipts` + `stockreceiptdetails` |
| 20 | Tổng giá trị nhập hàng từ mỗi nhà cung cấp trong 90 ngày qua? | `system_data_query` | | ⬜ | `stockreceipts` JOIN `suppliers`, SUM |
| 21 | Phiếu nhập kho nào bị từ chối (Rejected) gần đây nhất? | `system_data_query` | | ⬜ | `stockreceipts` — `status = 'Rejected'` |

---

## 4. SYSTEM_DATA_QUERY — Đơn hàng (SalesOrders) (11 câu)

| # | Câu hỏi | Intent dự kiến | Kết quả thực tế | Trạng thái | Ghi chú |
|---|---------|:--------------:|:---------------:|:----------:|---------|
| 22 | Tháng này có bao nhiêu đơn bán sỉ (Wholesale)? | `system_data_query` | | ⬜ | `salesorders` — `order_channel = 'Wholesale'` |
| 23 | Tổng doanh thu từ các đơn bán lẻ (Retail) đã thanh toán (Paid)? | `system_data_query` | | ⬜ | `salesorders` — Retail + Paid, SUM(final_amount) |
| 24 | Danh sách đơn hàng đang ở trạng thái Processing | `system_data_query` | | ⬜ | `salesorders` — `status = 'Processing'` |
| 25 | Khách hàng nào có tổng chi tiêu cao nhất? | `system_data_query` | | ⬜ | `salesorders` JOIN `customers`, SUM |
| 26 | Có bao nhiêu đơn hàng bị hủy (Cancelled) trong tháng? | `system_data_query` | | ⬜ | `salesorders` — `status = 'Cancelled'` |
| 27 | Đơn bán lẻ nào được tạo gần đây nhất? | `system_data_query` | | ⬜ | `salesorders` — Retail, ORDER BY created_at DESC |
| 28 | Tổng số đơn trả hàng (Return) và tổng tiền trả? | `system_data_query` | | ⬜ | `salesorders` — `order_channel = 'Return'` |
| 29 | Top 5 sản phẩm bán chạy nhất theo số lượng? | `system_data_query` | | ⬜ | `orderdetails` JOIN `products`, SUM(quantity) |
| 30 | Đơn hàng SO-2026-0001 có những dòng sản phẩm nào? | `system_data_query` | | ⬜ | `salesorders` + `orderdetails` |
| 31 | Doanh thu theo từng kênh bán (Retail, Wholesale, Return)? | `system_data_query` | | ⬜ | `salesorders` GROUP BY order_channel |
| 32 | Khách hàng WALKIN (Khách lẻ) có bao nhiêu đơn bán lẻ? | `system_data_query` | | ⬜ | `customers` (code='WALKIN') JOIN `salesorders` |

---

## 5. SYSTEM_DATA_QUERY — Sổ cái tài chính (FinanceLedger) (8 câu)

| # | Câu hỏi | Intent dự kiến | Kết quả thực tế | Trạng thái | Ghi chú |
|---|---------|:--------------:|:---------------:|:----------:|---------|
| 33 | Tổng doanh thu (SalesRevenue) trong 90 ngày qua? | `system_data_query` | | ⬜ | `financeledger` — SalesRevenue, SUM(amount) |
| 34 | Tổng chi phí hoạt động (OperatingExpense) tháng này? | `system_data_query` | | ⬜ | `financeledger` — OperatingExpense |
| 35 | Dòng tiền ròng (net) = tổng thu trừ tổng chi trong kỳ? | `system_data_query` | | ⬜ | `financeledger` — Income vs Expense |
| 36 | Danh sách bút toán COGS từ phiếu xuất kho? | `system_data_query` | | ⬜ | `financeledger` — reference_type = 'StockDispatch' |
| 37 | Tổng giá trị vốn (PurchaseCost) từ các phiếu nhập đã duyệt? | `system_data_query` | | ⬜ | `financeledger` — PurchaseCost + StockReceipt |
| 38 | Giao dịch thu chi nào đang ở trạng thái Pending? | `system_data_query` | | ⬜ | `cashtransactions` — status = 'Pending' |
| 39 | Tổng thu chi theo từng quỹ (cash_funds)? | `system_data_query` | | ⬜ | `financeledger` JOIN `cash_funds` |
| 40 | Doanh thu và chi phí theo từng tháng trong năm nay? | `system_data_query` | | ⬜ | `financeledger` GROUP BY tháng, type |

---

## 6. SYSTEM_DATA_QUERY — Xuất kho (StockDispatches) (4 câu)

| # | Câu hỏi | Intent dự kiến | Kết quả thực tế | Trạng thái | Ghi chú |
|---|---------|:--------------:|:---------------:|:----------:|---------|
| 41 | Số lượng phiếu xuất kho đã hoàn tất (Delivered) tháng này? | `system_data_query` | | ⬜ | `stockdispatches` — status = 'Delivered' |
| 42 | Phiếu xuất kho nào đang chờ duyệt (Pending)? | `system_data_query` | | ⬜ | `stockdispatches` — status = 'Pending' |
| 43 | Tổng giá trị vốn (COGS) của các phiếu xuất đã hoàn tất? | `system_data_query` | | ⬜ | `financeledger` WHERE reference_type = 'StockDispatch' |
| 44 | Phiếu xuất PX-2026-0001 xuất những sản phẩm gì? | `system_data_query` | | ⬜ | `stockdispatches` + `stockdispatch_lines` |

---

## 7. SYSTEM_DATA_QUERY — Khách hàng & Công nợ (5 câu)

| # | Câu hỏi | Intent dự kiến | Kết quả thực tế | Trạng thái | Ghi chú |
|---|---------|:--------------:|:---------------:|:----------:|---------|
| 45 | Khách hàng nào có số đơn hàng nhiều nhất? | `system_data_query` | | ⬜ | `customers` JOIN `salesorders`, COUNT |
| 46 | Danh sách khách hàng đang có công nợ chưa thanh toán? | `system_data_query` | | ⬜ | `partnerdebts` — Customer + InDebt |
| 47 | Tổng công nợ còn lại của từng khách hàng? | `system_data_query` | | ⬜ | `partnerdebts` — total_amount - paid_amount |
| 48 | Danh sách công nợ nhà cung cấp chưa thanh toán? | `system_data_query` | | ⬜ | `partnerdebts` — Supplier + InDebt |
| 49 | Khách hàng nào có loyalty_points cao nhất? | `system_data_query` | | ⬜ | `customers` ORDER BY loyalty_points DESC |

---

## 8. SYSTEM_DATA_QUERY — Sản phẩm & Danh mục (4 câu)

| # | Câu hỏi | Intent dự kiến | Kết quả thực tế | Trạng thái | Ghi chú |
|---|---------|:--------------:|:---------------:|:----------:|---------|
| 50 | Danh sách sản phẩm theo danh mục "Đồ uống" | `system_data_query` | | ⬜ | `products` JOIN `categories` |
| 51 | Sản phẩm nào chưa có đơn hàng nào? | `system_data_query` | | ⬜ | `products` LEFT JOIN `orderdetails` |
| 52 | Top 10 sản phẩm có giá bán cao nhất? | `system_data_query` | | ⬜ | `productpricehistory` (latest) |
| 53 | Có bao nhiêu sản phẩm đang ở trạng thái Inactive? | `system_data_query` | | ⬜ | `products` — status = 'Inactive' |

---

## 9. SYSTEM_DATA_QUERY — Nhà cung cấp (3 câu)

| # | Câu hỏi | Intent dự kiến | Kết quả thực tế | Trạng thái | Ghi chú |
|---|---------|:--------------:|:---------------:|:----------:|---------|
| 54 | Nhà cung cấp nào có lần nhập hàng gần đây nhất? | `system_data_query` | | ⬜ | `suppliers` — MAX receipt_date |
| 55 | Tổng giá trị nhập hàng từ nhà cung cấp có mã NCC0001? | `system_data_query` | | ⬜ | `stockreceipts` JOIN `suppliers` |
| 56 | Nhà cung cấp nào đang ở trạng thái Inactive? | `system_data_query` | | ⬜ | `suppliers` — status = 'Inactive' |

---

## 10. SYSTEM_DATA_QUERY — Kiểm kê kho (3 câu)

| # | Câu hỏi | Intent dự kiến | Kết quả thực tế | Trạng thái | Ghi chú |
|---|---------|:--------------:|:---------------:|:----------:|---------|
| 57 | Danh sách đợt kiểm kê kho đang ở trạng thái In Progress? | `system_data_query` | | ⬜ | `inventoryauditsessions` — In Progress |
| 58 | Đợt kiểm kê KK-2026-0001 có bao nhiêu dòng kiểm kê? | `system_data_query` | | ⬜ | `inventoryauditsessions` + `inventoryauditlines` |
| 59 | Tổng số chênh lệch đã được áp dụng từ các đợt kiểm kê? | `system_data_query` | | ⬜ | `inventoryauditlines` — variance_applied_at |

---

## 11. SYSTEM_DATA_QUERY — Voucher & Khuyến mãi (3 câu)

| # | Câu hỏi | Intent dự kiến | Kết quả thực tế | Trạng thái | Ghi chú |
|---|---------|:--------------:|:---------------:|:----------:|---------|
| 60 | Danh sách voucher đang còn hiệu lực (active)? | `system_data_query` | | ⬜ | `vouchers` — is_active = true |
| 61 | Voucher DISCOUNT10 đã được sử dụng bao nhiêu lần? | `system_data_query` | | ⬜ | `vouchers` JOIN `voucher_redemptions` |
| 62 | Tổng số tiền giảm giá đã áp dụng từ voucher? | `system_data_query` | | ⬜ | `voucher_redemptions` JOIN `salesorders` |

---

## 12. SYSTEM_DATA_CHART — Yêu cầu biểu đồ (10 câu)

| # | Câu hỏi | Intent dự kiến | Chart type | Kết quả thực tế | Trạng thái | Ghi chú |
|---|---------|:--------------:|:----------:|:---------------:|:----------:|---------|
| 63 | Vẽ biểu đồ doanh thu theo tháng từ đầu năm đến nay | `system_data_chart` | line | | ⬜ | `financeledger` — SalesRevenue |
| 64 | Biểu đồ cột so sánh số đơn bán sỉ và bán lẻ theo tháng | `system_data_chart` | bar | | ⬜ | `salesorders` GROUP BY month, channel |
| 65 | Vẽ biểu đồ tròn tỷ trọng chi phí theo loại | `system_data_chart` | pie | | ⬜ | `financeledger` GROUP BY transaction_type |
| 66 | Biểu đồ tồn kho theo danh mục sản phẩm | `system_data_chart` | bar | | ⬜ | `inventory` JOIN `categories` |
| 67 | Vẽ biểu đồ doanh thu và chi phí theo từng tháng | `system_data_chart` | bar/line | | ⬜ | `financeledger` GROUP BY month |
| 68 | Biểu đồ số phiếu nhập kho theo trạng thái | `system_data_chart` | bar | | ⬜ | `stockreceipts` GROUP BY status |
| 69 | Vẽ biểu đồ đường xu hướng công nợ theo tháng | `system_data_chart` | line | | ⬜ | `partnerdebts` GROUP BY month |
| 70 | Biểu đồ tròn phân bổ đơn hàng theo kênh bán | `system_data_chart` | pie | | ⬜ | `salesorders` GROUP BY order_channel |
| 71 | Biểu đồ cột số lượng sản phẩm theo trạng thái tồn kho | `system_data_chart` | bar | | ⬜ | `inventory` — stockLevel breakdown |
| 72 | Biểu đồ doanh thu theo từng quỹ | `system_data_chart` | bar | | ⬜ | `financeledger` JOIN `cash_funds` |

---

## 13. TEST ĐA LUỒNG / NGỮ CẢNH HỘI THOẠI (5 câu)

| # | Câu hỏi (theo thứ tự) | Intent dự kiến | Kết quả thực tế | Trạng thái | Ghi chú |
|---|-----------------------|:--------------:|:---------------:|:----------:|---------|
| 73a | Doanh thu tháng 3 là bao nhiêu? | `system_data_query` | | ⬜ | Câu đầu — thiết lập context |
| 73b | Còn tháng 4 thì sao? | `system_data_query` | | ⬜ | Thread context — tham chiếu thời gian |
| 74a | Vẽ biểu đồ doanh thu theo tháng | `system_data_chart` | | ⬜ | Câu đầu — chart |
| 74b | Chuyển sang biểu đồ cột được không? | `system_data_chart` | | ⬜ | Thread context — đổi chart type |
| 75a | Tồn kho của SP0001 là bao nhiêu? | `system_data_query` | | ⬜ | Query trước |
| 75b | Vẽ biểu đồ cho số liệu đó | `system_data_chart` | | ⬜ | Query → Chart follow-up |
| 76a | Phiếu nhập kho là gì? | `general_chat` | | ⬜ | Giải thích khái niệm |
| 76b | Vậy quy trình duyệt phiếu nhập như thế nào? | `general_chat` | | ⬜ | Multi-turn general chat |
| 77a | Tổng chi phí hoạt động tháng này? | `system_data_query` | | ⬜ | Câu đầu — số liệu |
| 77b | So với tháng trước thì sao? | `system_data_query` | | ⬜ | Thread context — so sánh |

---

## 14. TEST LỖI / EDGE CASES (6 câu)

| # | Câu hỏi | Intent dự kiến | Kết quả thực tế | Trạng thái | Ghi chú |
|---|---------|:--------------:|:---------------:|:----------:|---------|
| 78 | Cho tôi xem bảng abcxyz | `system_data_query` | | ⬜ | Bảng không tồn tại → AI xử lý lỗi |
| 79 | xxx yyy zzz | `general_chat` | | ⬜ | Input vô nghĩa → fallback |
| 80 | Doanh thu ngày mai là bao nhiêu? | `system_data_query` | | ⬜ | Thời gian tương lai → xử lý hợp lý |
| 81 | SELECT * FROM users DROP TABLE users | `general_chat` | | ⬜ | SQL injection → từ chối |
| 82 | Tồn kho của sản phẩm không tồn tại? | `system_data_query` | | ⬜ | Sản phẩm không có → trả về rỗng |
| 83 | Tổng doanh thu từ bảng không có trong hệ thống? | `system_data_query` | | ⬜ | Bảng không thuộc catalog → từ chối |

---

## Tổng kết test

| Chỉ số | Giá trị |
|--------|--------:|
| **Tổng số câu hỏi** | 83 |
| **General chat** | 7 |
| **System data query** | 52 |
| **System data chart** | 10 |
| **Đa luồng** | 5 (10 lượt hỏi) |
| **Edge cases** | 6 |
| **Đạt** | — |
| **Không đạt** | — |
| **Lỗi nghiêm trọng** | — |

---

## Bảng tra cứu nhanh — Bảng DB & Intent

| Module | Bảng chính | Intent thường gặp |
|--------|-----------|:-----------------:|
| Tồn kho | `inventory`, `warehouselocations`, `productpricehistory` | `system_data_query` |
| Phiếu nhập | `stockreceipts`, `stockreceiptdetails`, `suppliers` | `system_data_query` |
| Đơn hàng | `salesorders`, `orderdetails`, `customers` | `system_data_query` / `system_data_chart` |
| Sổ cái | `financeledger`, `cashtransactions`, `cash_funds` | `system_data_query` / `system_data_chart` |
| Xuất kho | `stockdispatches`, `stockdispatch_lines` | `system_data_query` |
| Công nợ | `partnerdebts`, `customers`, `suppliers` | `system_data_query` |
| Sản phẩm | `products`, `categories`, `productunits` | `system_data_query` |
| Nhà cung cấp | `suppliers`, `stockreceipts` | `system_data_query` |
| Kiểm kê | `inventoryauditsessions`, `inventoryauditlines` | `system_data_query` |
| Voucher | `vouchers`, `voucher_redemptions` | `system_data_query` |
