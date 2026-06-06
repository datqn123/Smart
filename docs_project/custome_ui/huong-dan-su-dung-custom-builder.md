# Hướng dẫn sử dụng Custom Builder

## Custom Builder là gì?

Custom Builder là công cụ cho phép bạn **tự tạo một giao diện quản lý dữ liệu mới** trong hệ thống — không cần lập trình. Ví dụ: bạn muốn quản lý danh sách "Hàng hỏng", "Yêu cầu bảo trì", hoặc "Phiếu khảo sát" — chỉ cần vào Custom Builder, tạo giao diện, hệ thống sẽ sinh ra trang đó với bảng danh sách và form nhập liệu.

**Đường dẫn:** Menu bên trái → **Trình thiết kế giao diện**

---

## Phần 1 — Trang danh sách

Khi vào Custom Builder, bạn thấy bảng liệt kê tất cả giao diện đã tạo. Mỗi dòng gồm:

| Cột | Ý nghĩa |
|-----|---------|
| Tên giao diện | Tên hiển thị trên menu |
| Menu cha | Nhóm chứa giao diện này trên sidebar |
| Loại | `table_detail` / `record_list` / `form` |
| Trường | Số lượng field đang active |
| Trạng thái | Bản nháp / Cần sửa / Đã publish / Ngừng hiển thị |
| Hành động | **Sửa** (mở cài đặt), Xem thử *(chưa khả dụng)*, Nhân bản *(chưa khả dụng)* |

**Lọc & tìm kiếm:** Thanh tìm kiếm phía trên lọc theo tên, mã key, menu. Dropdown bên cạnh lọc theo trạng thái.

---

## Phần 2 — Tạo giao diện mới (Wizard 5 bước)

Bấm **"Tạo giao diện mới"**. Wizard gồm 5 bước — bạn có thể click tự do giữa các bước, không bắt buộc theo thứ tự.

Panel **Tóm tắt** bên phải luôn hiện tên, route, số field và số lỗi hiện tại.

---

### Bước 1 — Thông tin cơ bản

- **Tên giao diện** *(bắt buộc)*: Tên hiển thị trên menu. Ví dụ: `Hàng hỏng`
- **Mã giao diện** *(bắt buộc)*: Tự động sinh từ tên, chỉ gồm chữ thường, số và dấu `_`. Ví dụ: `hang_hong`. Có thể sửa tay.
  - Lưu ý: mã này là định danh kỹ thuật, **không đổi được sau khi publish**
- **Loại giao diện**: Chọn 1 trong 3:
  - `Bảng + Chi tiết` — trang có bảng danh sách, click vào 1 dòng mở form chi tiết *(phổ biến nhất)*
  - `Danh sách` — chỉ có bảng, không có form chi tiết
  - `Form` — chỉ có form nhập liệu, không có bảng
- **Mô tả**: Tùy chọn, hiện dưới tiêu đề trang.

---

### Bước 2 — Vị trí trên menu

Chọn giao diện này sẽ nằm ở đâu trên sidebar:

- **Dùng menu cha có sẵn**: Chọn từ danh sách nhóm menu đã tồn tại
- **Tạo menu cha mới**: Nhập tên nhóm mới — hệ thống tự tạo folder mới trên sidebar

Preview sidebar bên phải cho bạn thấy trước giao diện sẽ trông như thế nào.

---

### Bước 3 — Dữ liệu cần quản lý (Fields)

Định nghĩa các **trường dữ liệu** của giao diện. Mỗi field là một cột trong bảng / một ô trong form.

Với mỗi field:

| Cài đặt | Ý nghĩa |
|---------|---------|
| Tên trường | Nhãn hiển thị. Ví dụ: `Số lượng hỏng` |
| Mã trường | Key kỹ thuật, tự sinh. Ví dụ: `so_luong_hong` |
| Kiểu | Xem bảng kiểu dữ liệu bên dưới |
| Bắt buộc | Nếu tick, form bắt buộc nhập field này |
| Hiện bảng | Nếu tick, field này xuất hiện trong bảng danh sách |

**Các kiểu dữ liệu:**

