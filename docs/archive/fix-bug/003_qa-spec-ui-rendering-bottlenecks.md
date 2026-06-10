# QA Specification & Test Plan - Khắc phục các lỗi nghẽn hiệu năng render (UI Rendering Bottlenecks)

> **File**: `docs/fix-bug/003_qa-spec-ui-rendering-bottlenecks.md`  
> **Người viết**: Agent QA_SPEC_WRITER  
> **Ngày cập nhật**: 03/06/2026  
> **Trạng thái**: Approved  
> **Readiness**: `QA_READY_FOR_CODING`

---

## 1. Tham chiếu & Mục tiêu kiểm thử
- **Tài liệu SRS**: [001_srs-ui-rendering-bottlenecks.md](file:///d:/do_an_tot_nghiep/project/docs/fix-bug/001_srs-ui-rendering-bottlenecks.md)
- **Tài liệu Tech Spec**: [002_tech-spec-ui-rendering-bottlenecks.md](file:///d:/do_an_tot_nghiep/project/docs/fix-bug/002_tech-spec-ui-rendering-bottlenecks.md)
- **Mục tiêu**: Đảm bảo lỗi double-render khi chuyển trang và hiện tượng re-render toàn bộ layout khi thay đổi kích thước Sidebar được khắc phục hoàn toàn mà không làm gãy vỡ giao diện người dùng, không lỗi build và các ca kiểm thử hiện tại vẫn vượt qua thành công.

---

## 2. Ma trận các chế độ lỗi (Failure-Mode Matrix)

Chúng ta cần kiểm tra các kịch bản bất thường và rủi ro biên có thể phát sinh khi tối ưu hóa hiệu năng render:

| Kịch bản lỗi tiềm ẩn (Failure Mode) | Tác động hệ thống | Phương án phòng vệ kỹ thuật | Cách kiểm thử xác minh |
| :--- | :--- | :--- | :--- |
| **`setTitle` nhận giá trị rỗng / khoảng trắng hoặc undefined** | Tiêu đề trình duyệt bị hiển thị xấu (ví dụ: ` - Mini ERP` hoặc `undefined - Mini ERP`). | Kiểm tra giá trị đầu vào bằng hàm `.trim()` và kiểm tra độ dài trước khi ghép chuỗi. | Chạy thử nghiệm bằng cách điều hướng đến trang không có tiêu đề rõ ràng, xác nhận tiêu đề hiển thị mặc định `"Mini ERP"`. |
| **Chuyển hướng trang liên tục và cực nhanh (Stress Navigation)** | Có thể xảy ra xung đột cập nhật tiêu đề trễ (Race conditions) hoặc memory leaks. | Hàm `setTitle` sử dụng `useCallback` tĩnh, không tạo bộ nhớ đệm hay state bất đồng bộ của React. | Nhấp chuột chuyển trang liên tục (lớn hơn 10 lần trong 5 giây), kiểm tra tiêu đề trang cuối cùng có khớp chính xác không và tab trình duyệt không bị đơ. |
| **Kéo thả Sidebar ra ngoài ranh giới cho phép (nhỏ hơn 192px hoặc lớn hơn 320px)** | Giao diện Sidebar bị thu nhỏ quá mức hoặc che lấp trang. | Store `useUIStore` đã có sẵn giới hạn chặn trên và chặn dưới (`width >= 192 && width <= 320`). | Thực hiện kéo rê Sidebar kịch khung trái/phải, kiểm tra biên giới hạn hiển thị. |

---

## 3. Kế hoạch kiểm thử chi tiết (Test Strategy)

### 3.1 Automated Tests (Kiểm thử tự động)
Do các thay đổi liên quan đến cấu trúc Context và layout gốc, tất cả các test case kiểm thử component hiện có của dự án cần được chạy lại để đảm bảo tính hồi quy (Regression Testing):

```powershell
# Chạy bộ test suite của frontend
npm run test --prefix frontend/mini-erp
```
Đặc biệt, dự án phải build thành công bằng TypeScript Compiler:
```powershell
npm run build --prefix frontend/mini-erp
```

### 3.2 Manual & UI Verification (Kiểm thử thủ công & Giao diện)

Chúng ta sẽ sử dụng bộ công cụ **Chrome DevTools** và **React Developer Tools** để kiểm chứng hiệu năng:

#### Ca kiểm thử 1: Xác minh loại bỏ Double-render khi chuyển hướng trang
- **Mục tiêu**: Đảm bảo chuyển trang chỉ render Layout chính và trang con đúng 1 lần duy nhất.
- **Các bước thực hiện**:
  1. Mở Chrome DevTools ➔ Tab **React Profiler**.
  2. Bật tùy chọn *"Record why each component rendered while profiling"* trong cài đặt Profiler.
  3. Bấm **Record** (Bắt đầu ghi).
  4. Nhấn chuyển tiếp từ trang Dashboard sang trang Tồn kho.
  5. Bấm **Stop** (Dừng ghi) và kiểm tra các commit:
     - Xác nhận `MainLayout` chỉ có đúng **1 Commit** (chỉ render 1 lần).
     - Kiểm tra nguyên nhân render của trang con, không có lý do *"Parent context changed"* liên quan đến `PageTitleContext`.
  6. Kiểm tra tiêu đề tab trình duyệt thay đổi chính xác sang `"Tồn kho - Mini ERP"`.

#### Ca kiểm thử 2: Xác minh cách ly render khi thay đổi độ rộng Sidebar
- **Mục tiêu**: Kéo rê Sidebar không kích hoạt re-render nội dung bên trong `<Outlet />` (các trang con như `StockPage`, `ProductsPage`...).
- **Các bước thực hiện**:
  1. Truy cập trang danh sách Tồn kho (đầy đủ bảng dữ liệu).
  2. Mở Chrome DevTools ➔ Tab **React Profiler** (hoặc tab **Performance**).
  3. Bấm **Record**.
  4. Thực hiện rê chuột kéo rộng/thu nhỏ Sidebar liên tục từ trái qua phải 5-6 lần.
  5. Bấm **Stop**.
  6. Kiểm tra biểu đồ Flamegraph:
     - Chỉ có component `Sidebar` được highlight render lại (màu vàng/xanh).
     - Component `MainLayout`, `Header` và đặc biệt là `StockPage` (nằm trong Outlet) phải hoàn toàn có màu xám (không bị render lại).
     - Xác nhận chỉ số FPS trong tab Performance duy trì ở mức cao (> 55 FPS) trong suốt thời gian kéo rê chuột.

#### Ca kiểm thử 3: Xác minh tự động mở rộng Sidebar khi điều hướng trang
- **Mục tiêu**: Đảm bảo tính năng tự động mở rộng (auto-expand) danh mục cha trên Sidebar hoạt động chính xác khi click điều hướng hoặc khi tải trang lần đầu bằng URL trực tiếp.
- **Các bước thực hiện**:
  1. Thu gọn toàn bộ các thư mục cha trên Sidebar (nhấn nút để đóng Kho hàng, Sản phẩm...).
  2. Nhấp vào menu con "Phiếu nhập kho" (hoặc truy cập trực tiếp URL `/inventory/inbound`).
  3. Xác nhận danh mục cha "Kho hàng" được tự động mở rộng trên Sidebar.
  4. Click tiếp sang "Phiếu xuất kho", kiểm tra danh mục "Kho hàng" vẫn mở và component `Sidebar` không bị chớp hay render lại 2 lần do hàm `expandItem` cập nhật Set dư thừa.
