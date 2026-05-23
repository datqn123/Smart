# Nâng cấp Node Intent — Phân tích Loại 2 & Đề xuất bổ sung

> **Ngày phân tích:** 17/05/2026
> **Nguồn:** CLASSIFICATION.md (Loại 2: 40 câu chưa rõ ràng)
> **Đối chiếu:** Table catalog (15_database.md), Module guides (05-08)

---

## 1. Phân tích chi tiết từng câu Loại 2

### Nhóm A: Từ vựng đời thường không được map → AI bắt sửa từ

| # | Câu hỏi | AI phản hồi | Bảng liên quan | Gợi ý AI có đúng không? |
|---|---------|-------------|----------------|------------------------|
| N2 | Kho mình còn bao nhiêu hàng vậy? | "Cần làm rõ thêm" | `inventory` — Current stock levels | ❌ Sai — Câu hỏi hoàn toàn hợp lệ, AI nên hiểu "hàng" = products trong inventory |
| N3 | Có món nào sắp hết hàng không, mình cần nhập thêm | "Cần làm rõ thêm" | `inventory` — Low Stock (quantity <= minQuantity) | ❌ Sai — "sắp hết hàng" = low_stock, đã có trong UI KPI cards |
| N7 | Món nào bán chạy nhất bên mình? | "«món» nên dùng «sản phẩm»" | `salesorders` + `orderdetails` | ❌ Sai — AI quá cứng nhắc, "món" là từ phổ thông của "sản phẩm" |
| N9 | Tạo giúp mình phiếu nhập 50 thùng sữa từ nhà cung cấp Vinamilk | "«thùng sữa» nên dùng «sản phẩm»" | `stockreceipts` | ❌ Sai — Đây là `inventory_data_entry`, AI nên nhận intent và để slot-filling xử lý sau |
| N10 | Thêm giúp mình mấy sản phẩm mới vào danh mục đồ uống | "«đồ uống» nên dùng «loại sản phẩm»" | `categories`, `products` | ❌ Sai — Đây là `catalog_data_entry`, AI nên nhận intent đúng |
| N53 | Phiếu nhập kho là gì vậy? | "Cần làm rõ thêm" | `stockreceipts` | ⚠️ Partial — Đây là general_chat (giải thích khái niệm), AI không nên bắt sửa từ |
| N95 | Từ lúc tạo phiếu đến khi duyệt thì nhập kho làm sao? | "nên dùng «từ lúc tạo phiếu nhập kho đến khi duyệt thì nhập kho»" | `stockreceipts` workflow | ❌ Sai — Câu hỏi hợp lệ, AI nên hiểu là hỏi quy trình |
| N109 | Top 5 món bán chạy nhất theo số lượng là gì? | "«món» nên dùng «sản phẩm»" | `salesorders` + `orderdetails` | ❌ Sai — Lặp lại vấn đề N7 |

**Vấn đề chung:** Intent prompt không có hướng dẫn về từ vựng đời thường → AI LLM tự "bắt lỗi" từ ngữ thay vì phân loại intent.

---

### Nhóm B: AI từ chối do "không hỗ trợ" — nhưng table CÓ dữ liệu

