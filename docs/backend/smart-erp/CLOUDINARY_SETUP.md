# Setup Cloudinary cho `smart-erp`

Hướng dẫn bật upload ảnh sản phẩm (multipart `POST /api/v1/products/{id}/images`) qua Cloudinary. Cấu hình gốc map từ biến môi trường trong [`src/main/resources/application.properties`](../src/main/resources/application.properties); bean Cloudinary được tạo trong [`CloudinaryConfiguration`](../src/main/java/com/example/smart_erp/config/CloudinaryConfiguration.java).

---

## 1. Lấy giá trị từ Cloudinary Dashboard

1. Đăng nhập [Cloudinary Console](https://console.cloudinary.com/).
2. **Cloud name**: Dashboard (Programmable Media) — thường ở phần Account / Product environment.
3. **API Key** và **API Secret**: **Settings** (bánh răng) → **API Keys** (hoặc **Product environment credentials**).
   - **API Secret** có thể chỉ hiển thị khi tạo hoặc “reveal” — lưu ở nơi an toàn, **không** đưa vào git.

---

## 2. Biến môi trường (khuyến nghị)

| Biến | Ý nghĩa | Bắt buộc khi bật upload? |
| :--- | :--- | :---: |
| `CLOUDINARY_ENABLED` | Phải là `true` để đăng ký bean Cloudinary | Có |
| `CLOUDINARY_CLOUD_NAME` | Cloud name | Có |
| `CLOUDINARY_API_KEY` | API Key | Có |
| `CLOUDINARY_API_SECRET` | API Secret | Có |
| `CLOUDINARY_FOLDER` | Tiền tố folder trên Cloudinary (mặc định `smart-erp/products`) | Không |
| `CLOUDINARY_MAX_BYTES` | Giới hạn kích thước một file, byte (mặc định `5242880` = 5 MiB) | Không |

Nếu `CLOUDINARY_ENABLED=true` nhưng thiếu **cloud name**, **api key** hoặc **api secret** (chuỗi rỗng), ứng dụng sẽ **không khởi động** (`IllegalStateException` khi tạo bean).

**Windows PowerShell (phiên terminal hiện tại):**

```powershell
$env:CLOUDINARY_ENABLED = "true"
$env:CLOUDINARY_CLOUD_NAME = "<cloud_name>"
$env:CLOUDINARY_API_KEY = "<api_key>"
$env:CLOUDINARY_API_SECRET = "<api_secret>"
```

Sau đó chạy Spring Boot **cùng cửa sổ** đó, hoặc cấu hình tương đương trong IDE: **Run → Edit Configurations → Environment variables**.

**Multipart:** `spring.servlet.multipart.max-file-size` / `max-request-size` đang **5MB** mỗi part (khớp nghiệp vụ ảnh) — file không nên vượt quá nếu chưa đổi cấu hình.

---

## 3. Thay thế: properties cục bộ (chỉ máy dev)

Có thể đặt trực tiếp (không dùng env), ví dụ trong file **không commit** (xem `.gitignore` — pattern `application-secrets.properties`):

```properties
app.cloudinary.enabled=true
app.cloudinary.cloud-name=...
app.cloudinary.api-key=...
app.cloudinary.api-secret=...
```

Nạp file đó bằng một trong các cách Spring Boot hỗ trợ (`spring.config.import`, `spring.profiles.active`, v.v.) tùy môi trường IDE của bạn. **Không** dán secret vào `application.properties` đã theo dõi git.

---

## 4. Kiểm tra nhanh

1. PostgreSQL + Flyway đã chạy; khởi động `smart-erp` với `spring.profiles.active=postgres` (hoặc profile mặc định của bạn trỏ đúng DB).
2. Lấy JWT có quyền `can_manage_products` (khi `APP_SECURITY_MODE=jwt-api`).
3. Gọi multipart (ví dụ `curl` — thay `TOKEN`, `BASE`, `PRODUCT_ID`, đường dẫn ảnh):

```bash
curl -sS -X POST "${BASE}/api/v1/products/${PRODUCT_ID}/images" \
  -H "Authorization: Bearer ${TOKEN}" \
  -F "file=@/path/to/photo.png" \
  -F "sortOrder=0" \
  -F "isPrimary=false"
```

Kỳ vọng: **HTTP 201**, JSON `success: true`, `data.url` bắt đầu bằng `https://res.cloudinary.com/...`.

Nếu `CLOUDINARY_ENABLED=false` (mặc định): multipart trả **400** hướng dẫn bật cấu hình; vẫn có thể thêm ảnh bằng **JSON** với trường `url` (URL có sẵn) không cần Cloudinary.

---

## 5. Tài liệu API

Chi tiết endpoint và part `file`: [`frontend/docs/api/API_Task039_products_post_image.md`](../../../frontend/docs/api/API_Task039_products_post_image.md).
