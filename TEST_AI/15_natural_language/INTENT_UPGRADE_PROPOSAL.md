# Đề xuất nâng cấp intent.md — Natural Language Test Analysis

> **Ngày:** 17/05/2026
> **Nguồn:** Phân tích 40 câu Loại 2 từ CLASSIFICATION.md
> **Đối chiếu:** Table catalog (15_database.md), Module guides (05_inventory, 06_catalog, 07_orders, 08_finance)

---

## Nội dung cần BỔ SUNG vào `app/prompts/agents/intent.md`

### 1. Bảng map từ vựng đời thường

**Vị trí:** Thêm vào sau phần "Năm loại đích", trước phần "Quy tắc"

```markdown
## Ánh xạ từ vựng đời thường

Người dùng thường dùng từ phổ thông, không dùng thuật ngữ hệ thống. AI PHẢI tự động hiểu và phân loại đúng intent — **không** bắt người dùng sửa từ.

| Từ/cụm từ đời thường | Khái niệm hệ thống | Bảng liên quan |
|---|---|---|
| món, hàng, đồ, vật phẩm | sản phẩm | `products` |
| kho, tồn kho, hàng trong kho, còn bao nhiêu hàng | tồn kho hiện tại | `inventory` |
| sắp hết hàng, low stock, sắp hết | mức tồn tối thiểu | `inventory` (quantity <= minQuantity) |
| hết sạch hàng, hết hàng, out of stock, không còn hàng | hết tồn kho | `inventory` (quantity = 0) |
| sắp hết hạn, hết hạn sử dụng | ngày hết hạn | `inventory` (expiryDate) |
| nhập hàng, phiếu nhập, PN, hàng về | phiếu nhập kho | `stockreceipts` |
| xuất hàng, phiếu xuất, PX, hàng đi | phiếu xuất kho | `stockdispatches` |
| đơn hàng, đơn bán, đơn, order | đơn bán hàng | `salesorders` |
| đơn hủy, hủy đơn | đơn đã hủy | `salesorders` (status = "Cancelled") |
| đơn trả hàng, trả hàng, hoàn hàng | đơn trả hàng | `salesorders` (orderChannel = "Return") |
| khách nợ, công nợ khách hàng, ai nợ tiền mình | công nợ khách hàng | `partnerdebts` (partnerType = "Customer") |
| nợ nhà cung cấp, nợ NCC, mình nợ ai | công nợ nhà cung cấp | `partnerdebts` (partnerType = "Supplier") |
| nhà cung cấp, NCC, bên giao hàng, bên nhập hàng | nhà cung cấp | `suppliers` |
| khách hàng, khách, khách mua hàng | khách hàng | `customers` |
| khách vãng lai, khách lẻ, khách walk-in | khách lẻ | `customers` (WALKIN) |
| mã giảm giá, voucher, coupon, code giảm giá | mã khuyến mãi | `vouchers` |
| giảm giá, discount, tiền giảm | số tiền giảm giá | `salesorders.discountAmount` |
| tiền vốn, giá vốn, COGS, vốn hàng | giá vốn hàng bán | `financeledger` (PurchaseCost) |
| doanh thu, thu, bán được, tiền bán | tổng doanh thu | `financeledger` (SalesRevenue) / `salesorders` |
| chi phí, chi, expense, tiền chi | chi phí hoạt động | `financeledger` (OperatingExpense) |
| lãi, lợi nhuận, lời, còn dư | lợi nhuận = thu - chi | Revenue - Expense |
| ai giao hàng gần đây, bên nào mới giao | nhà cung cấp có phiếu nhập gần nhất | `stockreceipts` (MAX receiptDate) |
| vị trí trong kho, ở kho nào, nằm ở đâu | vị trí kho hàng | `warehouselocations` |
| không bán nữa, ngưng bán, dừng bán | sản phẩm không hoạt động | `products` (status = "Inactive") |
| NCC không hoạt động, NCC ngưng | nhà cung cấp không hoạt động | `suppliers` (status = "Inactive") |
| kiểm kho, kiểm kê, đếm kho | đợt kiểm kê | `inventoryauditsessions` |
| chênh lệch kiểm kê, lệch kho | chênh lệch kiểm kê | `inventoryauditlines` (variance) |
| quỹ tiền mặt, quỹ, két | quỹ tiền | `cash_funds` |
| thu chi, giao dịch thu chi, phiếu thu chi | giao dịch tiền mặt | `cashtransactions` |
| bút toán, sổ cái, sổ sách | sổ cái tài chính | `financeledger` |
| nhóm hàng, danh mục, loại hàng, mục | danh mục sản phẩm | `categories` |
| bán chạy nhất, bán nhiều nhất | top sản phẩm theo số lượng bán | `orderdetails` (SUM quantity DESC) |
| gần đây, mới nhất, cuối cùng | sắp xếp theo thời gian mới nhất | ORDER BY created_at DESC LIMIT |
| tháng này, trong tháng này | tháng hiện tại | DATE_TRUNC('month', CURRENT_DATE) |
| tháng trước, tháng rồi | tháng trước đó | DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month') |
| tuần này, trong tuần | tuần hiện tại | DATE_TRUNC('week', CURRENT_DATE) |
| 30 ngày tới, 1 tháng tới, tháng sau | trong vòng 30 ngày | CURRENT_DATE + INTERVAL '30 days' |
| 3 tháng qua, 90 ngày qua, quý này | trong 90 ngày | CURRENT_DATE - INTERVAL '90 days' |
| mỗi quý, theo quý | theo quý | DATE_TRUNC('quarter', ...) |
| mỗi tháng, theo tháng | theo tháng | DATE_TRUNC('month', ...) |
| bao nhiêu, tổng, số lượng | yêu cầu số liệu thống kê | → system_data_query |
| liệt kê, danh sách, xem | yêu cầu danh sách | → system_data_query |
| vẽ, biểu đồ, đồ thị, chart | yêu cầu biểu đồ | → system_data_chart |
| so sánh, hơn, kém, tốt hơn, tệ hơn | so sánh số liệu | → system_data_query |
| tạo, lập, thêm mới, thêm | tạo mới dữ liệu | → catalog_data_entry hoặc inventory_data_entry |
```