| Kiểu | Dùng cho |
|------|---------|
| `text` | Văn bản ngắn (tên, mã, ghi chú ngắn) |
| `long_text` | Văn bản dài (mô tả, ghi chú nhiều dòng) |
| `number` | Số nguyên hoặc thập phân |
| `money` | Số tiền (có định dạng VNĐ) |
| `date` | Ngày tháng |
| `boolean` | Có / Không (checkbox) |
| `single_select` | Chọn 1 trong nhiều option cố định |
| `reference` | Liên kết đến entity khác (sản phẩm, kho, khách hàng...) |

Nếu chọn `reference`, cần chỉ định thêm:
- **Loại tham chiếu**: `Core entity` (dữ liệu gốc hệ thống) hoặc `Custom entity published`
- **Target**: Sản phẩm / Kho / Nhà cung cấp / Khách hàng / Người dùng

---

### Bước 4 — Cách hiển thị

- **Cột bảng**: Tick các field muốn hiện trong bảng danh sách. Field bắt buộc phải có trong form.
- **Field trong form**: Tick field nào xuất hiện khi nhập liệu.

---

### Bước 5 — Kiểm tra & lưu

Xem lại toàn bộ lỗi validation từ 4 bước trước. Hai lựa chọn:

- **Lưu bản nháp**: Lưu dù còn lỗi không nghiêm trọng. Trạng thái = `Bản nháp`.
- **Lưu và mở cài đặt**: Lưu xong chuyển thẳng vào Edit Settings để cấu hình chi tiết hơn.

---

## Phần 3 — Edit Settings (6 tab)

Sau khi tạo xong, bấm **Sửa** để vào trang cài đặt chi tiết. Có 3 nút ở góc phải:

- **Lưu nháp**: Lưu tất cả thay đổi, giữ trạng thái Draft
- **Publish**: Đẩy giao diện lên hệ thống thật — chỉ bật được khi **không còn lỗi validation** và **đã lưu**
- Badge **"Có thay đổi chưa lưu"** xuất hiện khi bạn chỉnh mà chưa lưu

---

### Tab Tổng quan

Xem và sửa thông tin cơ bản: tên, mã, mô tả, loại giao diện. Không thay đổi mã sau khi publish.

---

### Tab Dữ liệu

Quản lý toàn bộ field. Với mỗi field ngoài những cài đặt từ wizard, còn có **Logic cơ bản**:

#### Validation rules

Kiểm tra dữ liệu nhập vào:

- Giá trị tối thiểu / tối đa (cho kiểu số)
- Độ dài tối thiểu / tối đa (cho kiểu text)
- Pattern regex

#### Giá trị mặc định

Tự điền sẵn khi tạo bản ghi mới.

#### Options *(chỉ với `single_select`)*

Danh sách lựa chọn, có thể thêm/xóa tùy ý.

#### Readonly / Hidden

Tick để field chỉ đọc hoặc ẩn hoàn toàn khỏi form.

#### Conditional visibility

Hiện/ẩn field này **dựa theo giá trị của field khác**:

| Cài đặt | Ý nghĩa |
|---------|---------|
| Điều kiện theo field | Field nào sẽ điều khiển visibility |
| Toán tử | `Bằng` (so sánh giá trị cụ thể) hoặc `Có dữ liệu` (chỉ cần field kia không rỗng) |
| Giá trị | Giá trị cần so sánh (chỉ dùng khi toán tử = "Bằng") |
| Hành động | `Hiện` hoặc `Ẩn` field này khi điều kiện đúng |

**Ví dụ:** Field `Lý do hỏng` chỉ hiện khi `Trạng thái` = `Hỏng`.

---

### Tab Hiển thị

Cấu hình giao diện bảng và form:

**Cột bảng** — Với mỗi cột đang active:

| Cài đặt | Ý nghĩa |
|---------|---------|
| Width | Độ rộng cột (px), từ 80 đến 480 |
| Align | Căn trái / giữa / phải |
| Format | Cách hiển thị: `text`, `number`, `date`, `badge`, `boolean`, `money`, `link` |