| # | Câu hỏi | AI từ chối | Bảng liên quan | Thực tế table có không? |
|---|---------|-----------|----------------|------------------------|
| N48 | Ai là người mới giao hàng cho mình gần đây nhất? | "ERP không hỗ trợ quản lý giao hàng" | `stockreceipts` (receiptDate, supplierId) | ✅ CÓ — supplier có receipt gần nhất = người giao hàng gần nhất |
| N59 | Hàng mã SP0001 đang nằm ở kho nào? | "lỗi kết nối hệ thống" | `inventory` + `warehouselocations` | ✅ CÓ — inventory JOIN warehouselocations theo locationId |
| N60 | Mình đã nhập bao nhiêu tiền từ nhà cung cấp NCC0001? | "ERP không hỗ trợ truy vấn về số tiền nhập từ NCC" | `stockreceipts` + `stockreceiptdetails` | ✅ CÓ — SUM(costPrice × quantity) WHERE supplierId = NCC0001 |
| N62 | Mình còn nợ nhà cung cấp nào chưa trả không? | "ERP không hỗ trợ truy vấn về nợ NCC" | `partnerdebts` (partnerType = "Supplier") | ✅ CÓ — partnerdebts có partnerType Supplier |
| N66 | Mình đã giảm giá cho khách tổng cộng bao nhiêu tiền? | "ERP không hỗ trợ truy vấn về giảm giá" | `vouchers` + `voucher_redemptions` + `salesorders.discountAmount` | ✅ CÓ — SUM(discountAmount) từ salesorders |
| N67 | Có hàng nào hết hạn trong vòng 1 tháng tới không? | "ERP không hỗ trợ tính năng kiểm tra hàng hết hạn" | `inventory` (expiryDate, isExpiringSoon) | ✅ CÓ — UI có KPI "Expiring Soon Count", điều kiện: expiryDate <= today+30days |
| N68 | Có sản phẩm nào mình đang không bán nữa không? | "ERP không hỗ trợ tính năng kiểm tra sản phẩm không bán nữa" | `products` (status = "Inactive") | ✅ CÓ — products có trường status: Active/Inactive |
| N80 | Ai đang nợ tiền mình và nợ bao nhiêu? | "Không tìm thấy thông tin" | `partnerdebts` (partnerType = "Customer", status = "InDebt") | ✅ CÓ — partnerdebts có partnerType Customer |
| N113 | SP0001 đang nằm ở những vị trí nào trong kho? | "Không tìm thấy thông tin về vị trí" | `inventory` + `warehouselocations` | ✅ CÓ — inventory JOIN warehouselocations |
| N124 | Danh sách sản phẩm nào sắp hết hạn trong 30 ngày tới | Gợi ý câu khác, không có danh sách | `inventory` (expiryDate <= today+30days) | ✅ CÓ — isExpiringSoon = expiryDate <= today+30days |
| N133 | Nhà cung cấp nào đang không hoạt động? | "Không tìm thấy NCC nào đang không hoạt động" | `suppliers` (status = "Inactive") | ✅ CÓ — suppliers có trường status |

**Vấn đề chung:** Intent prompt không mô tả đầy đủ khả năng của từng bảng → AI LLM không biết table nào có thể trả lời câu hỏi nào → từ chối sai.

---

### Nhóm C: Không tìm thấy dữ liệu — do điều kiện lọc sai hoặc data trống

