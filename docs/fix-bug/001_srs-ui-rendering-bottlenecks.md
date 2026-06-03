# SRS - Khắc phục các lỗi nghẽn hiệu năng render (UI Rendering Bottlenecks)

> **File**: `docs/fix-bug/001_srs-ui-rendering-bottlenecks.md`  
> **Người viết**: Agent SRS_WRITER  
> **Ngày cập nhật**: 03/06/2026  
> **Trạng thái**: Draft

---

## 1. Tóm tắt

- **Vấn đề**: Hiện tại giao diện người dùng (UI) gặp hiện tượng giật lag, phản hồi chậm khi chuyển tiếp giữa các trang và khi thực hiện kéo rê thay đổi độ rộng của Sidebar.
- **Mục tiêu**: Loại bỏ hoàn toàn các lượt render dư thừa (double-render) khi chuyển trang và tối ưu hóa việc phân chia quyền cập nhật state trong layout để đạt hiệu năng hiển thị mượt mà (đáp ứng tiêu chuẩn 60fps khi kéo thả và chuyển hướng).
- **Đối tượng**: Tất cả người dùng hệ thống (Admin, Owner, Staff).

---

## 2. Phân tích nguyên nhân & Lý do tồn tại (Root Cause & Legacy Analysis)

### 2.1 Tại sao giao diện bị render 2 lần khi chuyển trang?
1. **Lượt render thứ nhất (Initial Render)**: Khi người dùng chuyển hướng sang một route mới (ví dụ `/inventory/stock`), router sẽ gắn component trang tương ứng (ví dụ `StockPage`). Trang này thực hiện lượt render đầu tiên.
2. **Kích hoạt Effect**: Ngay sau khi render xong lần đầu, hook `useEffect` của trang đó được kích hoạt để thiết lập tiêu đề trang:
   ```tsx
   useEffect(() => { setTitle("Tồn kho") }, [setTitle])
   ```