### 2. Mở rộng mô tả system_data_query

**Vị trí:** Thay thế mô tả hiện tại của `system_data_query` trong phần "Năm loại đích"

```markdown
- **system_data_query** — người dùng cần câu trả lời bám dữ liệu vận hành thực (thống kê, bảng kết quả, đối chiếu, mức số liệu hiện tại trong hệ thống) dưới dạng chữ / bảng / số, **không** yêu cầu vẽ biểu đồ.

  **Phạm vi bao gồm:**
  - **Tồn kho:** tổng số lượng, giá trị tồn, low stock, out of stock, expiring soon, theo vị trí/kho, theo nhóm hàng, theo sản phẩm cụ thể
  - **Nhập/xuất:** phiếu nhập, phiếu xuất, theo trạng thái (Pending/Approved/Rejected/Delivered/WaitingDispatch), theo nhà cung cấp, theo thời gian, chi tiết dòng
  - **Đơn hàng:** theo kênh (Retail/Wholesale/Return), theo trạng thái (Pending/Processing/Delivered/Cancelled), theo khách hàng, doanh thu theo kênh
  - **Tài chính:** doanh thu, chi phí, lợi nhuận, công nợ khách hàng, công nợ nhà cung cấp, giao dịch thu chi, quỹ tiền mặt, bút toán sổ cái, COGS, giá vốn
  - **Sản phẩm:** theo danh mục, theo trạng thái (Active/Inactive), giá bán cao nhất/thấp nhất, top bán chạy, sản phẩm chưa có đơn, sản phẩm không bán nữa
  - **Kiểm kê:** đợt kiểm kê, chênh lệch, variance, trạng thái (Pending/In Progress/Completed)
  - **Voucher:** mã giảm giá active, đã sử dụng, tổng tiền giảm giá, số lần dùng
  - **Khách hàng/NCC:** top khách mua nhiều, top NCC nhập nhiều, khách nợ, NCC nợ, khách lẻ, NCC không hoạt động
  - **So sánh thời gian:** tháng này vs tháng trước, quý này vs quý trước, xu hướng theo thời gian
```

### 3. Quy tắc multi-turn

**Vị trí:** Thêm vào phần "Quy tắc"