| # | Câu hỏi | AI phản hồi | Bảng liên quan | Vấn đề thực tế |
|---|---------|-------------|----------------|----------------|
| N5 | Ai đang nợ mình nhiều tiền nhất? | "Không tìm thấy thông tin" | `partnerdebts` | Có thể không có dữ liệu InDebt, hoặc query sai điều kiện |
| N19 | Có đơn nào bị hủy gần đây không? | "Không tìm thấy đơn hàng bị hủy gần đây" | `salesorders` (status = "Cancelled") | "gần đây" không có định nghĩa thời gian rõ ràng |
| N20 | Mình đã xuất kho những gì trong tuần này? | "Không tìm thấy dữ liệu xuất kho trong tuần này" | `stockdispatches` | Có thể không có dispatch trong tuần hiện tại |
| N23 | Tháng này so với tháng trước thì bán tốt hơn hay tệ hơn? | Chỉ có dữ liệu tháng 5 | `salesorders` | Query chỉ trả 1 tháng, không so sánh được |
| N24 | Mình đang có mã giảm giá nào còn dùng được không? | "Không có mã giảm giá nào đang còn hiệu lực" | `vouchers` (isActive, validity period) | Có thể đúng — không có voucher active |
| N25 | Lần kiểm kho gần nhất là khi nào, có chênh lệch gì không? | "Không tìm thấy thông tin" | `inventoryauditsessions` | Có thể không có audit session nào |
| N28 | Đơn SO-2026-0001 bán những gì vậy? | "Không tìm thấy đơn hàng SO-2026-0001" | `salesorders` + `orderdetails` | Mã đơn có thể không tồn tại trong DB (demo data khác) |
| N31 | Có nhà cung cấp nào mình không liên hệ nữa không? | "Không tìm thấy NCC nào không có hoạt động" | `suppliers` + `stockreceipts` | Query có thể sai — cần tìm supplier không có receipt trong X ngày |
| N34 | Có ai trả hàng lại mình gần đây không? | "Không tìm thấy dữ liệu trả hàng" | `salesorders` (orderChannel = "Return") | Có thể không có return order nào |
| N47 | Phiếu xuất PX-2026-0001 xuất những gì vậy? | "Không tìm thấy thông tin" | `stockdispatches` + `stockdispatch_lines` | Mã PX có thể không tồn tại (demo data bắt đầu từ PX-2026-0024) |
| N49 | Cho mình xem tồn kho của cái sản phẩm không có trong hệ thống | "ERP không hỗ trợ" | N/A — edge case | ✅ AI xử lý đúng — từ chối sản phẩm không tồn tại |
| N51 | Còn tháng 4 thì sao? | "Hiện chưa tính được tổng doanh thu" | `salesorders` | Multi-turn mất context, không biết "tháng 4" = doanh thu |
| N56 | So với tháng trước thì sao? | "Không tìm thấy dữ liệu tổng chi phí" | `financeledger` | Multi-turn mất context |
| N86 | Có món nào hết sạch hàng trong kho không? | "max_sql_attempts, attempts=3" | `inventory` (quantity = 0) | Lỗi SQL, không phải do intent |
| N87 | Tháng 3 vừa rồi mình thu được bao nhiêu? | "Hiện chưa tính được tổng doanh thu" | `salesorders` | Query có thể sai điều kiện tháng 3 |
| N88 | SP0001 còn bao nhiêu cái trong kho? | "Hiện chưa có thông tin" | `inventory` | SP0001 có thể không tồn tại trong DB (demo data dùng SKU khác) |
| N96 | Tồn kho của SP0001 là bao nhiêu? | "Không tìm thấy thông tin" | `inventory` |同上 — SP0001 không có trong demo data |
| N111 | Tháng 3 bán được bao nhiêu? | "Không tìm thấy dữ liệu bán hàng cho tháng 3" | `salesorders` | Query sai điều kiện tháng |
| N112 | Còn tháng 4 thì sao? | "Hiện chưa tính được tổng doanh thu" | `salesorders` | Multi-turn mất context |
| N127 | Tổng giá trị nhập hàng từ NCC0001 là bao nhiêu? | "Hiện chưa tính được tổng giá trị" | `stockreceipts` + `stockreceiptdetails` | NCC0001 có thể không tồn tại (demo data dùng NCC seed V10 A/B/C) |

**Vấn đề chung:** Một số do data trống/demo data khác mã, một số do multi-turn mất context, một số do query sai điều kiện thời gian.

---

## 2. Đề xuất bổ sung vào file intent.md

### 2.1. Bổ sung quy tắc từ vựng đời thường

Thêm vào phần **Quy tắc**:

```markdown
## Quy tắc xử lý từ vựng đời thường

Người dùng thường dùng từ phổ thông, không dùng thuật ngữ hệ thống. AI PHẢI tự động map:

| Từ đời thường | Map sang khái niệm hệ thống |
|--------------|---------------------------|
| món, hàng, đồ, sản phẩm | `products` |
| kho, tồn kho, hàng trong kho | `inventory` |
| sắp hết hàng, low stock | `inventory` (quantity <= minQuantity) |
| hết sạch hàng, hết hàng, out of stock | `inventory` (quantity = 0) |
| sắp hết hạn, hết hạn | `inventory` (expiryDate) |
| nhập hàng, phiếu nhập, PN | `stockreceipts` |
| xuất hàng, phiếu xuất, PX | `stockdispatches` |
| đơn hàng, đơn bán, đơn | `salesorders` |
| đơn hủy | `salesorders` (status = "Cancelled") |
| đơn trả hàng, trả hàng | `salesorders` (orderChannel = "Return") |
| khách nợ, công nợ khách hàng | `partnerdebts` (partnerType = "Customer") |
| nợ nhà cung cấp, nợ NCC | `partnerdebts` (partnerType = "Supplier") |
| nhà cung cấp, NCC, bên giao hàng | `suppliers` |
| khách hàng, khách, khách lẻ | `customers` |
| khách vãng lai, khách lẻ | `customers` (WALKIN) |
| mã giảm giá, voucher, coupon | `vouchers` |
| giảm giá, discount | `salesorders.discountAmount` |
| tiền vốn, giá vốn, COGS | `financeledger` (PurchaseCost) |
| doanh thu, thu, bán được | `financeledger` (SalesRevenue) / `salesorders` |
| chi phí, chi, expense | `financeledger` (OperatingExpense) |
| lãi, lợi nhuận | Revenue - Expense |
| giao hàng, người giao hàng | `stockreceipts` (supplier có receipt gần nhất) |
| vị trí trong kho, kho nào | `warehouselocations` |
| không bán nữa, ngưng hoạt động | `products` (status = "Inactive") |
| NCC không hoạt động | `suppliers` (status = "Inactive") |
| kiểm kho, kiểm kê | `inventoryauditsessions` |
| chênh lệch kiểm kê | `inventoryauditlines` (variance) |
| quỹ tiền mặt, quỹ | `cash_funds` |
| thu chi, giao dịch thu chi | `cashtransactions` |
| bút toán, sổ cái | `financeledger` |
| nhóm hàng, danh mục, loại | `categories` |
| bán chạy nhất | `orderdetails` (SUM quantity DESC) |
| gần đây, mới nhất | ORDER BY created_at DESC LIMIT |
| tháng này, trong tháng | DATE_TRUNC('month', CURRENT_DATE) |
| tháng trước | DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month') |
| tuần này | DATE_TRUNC('week', CURRENT_DATE) |
| 30 ngày tới, 1 tháng tới | CURRENT_DATE + INTERVAL '30 days' |
| 3 tháng qua, 90 ngày qua | CURRENT_DATE - INTERVAL '90 days' |

**QUAN TRỌNG:** Không bắt người dùng sửa từ. Nếu câu dùng từ đời thường, AI vẫn phân loại intent bình thường và để các node sau xử lý.
```

### 2.2. Bổ sung mô tả khả năng từng bảng vào quy tắc intent

Thêm vào phần **Năm loại đích** — mở rộng mô tả `system_data_query`:

```markdown
- **system_data_query** — người dùng cần câu trả lời bám dữ liệu vận hành thực (thống kê, bảng kết quả, đối chiếu, mức số liệu hiện tại trong hệ thống) dưới dạng chữ / bảng / số, **không** yêu cầu vẽ biểu đồ.

  **Bao gồm nhưng không giới hạn:**
  - Tồn kho: tổng số lượng, giá trị tồn, low stock, out of stock, expiring soon, theo vị trí/kho, theo nhóm hàng
  - Nhập/xuất: phiếu nhập, phiếu xuất, theo trạng thái (Pending/Approved/Rejected/Delivered), theo nhà cung cấp, theo thời gian
  - Đơn hàng: theo kênh (Retail/Wholesale/Return), theo trạng thái (Pending/Processing/Delivered/Cancelled), theo khách hàng
  - Tài chính: doanh thu, chi phí, lợi nhuận, công nợ khách hàng, công nợ nhà cung cấp, giao dịch thu chi, quỹ tiền mặt, bút toán sổ cái
  - Sản phẩm: theo danh mục, theo trạng thái (Active/Inactive), giá bán, top bán chạy, sản phẩm chưa có đơn
  - Kiểm kê: đợt kiểm kê, chênh lệch, variance
  - Voucher: mã giảm giá active, đã sử dụng, tổng tiền giảm giá
  - So sánh: tháng này vs tháng trước, quý này vs quý trước, theo thời gian
```

### 2.3. Bổ sung quy tắc multi-turn context