3. **Cập nhật State ở Root**: Hàm `setTitle` sẽ gọi hàm cập nhật trạng thái `setTitleState` nằm ở [PageTitleContext.tsx](file:///d:/do_an_tot_nghiep/project/frontend/mini-erp/src/context/PageTitleContext.tsx) (vốn là Provider bọc toàn bộ ứng dụng ở cấp cao nhất trong `App.tsx`).
4. **Thay đổi tham chiếu và ép Render lần hai**: Trạng thái thay đổi làm cho `PageTitleProvider` render lại. Do Provider này truyền xuống một object value mới `{{ title, setTitle }}` (thay đổi tham chiếu) và re-render ở cấp Root, React buộc **toàn bộ các component con bên trong nó** (bao gồm cả layout chính, sidebar, header và bản thân trang vừa hiển thị) phải render lại lần thứ hai ngay lập tức.

### 2.2 Biến `title` trong Context hiện tại dùng làm gì?
* **Thực trạng**: Biến `title` trong `PageTitleContext` hiện tại **không được tiêu thụ bởi bất kỳ component nào trong giao diện**.
* **Lý do tồn tại lịch sử**: Ban đầu, nhà phát triển có thể đã thiết kế để [Header.tsx](file:///d:/do_an_tot_nghiep/project/frontend/mini-erp/src/components/shared/layout/Header.tsx) lấy tiêu đề động từ Context này. Tuy nhiên, sau đó Header đã được đổi sang cơ chế tối giản hơn: tự phân tích đường dẫn URL hiện tại (`location.pathname`) qua map tĩnh `PAGE_TITLE_VI`:
   ```tsx
   const currentPage = lastSegment ? PAGE_TITLE_VI[lastSegment] : "Bảng điều khiển"
   ```
   Do đó, biến `title` trong Context bị bỏ quên (mồ côi) nhưng các trang vẫn giữ nguyên lệnh gọi `setTitle` làm thay đổi state vô ích.

---

## 3. Tác động của thay đổi (Impact Analysis)

Nếu chúng ta thay đổi cơ chế này bằng cách loại bỏ việc cập nhật state toàn cục hoặc memoize Context, tác động cụ thể sẽ như sau:

| Thuộc tính | Trước khi sửa | Sau khi sửa | Tác động / Ảnh hưởng |
| :--- | :--- | :--- | :--- |
| **Hiệu năng render** | Bị render 2 lần trên mọi trang khi chuyển hướng (Double-render). | Chỉ render 1 lần duy nhất khi mount (Single-render). | **Tích cực:** Giảm 50% tải render giao diện lúc chuyển trang, triệt tiêu hiện tượng nhấp nháy màn hình. |
| **Độ rộng Sidebar (Resize)** | Kéo thả Sidebar làm re-render toàn bộ layout chính và trang con đang mở. | Kéo thả Sidebar chỉ render lại Sidebar component. | **Tích cực:** Quá trình resize mượt mà ở mức 60fps, không gây nghẽn CPU khi đang mở trang dữ liệu lớn. |
| **Khả năng tương thích mã nguồn** | Các trang gọi hàm `setTitle` trong `useEffect`. | Giữ nguyên chữ ký API của `usePageTitle` và hàm `setTitle`. | **Không ảnh hưởng:** 29 trang hiện tại không cần phải sửa đổi bất kỳ dòng code nào. |
| **Hệ thống Test** | Các file test mock/wrap bằng `PageTitleProvider`. | `PageTitleProvider` vẫn tồn tại với giao diện kiểu dữ liệu tương thích. | **Không ảnh hưởng:** Các test case frontend hiện tại vẫn chạy bình thường. |

---

## 4. Phạm vi ảnh hưởng chi tiết (Affected Scope)

### 4.1 In-scope (Các file trực tiếp chỉnh sửa)
- [PageTitleContext.tsx](file:///d:/do_an_tot_nghiep/project/frontend/mini-erp/src/context/PageTitleContext.tsx): Thay đổi nội dung Provider để cô lập hàm `setTitle` ổn định bằng `useCallback`, loại bỏ việc cập nhật state React toàn cục hoặc tách biệt State/Dispatch Context. Cập nhật tiêu đề tài liệu thông qua side-effect tĩnh `document.title = ...`.
- [MainLayout.tsx](file:///d:/do_an_tot_nghiep/project/frontend/mini-erp/src/components/shared/layout/MainLayout.tsx) & [Header.tsx](file:///d:/do_an_tot_nghiep/project/frontend/mini-erp/src/components/shared/layout/Header.tsx): Sửa đổi cách gọi hook `useUIStore` thành sử dụng selector cụ thể (`useUIStore(s => s.sidebarOpen)`) để thoát khỏi subscription biến `sidebarWidth`.
- [Sidebar.tsx](file:///d:/do_an_tot_nghiep/project/frontend/mini-erp/src/components/shared/layout/Sidebar.tsx): Thêm kiểm tra điều kiện trước khi thực hiện hành động `expandItem`.

### 4.2 Out-of-scope (Không cần can thiệp nhưng được hưởng lợi)
- 29 file trang trong hệ thống (`StockPage.tsx`, `ProductsPage.tsx`, `WholesalePage.tsx`...).
- Phân quyền người dùng (RBAC).
- API Backend và Cơ sở dữ liệu.

---

## 5. Persona & Quyền (RBAC)

- **Vai trò áp dụng**: Tất cả các vai trò truy cập giao diện (Owner, Admin, Staff).
- **Quyền hạn**: Không thay đổi logic phân quyền hiện tại. Chỉ tối ưu hóa hiệu năng render ở tầng Client.

---

## 6. User Stories

- **US1**: Là người dùng hệ thống, tôi muốn các trang được hiển thị ngay lập tức khi tôi nhấn chọn menu điều hướng mà không có cảm giác trễ (double-render/chớp màn hình).
- **US2**: Là quản trị viên thường xuyên làm việc đa nhiệm, tôi muốn thao tác kéo rê thay đổi kích thước Sidebar diễn ra mượt mà ở mức 60fps, không gây đơ lag hay render lại nội dung trang đang mở.

---

## 7. Quy tắc nghiệp vụ & Kỹ thuật (Business & Technical Rules)

- **Ngăn chặn Double-Render**: Khi chuyển trang, Layout gốc và trang con chỉ được render tối đa **1 lần** (trừ trường hợp fetching dữ liệu bất đồng bộ từ API).
- **Cách ly State Thay đổi nhanh**: State thay đổi liên tục với tần suất cao (ví dụ: `sidebarWidth` thay đổi theo pixel khi drag chuột) không được phép lan truyền cập nhật đến các component bao quanh nội dung trang (`MainLayout` hoặc `<Outlet />`).
- **Tính ổn định của Context**: Giá trị Context truyền xuống cho các consumer chỉ thay đổi khi các thuộc tính thực tế mà consumer đó sử dụng có sự thay đổi.

---

## 8. Phương hướng giải quyết (Proposed Technical Strategy)

### 8.1 Giải quyết lỗi `PageTitleContext` (Double-render khi chuyển trang)
Do `title` không được tiêu thụ bởi bất kỳ component nào (Header tự tính toán tiêu đề qua URL), chúng ta sẽ:
- Loại bỏ state `title` trong Provider hoặc chuyển đổi `setTitle` thành một hàm callback tĩnh (không trigger state React toàn cục).
- Sử dụng `useCallback` cho `setTitle` và `useMemo` cho giá trị truyền xuống `PageTitleContext.Provider` để đảm bảo tham chiếu không thay đổi qua các lần render của provider.

### 8.2 Giải quyết lỗi `useUIStore` thiếu Selector (Lag khi kéo rộng Sidebar)
- Sửa đổi cách đăng ký trong [MainLayout.tsx](file:///d:/do_an_tot_nghiep/project/frontend/mini-erp/src/components/shared/layout/MainLayout.tsx) và [Header.tsx](file:///d:/do_an_tot_nghiep/project/frontend/mini-erp/src/components/shared/layout/Header.tsx):
  ```tsx
  // Trước đây:
  // const { sidebarOpen, setSidebarOpen } = useUIStore() // Đăng ký toàn bộ store bao gồm cả sidebarWidth
  
  // Giải pháp:
  const sidebarOpen = useUIStore((s) => s.sidebarOpen)
  const setSidebarOpen = useUIStore((s) => s.setSidebarOpen)
  ```
- Việc này giúp tách rời việc lắng nghe biến `sidebarWidth` ra khỏi Layout chính, chỉ có `Sidebar.tsx` (component cần chiều rộng thực tế) mới re-render khi kéo.

### 8.3 Giải quyết lỗi cập nhật vô điều kiện trong `Sidebar.tsx`
- Trong `useEffect` tự động mở rộng danh mục hiện tại, thêm kiểm tra điều kiện trước khi gọi cập nhật:
  ```tsx
  if (activeParent && !expandedItems.has(activeParent.id)) {
    expandItem(activeParent.id)
  }
  ```
- Điều này giúp triệt tiêu hoàn toàn lượt cập nhật Set dư thừa khi người dùng click qua lại giữa các menu con trong cùng một nhóm cha.

---

## 9. Tiêu chuẩn nghiệm thu (Acceptance Criteria)

### 9.1 Happy Paths

#### Kịch bản 1: Điều hướng trang mượt mà
```gherkin
Given Người dùng đang ở màn hình Dashboard
When Người dùng nhấn vào menu "Tồn kho"
Then Trang Tồn kho hiển thị đầy đủ
And MainLayout và Header chỉ thực hiện render duy nhất 1 lần (không bị render lần 2 do setTitle)
```

#### Kịch bản 2: Kéo giãn kích thước Sidebar mượt mà
```gherkin
Given Người dùng đang mở trang danh sách Tồn kho
When Người dùng nhấn giữ chuột và kéo rê thanh biên Sidebar để đổi kích thước
Then Sidebar thay đổi độ rộng theo thời gian thực một cách mượt mà
And Trang con (StockPage) và MainLayout không thực hiện re-render trong suốt quá trình kéo rê chuột
```

---

## 10. Kế hoạch xác thực (Verification Plan)

### 10.1 Kiểm tra thủ công (Manual Verification)
- Sử dụng **React Developer Tools (Profiler)** trong Google Chrome để ghi lại lượt render (Commit tree) khi thực hiện chuyển trang:
  - Xác nhận không có lượt re-render thừa từ `PageTitleProvider`.
- Sử dụng **Performance Panel** trong Chrome DevTools để ghi lại FPS khi kéo giãn Sidebar:
  - Mục tiêu đạt chỉ số FPS duy trì ổn định xung quanh 60fps và không có cảnh báo "Long Task" (màu đỏ).
- Kiểm tra tính đúng đắn của việc tự động mở rộng nhóm menu cha khi truy cập URL trực tiếp.
- Chạy build ứng dụng thành công bằng lệnh `npm run build` để kiểm tra lỗi TypeScript.

---

## 11. Open Questions (Câu hỏi mở)
- **OQ-1**: Chúng ta có muốn giữ lại state `title` của `PageTitleContext` để phòng trường hợp hiển thị tiêu đề động trên thẻ `<title>` của trình duyệt trong tương lai hay không?
  * *Tác động*: Nếu có, chúng ta phải giữ lại state nhưng cần tách `setTitle` và `title` thành 2 Context riêng biệt (State Context và Dispatch Context) để tránh re-render khi chỉ sử dụng hàm cập nhật.
  * *Phương án tạm thời*: SRS chọn phương án cập nhật trực tiếp tiêu đề tài liệu (`document.title`) thông qua side-effect tĩnh bên trong hàm `setTitle` nhằm tối giản hóa cấu trúc.
