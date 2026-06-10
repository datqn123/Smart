# QA SPEC 025 — Invoice History Upgrade (SRS-020 / TECH-024)

**Ngày:** 2026-06-06
**Superpowers:** TDD

---

## P0 — Smoke (must pass trước khi merge)

| ID | Kịch bản | Kết quả mong đợi |
|----|----------|-----------------|
| P0-01 | Mở trang "Lịch sử hóa đơn" | Toolbar render không có `<select>` rời ở phía trên bảng |
| P0-02 | Toolbar hiển thị 3 pill tabs status | "Tất cả", "Hoàn thành", "Đã huỷ" đều hiện |
| P0-03 | Toolbar hiển thị 4 pill tabs payment | "Tất cả", "Đã TT", "Chưa TT", "Một phần" đều hiện |
| P0-04 | Sort dropdown nằm trong toolbar | Dropdown sort nằm trong dòng 3 của toolbar (không còn ngoài toolbar) |
| P0-05 | Table có cột "Thanh toán" | Header "Thanh toán" xuất hiện sau "Thành tiền" |
| P0-06 | Table có cột "Trạng thái" | Header "Trạng thái" xuất hiện sau "Thanh toán" |
| P0-07 | `npx tsc --noEmit` | 0 errors |

## P1 — Functional

| ID | Kịch bản | Kết quả mong đợi |
|----|----------|-----------------|
| P1-01 | Click pill "Hoàn thành" | Chỉ hiển thị hàng có status = Delivered; pill "Hoàn thành" active (bg-slate-900) |
| P1-02 | Click pill "Đã huỷ" | Chỉ hiển thị hàng có status = Cancelled |
| P1-03 | Click pill "Tất cả" (status) | Hiển thị lại tất cả hàng |
| P1-04 | Click pill "Đã TT" | Chỉ hiển thị hàng paymentStatus = Paid |
| P1-05 | Click pill "Chưa TT" | Chỉ hiển thị hàng paymentStatus = Unpaid |
| P1-06 | Kết hợp: "Hoàn thành" + "Đã TT" | Chỉ hiển thị hàng Delivered & Paid |
| P1-07 | PaymentBadge Paid | Badge xanh "Đã TT" |
| P1-08 | PaymentBadge Unpaid | Badge đỏ "Chưa TT" |
| P1-09 | PaymentBadge Partial | Badge cam "Một phần" |
| P1-10 | StatusBadge Delivered | Badge xanh "Hoàn thành" |
| P1-11 | StatusBadge Cancelled | Badge đỏ "Đã huỷ" |
| P1-12 | Không còn TypeBadge "Bán lẻ" trên mỗi hàng | Không thấy badge "Bán lẻ" / "Bán buôn" trong cột Khách hàng |
| P1-13 | Thay đổi sort qua dropdown trong toolbar | Danh sách re-fetch với sort mới |
| P1-14 | Search + date range vẫn hoạt động | Tìm kiếm theo mã / tên KH; lọc theo ngày vẫn hoạt động |

## P1 — Detail Dialog

| ID | Kịch bản | Kết quả mong đợi |
|----|----------|-----------------|
| P1-15 | Xem chi tiết đơn có `shippingAddress` | Hiển thị địa chỉ thực từ API, không hiện "123 Đường ABC" |
| P1-16 | Xem chi tiết đơn POS (shippingAddress = null) | Hiển thị "Tại cửa hàng (POS)" |
| P1-17 | Ô "Trạng thái thanh toán" | Hiển thị "Đã thanh toán" / "Chưa thanh toán" / "Thanh toán một phần" (tiếng Việt) |
| P1-18 | Xem đơn Delivered | Progress tracker 4 bước render bình thường; không có banner đỏ |
| P1-19 | Xem đơn Cancelled | Banner đỏ "Đơn hàng đã bị huỷ" thay progress tracker |
| P1-20 | Xem đơn Cancelled có `cancelledAt` | Banner đỏ hiển thị thêm "Thời điểm huỷ: dd/MM/yyyy" |
| P1-21 | Xem đơn có `voucherCode` | Section "Voucher áp dụng" hiện với mã voucher |
| P1-22 | Xem đơn không có voucher | Không có section voucher |
| P1-23 | Xem đơn có `posShiftRef` | Section "Ca POS" hiện với mã ca |
| P1-24 | Xem đơn không có posShiftRef | Không có section Ca POS |

## P2 — Regression (các page khác không bị ảnh hưởng)

| ID | Kịch bản | Kết quả mong đợi |
|----|----------|-----------------|
| P2-01 | `ReturnsPage` — mở detail dialog | Dialog mở bình thường; không crash (không có `detailDto`) |
| P2-02 | `ApprovalHistoryPage` — mở detail dialog | Dialog mở bình thường |
| P2-03 | `ReturnsPage` — `OrderTable` render | Hiển thị `TypeBadge` ("Trả hàng") bình thường (không truyền `hideTypeBadge`) |
| P2-04 | `WholesalePage` (wholesale) | Không tồn tại trong codebase — `WholesalePage` đã là trang retail history |
| P2-05 | Pagination prev/next vẫn hoạt động | Điều hướng trang không bị phá vỡ |
| P2-06 | Indicator "Đang cập nhật..." khi re-fetch | Vẫn hiển thị khi `isListFetching` |

## Failure mode matrix

| Điều kiện | Hành vi mong đợi |
|-----------|-----------------|
| `detailLines` chưa load (empty array) | Dialog hiển thị bảng chi tiết rỗng, không crash |
| `detailQuery.data` = undefined (loading) | `detailDto` = undefined → địa chỉ = "Tại cửa hàng (POS)" |
| `orders` = [] sau filter | Table hiển thị "Không tìm thấy đơn hàng nào" |
| Sort `<select>` thay đổi khi đang filter | Filter client-side vẫn áp dụng trên kết quả mới |