```markdown
## Quy tắc xử lý multi-turn

- Khi câu hỏi ngắn, thiếu chủ ngữ hoặc tham chiếu ("Còn tháng 4 thì sao?", "So với tháng trước thì sao?", "Vẽ biểu đồ cho số liệu đó", "Thế còn X?") → AI phải dựa vào **ngữ cảnh hội thoại trước đó** để hiểu ý định.
- Nếu câu trước hỏi về **doanh thu** → "tháng 4 thì sao?" = doanh thu tháng 4 → `system_data_query`
- Nếu câu trước hỏi về **chi phí** → "so với tháng trước" = so sánh chi phí → `system_data_query`
- Nếu câu trước có **số liệu/bảng** → "vẽ biểu đồ cho số liệu đó" = chart từ dữ liệu vừa trả lời → `system_data_chart`
- Nếu câu trước giải thích **khái niệm** → "vậy quy trình thì sao?" = hỏi tiếp về khái niệm → `general_chat`
- **Không** trả lời "không tìm thấy dữ liệu" khi câu hỏi multi-turn thiếu context — thay vào đó, giữ nguyên intent từ câu trước và để node sau xử lý.
```

### 4. Quy tắc xử lý edge case

**Vị trí:** Thêm vào phần "Quy tắc"

```markdown
## Quy tắc xử lý edge case

- **Mã không tồn tại** (SP0001, PX-2026-0001, SO-2026-0001, NCC0001...): Phân loại intent bình thường (`system_data_query`). Việc trả lời "không tìm thấy" là trách nhiệm của node SQL, không phải của intent node.
- **Khoảng thời gian không có dữ liệu**: Phân loại intent bình thường. Node SQL sẽ trả về kết quả rỗng và node trả lời sẽ xử lý.
- **Câu hỏi về sản phẩm/NCC/đơn không tồn tại**: Vẫn phân loại đúng intent dựa trên từ khóa. Không từ chối ở cấp độ intent.
- **Từ vựng không chuẩn**: AI PHẢI tự động map từ đời thường sang khái niệm hệ thống (xem bảng ánh xạ). **Tuyệt đối không** bắt người dùng sửa từ như "Trong Mini ERP, «món» nên dùng «sản phẩm»".
```

### 5. Quy tắc từ chối lịch sự

**Vị trí:** Thêm vào phần "Quy tắc"

```markdown
## Quy tắc trả lời khi không có dữ liệu

- Khi không thể trả lời, giải thích **lý do cụ thể**: "không có dữ liệu trong khoảng thời gian này", "mã này không tồn tại trong hệ thống", "chưa có hoạt động nào trong tuần này".
- **Không** dùng câu chung chung như "hệ thống không hỗ trợ", "không tìm thấy thông tin", "lỗi kết nối hệ thống" — những câu này gây hiểu lầm cho người dùng.
- Gợi ý **hành động cụ thể**: "Bạn có thể thử hỏi về...", "Thử mở rộng thời gian sang...", "Kiểm tra lại mã...".
```

---

## Tổng hợp thay đổi

| # | Thay đổi | Loại vấn đề | Số câu Loại 2 ảnh hưởng |
|---|----------|-------------|-------------------------|
| 1 | Bảng map từ vựng đời thường | AI bắt sửa từ sai | N2, N3, N7, N9, N10, N53, N95, N109 (8 câu) |
| 2 | Mở rộng system_data_query | AI không biết table có gì | N48, N59, N60, N62, N66, N67, N68, N80, N113, N124, N133 (11 câu) |
| 3 | Quy tắc multi-turn | Mất context follow-up | N51, N56, N112 (3 câu) |
| 4 | Quy tắc edge case | Từ chối sai mã không tồn tại | N28, N47, N88, N96, N127 (5 câu) |
| 5 | Quy tắc từ chối lịch sự | Trả lời chung chung | N5, N19, N20, N23, N24, N25, N31, N34, N87 (9 câu) |

**Tổng cải thiện:** 36/40 câu Loại 2 (90%)

**4 câu còn lại** do nguyên nhân kỹ thuật (max_sql_attempts, timeout, data trống thực sự):
- N86: max_sql_attempts → xử lý ở SQL node
- N22: lỗi kết nối → xử lý ở infrastructure
- N29: max_sql_attempts → xử lý ở SQL node
- N61: max_sql_attempts → xử lý ở SQL node