Thêm vào phần **Quy tắc**:

```markdown
## Quy tắc xử lý multi-turn

- Khi câu hỏi ngắn, thiếu chủ ngữ ("Còn tháng 4 thì sao?", "So với tháng trước thì sao?", "Vẽ biểu đồ cho số liệu đó") → AI phải dựa vào ngữ cảnh hội thoại trước đó để hiểu ý định.
- Nếu câu trước hỏi về doanh thu → "tháng 4 thì sao?" = doanh thu tháng 4.
- Nếu câu trước hỏi về chi phí → "so với tháng trước" = so sánh chi phí.
- Nếu câu trước có số liệu → "vẽ biểu đồ cho số liệu đó" = chart từ dữ liệu vừa trả lời.
- **Không** trả lời "không tìm thấy dữ liệu" khi câu hỏi multi-turn thiếu context — thay vào đó, hỏi lại user để xác nhận.
```

### 2.4. Bổ sung quy tắc xử lý edge case

Thêm vào phần **Quy tắc**:

```markdown
## Quy tắc xử lý edge case

- **Mã không tồn tại** (SP0001, PX-2026-0001, SO-2026-0001...): Trả lời "không tìm thấy [loại] với mã này trong hệ thống" và gợi ý cách tìm đúng. **Không** nói "hệ thống không hỗ trợ".
- **Không có dữ liệu trong khoảng thời gian**: Trả lời "không có [dữ liệu] trong [khoảng thời gian]" và gợi ý mở rộng thời gian. **Không** nói "không tìm thấy dữ liệu".
- **Từ chối lịch sự**: Khi không thể trả lời, giải thích lý do cụ thể (không có dữ liệu, mã không tồn tại, ngoài phạm vi) — không dùng câu chung chung "hệ thống không hỗ trợ".
```

---

## 3. Tóm tắt nội dung cần thêm vào intent.md

| STT | Nội dung bổ sung | Vị trí trong file |
|-----|-----------------|-------------------|
| 1 | Bảng map từ vựng đời thường → khái niệm hệ thống (30+ mục) | Phần **Quy tắc** — thêm section mới |
| 2 | Quy tắc "không bắt người dùng sửa từ" | Phần **Quy tắc** |
| 3 | Mở rộng mô tả `system_data_query` với danh sách khả năng | Phần **Năm loại đích** |
| 4 | Quy tắc xử lý multi-turn context | Phần **Quy tắc** — thêm section mới |
| 5 | Quy tắc xử lý edge case (mã không tồn tại, data trống) | Phần **Quy tắc** — thêm section mới |
| 6 | Quy tắc từ chối lịch sự với lý do cụ thể | Phần **Quy tắc** |

---

## 4. Các câu Loại 2 KHÔNG cần sửa intent (do nguyên nhân khác)

| # | Câu hỏi | Nguyên nhân thực sự | Hướng xử lý |
|---|---------|-------------------|-------------|
| N86 | Có món nào hết sạch hàng trong kho không? | max_sql_attempts — lỗi SQL node | Tăng max_attempts hoặc optimize query |
| N22 | Tổng giá trị hàng tồn kho của mình là bao nhiêu? | Lỗi kết nối hệ thống | Kiểm tra DB connection |
| N29 | Cho mình xem biểu đồ chi phí theo từng loại | max_sql_attempts | Tăng max_attempts |
| N33 | Khách vãng lai mua lẻ tổng cộng được bao nhiêu? | HTTP timeout 124s | Optimize query hoặc tăng timeout |
| N61 | Phiếu PN-2026-0001 có bao nhiêu dòng chi tiết? | max_sql_attempts | Tăng max_attempts |
| N65 | Mã DISCOUNT10 đã có bao nhiêu người dùng? | max_sql_attempts | Tăng max_attempts |

→ 6 câu này thuộc **Loại 3** (lỗi kỹ thuật), không liên quan intent classification.

---

## 5. File intent.md đề xuất (full)

Xem file: `INTENT_UPGRADE_PROPOSAL.md`