**Default sort** — Cột sắp xếp mặc định khi mở bảng, và hướng tăng/giảm dần.

**Filter nhanh** — Tick field nào xuất hiện trong thanh lọc nhanh của bảng.

**Form nhập liệu** — Chia form thành nhiều section (nhóm), sắp xếp thứ tự, chọn field cho từng nhóm.

**Preview xem thử** — Nút xem thử bảng và form với dữ liệu mẫu, không ghi dữ liệu thật.

---

### Tab Phân quyền

Chọn các **Role** có quyền xem và thao tác giao diện này:

- Owner / Admin / Manager / Staff / Warehouse

---

### Tab Kiểm tra

Xem toàn bộ lỗi validation được nhóm theo section. Mỗi lỗi có nút **"Sửa ngay"** nhảy thẳng đến tab liên quan. Khi tất cả lỗi được sửa → nút **Publish** ở trên mới sáng lên.

---

### Tab Nâng cao

Mở accordion **"Nâng cao"** để truy cập 2 tính năng:

#### Workflow Designer

Thiết kế vòng đời trạng thái của một bản ghi. Ví dụ: `Nháp → Chờ xử lý → Đã xử lý`.

| Thành phần | Ý nghĩa |
|-----------|---------|
| States (trạng thái) | Thêm/sửa/xóa trạng thái. State đầu tiên là `start`, cuối cùng là `end` |
| Transitions (chuyển trạng thái) | Định nghĩa ai có thể chuyển từ trạng thái nào sang trạng thái nào |
| Allowed roles | Role nào được phép thực hiện transition đó |
| Preview | Sơ đồ trực quan các mũi tên chuyển trạng thái |

#### Logic Connector Builder

Tạo **rules tự động tính toán** giữa các field khi có sự kiện xảy ra. Ví dụ: khi lưu bản ghi, tự cộng `số lượng hỏng` vào `tổng hỏng`.

Mỗi rule được cấu hình theo 4 bước:

| Bước | Cài đặt | Ý nghĩa |
|------|---------|---------|
| 1 | **Trigger** | Khi nào rule chạy: `on_save` (lưu), `on_status_change` (đổi trạng thái), `on_field_change` (đổi field) |
| 2 | **Source** | Field nào là nguồn dữ liệu đầu vào |
| 3 | **Operation** | Phép tính: Set giá trị cố định / Cộng / Trừ / Nhân / Tính tổng các dòng... |
| 4 | **Target** | Field nào nhận kết quả |

Thêm vào đó:
- **Giá trị**: Hằng số hoặc tham số cho operation (ví dụ: set cứng = `"Chờ xử lý"`)
- **Tên rule**: Đặt tên để dễ nhận biết trong danh sách

**Review dry-run**: Sau khi cấu hình, hệ thống tự chạy thử rule với dữ liệu mẫu và hiển thị: *Source value → Target trước → Target sau*. Giúp bạn kiểm tra rule có đúng không trước khi publish.

---

## Luồng làm việc được khuyến nghị

```
Tạo mới (wizard 5 bước)
        ↓
Lưu bản nháp
        ↓
Edit Settings → Tab Dữ liệu
  → chỉnh validation, default, conditional visibility
        ↓
Tab Hiển thị
  → chỉnh cột bảng, sort, filter, form sections
        ↓
Tab Phân quyền
  → gán role phù hợp
        ↓
Tab Nâng cao (nếu cần)
  → cấu hình workflow và logic connector
        ↓
Tab Kiểm tra
  → sửa hết lỗi còn lại
        ↓
Lưu nháp → Publish
```

---

## Lưu ý quan trọng

- **Publish** chỉ hoạt động khi: không còn lỗi validation **và** đã lưu nháp (nút Lưu nháp phải đang mờ/disabled)
- Sau khi publish, giao diện xuất hiện trên sidebar — chỉ người dùng có role phù hợp mới thấy được
- **Hiện tại** hệ thống đang dùng dữ liệu mock (fixture) — publish chưa ghi vào backend thật
- Mã giao diện (`key`) không nên đổi sau khi đã dùng trong production vì nó là định danh kỹ thuật dùng cho route và tích hợp
