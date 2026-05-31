# SRS — Quản lý sản phẩm (list / CRUD / ảnh / xóa & bulk) — Task034–Task041

> **File (Spring / `smart-erp`):** `backend/docs/srs/SRS_Task034-041_products-management.md`  
> **Người soạn:** Agent BA + SQL (theo `BA_AGENT_INSTRUCTIONS.md`, `SQL_AGENT_INSTRUCTIONS.md`)  
> **Ngày:** 27/04/2026  
> **Đồng bộ sau trả lời PO (OQ):** 27/04/2026  
> **Đồng bộ codebase (upload ảnh / Cloudinary — Analyst):** 27/04/2026 — `ProductsController`, `ProductImageService`, `CloudinaryMediaService`, Flyway **V15**, [`smart-erp/docs/CLOUDINARY_SETUP.md`](../../smart-erp/docs/CLOUDINARY_SETUP.md)  
> **CR Task034 — thứ tự danh sách:** Mặc định / không truyền `sort` → **`id:asc`** (`products.id` tăng dần). Whitelist thêm `id:desc`. Với sort theo cột khác → **tie-break** `p.id ASC` (phân trang ổn định). **GAP:** [`API_Task034_products_get_list.md`](../../../frontend/docs/api/API_Task034_products_get_list.md) cần cùng mặc định + whitelist khi đồng bộ doc.  
> **Trạng thái:** Approved *(OQ §4; hành vi ảnh §4.3 + §8.6 bám mã hiện tại; phụ lục §14–§15: OQ-7 / OQ-8 / NFR tạo nhiều file đã chốt; UX **Lưu** theo ủy quyền PO)*  
> **Phụ lục CR 27/04/2026 — §14–§15:** Đã ghi nhận quyết định kỹ thuật/UX; **OQ-7, OQ-8** tại **§14.5**; **Màn sửa sản phẩm (§1.1, §9 BR-10, §11):** thay đổi ảnh thật sự (persist phía server) **chỉ** khi người dùng bấm **Lưu** — ủy quyền chốt bởi PO / Owner, 27/04/2026.  
> **PO duyệt (khi Approved):** PO — 27/04/2026 *(chữ ký PR/ticket theo quy trình team)*

---

## 0. Đầu vào & traceability

| Nguồn | Đường dẫn / ghi chú |
| :--- | :--- |
| API Task034 | [`../../../frontend/docs/api/API_Task034_products_get_list.md`](../../../frontend/docs/api/API_Task034_products_get_list.md) |
| API Task035 | [`../../../frontend/docs/api/API_Task035_products_post.md`](../../../frontend/docs/api/API_Task035_products_post.md) |
| API Task036 | [`../../../frontend/docs/api/API_Task036_products_get_by_id.md`](../../../frontend/docs/api/API_Task036_products_get_by_id.md) |
| API Task037 | [`../../../frontend/docs/api/API_Task037_products_patch.md`](../../../frontend/docs/api/API_Task037_products_patch.md) |
| API Task038 | [`../../../frontend/docs/api/API_Task038_products_delete.md`](../../../frontend/docs/api/API_Task038_products_delete.md) |
| API Task039 | [`../../../frontend/docs/api/API_Task039_products_post_image.md`](../../../frontend/docs/api/API_Task039_products_post_image.md) |
| API Task041 | [`../../../frontend/docs/api/API_Task041_products_bulk_delete.md`](../../../frontend/docs/api/API_Task041_products_bulk_delete.md) |
| Task040 | **Không có** file `API_Task040_*.md` trong repo — không nằm trong SRS này. |
| Khung API | [`../../../frontend/docs/api/API_PROJECT_DESIGN.md`](../../../frontend/docs/api/API_PROJECT_DESIGN.md) §4.9 |
| Envelope lỗi | [`../../../frontend/docs/api/API_RESPONSE_ENVELOPE.md`](../../../frontend/docs/api/API_RESPONSE_ENVELOPE.md) (tham chiếu) |
| UC / DB tham chiếu | [`../../../frontend/docs/UC/Database_Specification.md`](../../../frontend/docs/UC/Database_Specification.md) §7+ (đối chiếu Flyway; không phát minh tên bảng ngoài migration) |
| Flyway thực tế | [`V1__baseline_smart_inventory.sql`](../../smart-erp/src/main/resources/db/migration/V1__baseline_smart_inventory.sql) + [`V15__productimages_one_primary_unique.sql`](../../smart-erp/src/main/resources/db/migration/V15__productimages_one_primary_unique.sql) — `productimages` partial unique **một** `is_primary = true` / `product_id` |
| Triển khai ảnh (BE) | `ProductsController` (`POST …/images` JSON + multipart), `ProductImageService`, `ProductImageJdbcRepository`, `CloudinaryConfiguration` / `CloudinaryProperties`, `CloudinaryMediaService` | Xem §4.3, §8.6 |
| Vận hành Cloudinary | [`../../smart-erp/docs/CLOUDINARY_SETUP.md`](../../smart-erp/docs/CLOUDINARY_SETUP.md) | Biến `CLOUDINARY_*`, `app.cloudinary.*`, `spring.servlet.multipart.*` |
| Danh mục (FK / hiển thị) | [`SRS_Task029-033_categories-management.md`](SRS_Task029-033_categories-management.md) — `categories.deleted_at`, quyền `can_manage_products` / Owner |
| UI index | [`../../../frontend/mini-erp/src/features/FEATURES_UI_INDEX.md`](../../../frontend/mini-erp/src/features/FEATURES_UI_INDEX.md) |
| PM handoff (`WORKFLOW_RULE` §0.2) | [`../task034-041/01-pm/README.md`](../task034-041/01-pm/README.md) | Chuỗi task, gate, khối **API_BRIDGE §3.1** |
| CR 27/04/2026 — tạo/update ảnh | **§14–§15** tài liệu này; [`../../AGENTS/WORKFLOW_RULE.md`](../../AGENTS/WORKFLOW_RULE.md) §0.1 / §0.3 / mục API bridge | Bổ sung sau **G-DEV** — **API_BRIDGE** cập nhật `BRIDGE_*.md` + **samples** mock |

### 0.1 Đồng bộ spec ↔ Flyway (đã chốt kỹ thuật trong SRS — không cần sửa API markdown)

| Điểm | API / ghi chú | Flyway / thực tế | Cách xử lý trong SRS |
| :--- | :--- | :--- | :--- |
| Bảng ảnh Task039 | Gợi ý DDL `product_images` + cột `url` | V1 đã có **`ProductImages`** với cột **`image_url`**, `sort_order`, `is_primary`, `id` **SERIAL** | **Không** tạo bảng trùng: map JSON **`url`** ↔ DB **`image_url`**; response trả **`url`** (camelCase) lấy từ `image_url`. |
| Unique một ảnh primary | Task039 đề xuất partial unique | V1 chỉ có index `idx_pi_primary` **không unique** | **Đã triển khai OQ-4(a):** Flyway **`V15__productimages_one_primary_unique.sql`** — index `uq_productimages_one_primary` trên `productimages (product_id) WHERE is_primary = TRUE`. Transaction reset primary + `products.image_url` vẫn bắt buộc. |
| Upload server (Cloudinary) | Task039 gợi ý multipart tuỳ cấu hình | Mặc định Cloudinary **tắt** (`app.cloudinary.enabled=false`) | **Hai endpoint trùng path, khác `Content-Type`:** `application/json` (URL ngoài) **luôn**; `multipart/form-data` + part `file` → upload Cloudinary **chỉ khi** bật bean + đủ secret — xem §4.3. |
| Tên bảng trong SQL mẫu | API dùng `Products` (Pascal) | PostgreSQL chuẩn team: JDBC/SQL file thường dùng **chữ thường** (`products`, …) sau khi tạo không quote | §10 dùng identifier **thường** khớp repo JDBC hiện có (`products`, `categories`, …). |

---

## 1. Tóm tắt điều hành

- **Vấn đề:** UC8 cần API đầy đủ cho **danh sách phân trang**, **tạo** (sản phẩm + đơn vị cơ sở + giá khởi tạo) — *phụ lục §14:* cho phép **upload nhiều ảnh cùng request tạo**, xử lý phần upload **đa luồng (song song)**; **chi tiết** (đơn vị + giá hiện tại + gallery), **PATCH** (meta + giá) — *§14:* coi **thay đổi ảnh** on par với mọi field, **một input đổi** (kể cả chỉ ảnh) cũng là có thay đổi và cập nhật; **xóa một** / **xóa bulk** có kiểm tra chứng từ & tồn, **thêm ảnh** qua **JSON URL** hoặc **multipart** (upload **Cloudinary** khi bật cấu hình).
- **Mục tiêu nghiệp vụ:** Khớp envelope `success` / `data` / `message`; đọc/tạo/sửa + **thêm ảnh** (JSON và/hoặc multipart): user có **`can_manage_products`**; **`DELETE` / `bulk-delete`: chỉ Owner** (**OQ-6(a)**).
- **Đối tượng:** User JWT; Staff / Owner / Admin theo quyền seed `Roles.permissions`.

### 1.1 Giao diện Mini-ERP

| Nhãn menu (Sidebar) | Route | Page (export) | Component / vùng chính | File (dưới `frontend/mini-erp/src/features/`) |
| :--- | :--- | :--- | :--- | :--- |
| *(theo Sidebar — nhóm sản phẩm)* | `/products/list` | `ProductsPage` | `ProductTable`, `ProductToolbar`, `ProductForm`, `ProductDetailDialog` | `product-management/pages/ProductsPage.tsx` |
| *Chức năng **sửa** sản phẩm (cùng route / form tạo-sửa nếu dùng chung)* | *như trên* | *như trên* | **Cập nhật ảnh phía server chỉ tại sự kiện bấm** **Lưu** — chọn/xóa/đổi thứ tự ảnh trong lúc soạn = **state cục bộ**; **chưa** bấm Lưu thì **không** gọi `POST …/images`, `PATCH` ảnh, v.v. Hủy/đóng: bỏ thay đổi chưa lưu. Chi tiết **BR-10** | `product-management/...` *(theo* `FEATURES_UI_INDEX`*)* |

---

## 2. Bóc tách nghiệp vụ (capabilities)

| # | Capability | Kích hoạt bởi | Kết quả mong đợi | Ghi chú |
| :---: | :--- | :--- | :--- | :--- |
| C1 | Phân trang + lọc SP | `GET /api/v1/products` | `200` + `items`, `page`, `limit`, `total` | `search`, `categoryId`, `status`, `sort` whitelist; **mặc định thứ tự:** `id:asc` (ID sản phẩm tăng dần) |
| C2 | Đọc read-model list | C1 | Mỗi item có `categoryName`, `currentStock`, `currentPrice` | Giá: latest `product_price_history` theo đơn vị cơ sở; `effective_date` ≤ **`CURRENT_DATE`** (DB server — **OQ-1(a)**) |
| C3 | Tạo SP + đơn vị cơ sở + giá | `POST /api/v1/products` | `201` + object (Task034-shape + `unitId` base) | **Một transaction**; *§14:* hỗ trợ thêm **multipart** tạo kèm nhiều file ảnh, **upload lên storage (Cloudinary) chạy song song** (đa luồng) trước khi (hoặc khi) ghi DB — chi tiết §14.2 |
| C4 | Chi tiết SP | `GET /api/v1/products/{id}` | `200` + `units[]` + giá current mỗi unit + `images[]` | `images` từ bảng **`productimages`** (JDBC) |
| C5 | PATCH meta + giá base + gallery | `PATCH /api/v1/products/{id}` | `200` | `FOR UPDATE`; đổi giá → **INSERT** `product_price_history`; **cặp** `salePrice`+`costPrice` khi đổi giá (theo Task037); *§14:* phát hiện **`hasImageChange`**: nếu **chỉ** ảnh thay đổi, **vẫn 200** và cập nhật — không yêu cầu field khác thay đổi; **bất kỳ một thành phần thay đổi** (metadata / giá / ảnh) đều kích hoạt cập nhật |
| C6 | Xóa một SP | `DELETE /api/v1/products/{id}` | `200` + `{ id, deleted: true }` | Kiểm tra `stock_receipt_details`, `order_details`, tồn > 0 (policy §9) trước `DELETE` |
| C7 | Thêm ảnh | `POST /api/v1/products/{id}/images` | `201` + `ProductImageData` | **JSON:** `url` + `sortOrder` + `isPrimary` — không cần Cloudinary. **Multipart:** part **`file`** + params `sortOrder`, `isPrimary` — `CloudinaryMediaService` trả `secure_url` khi `app.cloudinary.enabled=true`; tắt → **400** hướng dẫn bật cấu hình. **`isPrimary`:** reset primary + `products.image_url`; index **V15**. |
| C8 | Xóa nhiều SP | `POST /api/v1/products/bulk-delete` | `200` hoặc `409` | **All-or-nothing** — **OQ-3(a)** |

---

## 3. Phạm vi

### 3.1 In-scope

- Bảy endpoint: Task034, 035, 036, 037, 038, 039, 041.
- **Phụ lục §14:** tạo sản phẩm có thể **kèm upload nhiều ảnh** cùng request, xử lý upload **song song (đa luồng)**; `PATCH` **phát hiện thay đổi ảnh** — nếu **chỉ ảnh đổi** thì vẫn cập nhật (**200**), **một thành phần bất kỳ đổi** cũng là đủ để update.
- Task039 **đủ hai** cách: JSON URL + **multipart → Cloudinary** (tuỳ bật `app.cloudinary.enabled` + secret).
- Validation, envelope, mã HTTP như §8.
- Transaction tạo SP; transaction PATCH giá; transaction ảnh primary; transaction xóa bulk **all-or-nothing** (**OQ-3(a)**).

### 3.2 Out-of-scope

- **Tự host file** trên disk máy chủ (không Cloudinary / không URL ngoài) — không có trong mã hiện tại.
- **Định dạng ảnh** ngoài **JPEG / PNG / WebP** (GIF, SVG, …) — `CloudinaryMediaService` từ chối.
- **Task040** (không có spec API trong repo).
- Đồng bộ giá đa đơn vị nâng cao, POS, đơn hàng.

---

## 4. Câu hỏi làm rõ cho PO (Open Questions) — **đã trả lời**

### 4.1 Quyết định PO (hành vi chốt cho Dev/Tester)

| ID | Chốt | Diễn giải triển khai |
| :--- | :--- | :--- |
| **OQ-1** | **(a)** | So sánh `effective_date` với **`CURRENT_DATE`** của PostgreSQL (múi giờ session/DB server). |
| **OQ-2** | **(a)** | **Cấm** `POST`/`PATCH` gán `categoryId` tới danh mục có `deleted_at IS NOT NULL` → **400**, `error` gợi ý `INVALID_CATEGORY` (hoặc tương đương trong envelope). Category **không tồn tại** (id không có row) → **404** (resource FK). |
| **OQ-3** | **(a)** | `POST /api/v1/products/bulk-delete`: **all-or-nothing** — một `id` không đủ điều kiện xóa → **409**, **không** xóa bản ghi nào. |
| **OQ-4** | **(a)** | **Đã triển khai:** Flyway **`V15__productimages_one_primary_unique.sql`** — tối đa một `is_primary = true` / `product_id`; transaction reset primary + `products.image_url` vẫn bắt buộc. |
| **OQ-5** | **PO (tự do) + mã đã bổ sung** | Nguyên tắc PO: **ưu tiên URL** (JSON). **Triển khai thêm:** multipart upload lên **Cloudinary** khi bật cấu hình — chi tiết **§4.3** (drift doc ↔ code đã đóng). |
| **OQ-6** | **(a)** | **`DELETE /products/{id}`** và **`POST /products/bulk-delete`**: **chỉ Owner** (`Jwt` claim `role`); user khác có `can_manage_products` → **403**. |

### 4.2 Traceability (bảng gốc + cột trả lời PO)

**Trả lời PO:**

| ID | Quyết định PO | Ngày |
| :--- | :--- | :--- |
| OQ-1 | **(a)** — `CURRENT_DATE` DB | 27/04/2026 |
| OQ-2 | **(a)** — cấm category đã soft-delete | 27/04/2026 |
| OQ-3 | **(a)** — bulk all-or-nothing | 27/04/2026 |
| OQ-4 | **(a)** — Flyway partial unique primary | 27/04/2026 |
| OQ-5 | V1 URL (JSON); Cloudinary multipart **đã triển khai** trong mã — xem §4.3 | 27/04/2026 |
| OQ-6 | **(a)** — chỉ Owner xóa / bulk-delete | 27/04/2026 |

| ID | Câu hỏi | Phương án (PO chọn một) | Ảnh hưởng nếu chưa chốt | Blocker? |
| :--- | :--- | :--- | :--- | :---: |
| **OQ-1** | So sánh `effective_date` (DATE) với “hôm nay” cho giá hiện hành | **(a)** Dùng **ngày theo timezone DB** (`CURRENT_DATE` — thường = server). **(b)** Dùng **UTC** cố định (`(now() AT TIME ZONE 'utc')::date`). **(c)** Truyền `X-Timezone-Offset` từ client (phức tạp hơn). | Lệch giá cuối ngày theo múi giờ | Không |
| **OQ-2** | `categoryId` trỏ tới danh mục đã **soft-delete** (`deleted_at NOT NULL`) | **(a)** **Cấm** gán mới / PATCH sang category đã xóa → **400** `INVALID_CATEGORY`. **(b)** Cho phép (giữ FK) — chỉ ảnh hưởng UI filter. | POST/PATCH validation | Không |
| **OQ-3** | `POST …/bulk-delete` | **(a)** **All-or-nothing:** một `id` conflict → **409**, không xóa cái nào (**khuyến nghị** đơn giản, dễ test). **(b)** **Partial:** trả `deletedIds` + `failed[]` như mẫu Task041. | Contract response & transaction | **Đã chốt (a)** — không còn blocker |
| **OQ-4** | Ràng buộc **một** `is_primary` trên `product_images` | **(a)** Thêm **Flyway** partial unique (khớp Task039). **(b)** Chỉ enforce trong **service transaction** (không thêm index). | Race concurrent upload | Không |
| **OQ-5** | Multipart upload ảnh | **(a)** **v1 chỉ JSON** `url` (đã upload ngoài). **(b)** v1 hỗ trợ cả `multipart/form-data` + giới hạn size/MIME. | Scope Dev + lưu file | Không |
| **OQ-6** | Ai được `DELETE` / `bulk-delete` | **(a)** **Chỉ Owner** (JWT `role` + nhất quán Task033). **(b)** Mọi user có `can_manage_products` (Staff được xóa nếu pass business checks). | 403 vs 200 | Không |

### 4.3 Đồng bộ codebase — upload ảnh (theo `CODEBASE_ANALYST_AGENT_INSTRUCTIONS` §6 drift)

> Mục này mô tả **hành vi thực tế** `smart-erp` sau khi bổ sung Cloudinary; **không** thay thế bảng lịch sử OQ §4.2.

| Hạng mục | Chi tiết |
| :--- | :--- |
| **Endpoint** | `POST /api/v1/products/{id}/images` — **hai mapping** cùng path: `consumes = APPLICATION_JSON` và `consumes = MULTIPART_FORM_DATA` (`ProductsController`). |
| **JSON** | Body `ProductImageCreateRequest`: `url` (@URL, max 500), `sortOrder`, `isPrimary` — lưu trực tiếp `productimages.image_url`; **không** gọi Cloudinary. |
| **Multipart** | Part bắt buộc **`file`** (`MultipartFile`); query/form **`sortOrder`** (optional, default `0`, ≥ 0), **`isPrimary`** (optional, default `false`). Thiếu/rỗng `file` → **400** (`BusinessException` hoặc `MissingServletRequestPartException` → handler chung). |
| **Cloudinary** | `CloudinaryMediaService.uploadProductImage`: kiểm `props.enabled` + bean `Cloudinary` non-empty; nếu tắt/thiếu cấu hình → **400** (message tiếng Việt hướng dẫn `app.cloudinary.enabled` + `CLOUDINARY_*`). Upload folder `{app.cloudinary.folder}/{productId}/`, `public_id` UUID, lấy **`secure_url`**. |
| **Giới hạn** | MIME: **`image/jpeg`**, **`image/png`**, **`image/webp`**; kích thước ≤ **`app.cloudinary.max-file-size-bytes`** (mặc định **5242880** = 5 MiB); Spring **`spring.servlet.multipart.max-file-size` = 5MB** / **`max-request-size`** theo cấu hình (`application.properties`). |
| **Persistence** | `ProductImageService` `@Transactional`: nếu `isPrimary` — `UPDATE productimages SET is_primary=false` theo `product_id`, `UPDATE products SET image_url`, rồi `INSERT productimages` (cột `file_size_bytes`, `mime_type` từ multipart; JSON có thể null). |
| **Bật production** | `CLOUDINARY_ENABLED=true` + `CLOUDINARY_CLOUD_NAME`, `API_KEY`, `API_SECRET`; xem [`smart-erp/docs/CLOUDINARY_SETUP.md`](../../smart-erp/docs/CLOUDINARY_SETUP.md). `enabled=true` mà thiếu secret → **fail-fast** khi khởi tạo bean (`CloudinaryConfiguration`). |

---

## 5. Phân tích scope tệp & bằng chứng

### 5.1 Tài liệu đã đối chiếu (read)

- 7 file API Task034–039, 041; `API_PROJECT_DESIGN.md`; `SRS_Task029-033`; `FEATURES_UI_INDEX.md`; Flyway **V1** + **V15**; `smart-erp/docs/CLOUDINARY_SETUP.md`; mã `catalog` (controller/service/repository/media/config) như §4.3.

### 5.2 Mã / migration (đã có — verify khi đổi SRS)

- Package **`com.example.smart_erp.catalog`**: `ProductsController`, `ProductImageService`, `ProductImageJdbcRepository`, `ProductImageCreateRequest`, `ProductImageData`.
- **`com.example.smart_erp.catalog.media`:** `CloudinaryMediaService`.
- **`com.example.smart_erp.config`:** `CloudinaryConfiguration`, `CloudinaryProperties` (`app.cloudinary.*` / env `CLOUDINARY_*`).
- Flyway **`V15__productimages_one_primary_unique.sql`** — `uq_productimages_one_primary`.
- Test tham chiếu: `ProductsControllerWebMvcTest` (JSON + multipart), `CloudinaryMediaServiceTest`.

### 5.3 Rủi ro phát hiện sớm

- Sản phẩm **không** có `product_units` `is_base_unit = true` → list Task034 (JOIN inner) **loại** khỏi kết quả — dữ liệu cũ cần data fix hoặc đổi LEFT JOIN + `currentPrice` null (**không** khuyến nghị LEFT nếu UC8 yêu cầu mỗi SP có base unit — giữ INNER + seed repair).
- `DELETE Products`: `stock_receipt_details` / `order_details` là **ON DELETE RESTRICT** — bắt buộc kiểm tra app trước DELETE (Task038 đã mô tả).
- **Multipart khi Cloudinary tắt:** FE gọi `multipart` trên môi trường dev không cấu hình → **400** — cần tài liệu vận hành (`CLOUDINARY_SETUP.md`) hoặc fallback JSON URL.
- **URL Cloudinary dài:** nếu `secure_url` > 500 ký tự → **400** sau upload (rủi ro hiếm — cấu hình folder/public_id ngắn).

---

## 6. Persona & RBAC

| Vai trò / quyền | Điều kiện | Task034–037, 039 | Task038, 041 |
| :--- | :--- | :--- | :--- |
| Có `can_manage_products` | JWT + permission | **Được** đọc / tạo / sửa / thêm ảnh (**JSON URL** hoặc **multipart** khi Cloudinary bật — §4.3) | **403** trên `DELETE` / `bulk-delete` (chỉ Owner — **OQ-6(a)**) |
| Thiếu permission | | **403** | **403** |
| Owner | `role` = Owner + `can_manage_products` | Giống hàng Staff (cột read/write) | **Được** `DELETE` / `bulk-delete` khi đủ điều kiện nghiệp vụ (không tồn/chứng từ) |

*(Chi tiết assert method đặt tên theo convention module `catalog` — `*AccessPolicy`.)*

---

## 7. Actor & luồng nghiệp vụ

### 7.1 Actor

| Actor | Mô tả |
| :--- | :--- |
| User | Nhân viên / chủ cửa hàng trên Mini-ERP |
| Client | SPA `mini-erp` |
| API | `smart-erp` |
| DB | PostgreSQL |

### 7.2 Luồng chính (tạo SP — tóm tắt)

1. Client `POST /products` + Bearer.  
2. API validate → kiểm tra `sku_code` unique, `category_id` tồn tại và **chưa** soft-delete (**OQ-2(a)**).  
3. Transaction: INSERT `products` → INSERT `product_units` (base) → INSERT `product_price_history`.  
4. `201` + body.

### 7.3 Sơ đồ

```mermaid
sequenceDiagram
  participant U as User
  participant C as Client
  participant A as API
  participant D as DB
  U->>C: Điền form tạo SP
  C->>A: POST /api/v1/products
  A->>D: BEGIN; INSERT products, units, price_history
  D-->>A: OK
  A-->>C: 201 + data
```

---

## 8. Hợp đồng HTTP & ví dụ JSON

### 8.1 Tổng quan endpoint

| Task | Method + path | Auth | Ghi chú |
| :--- | :--- | :--- | :--- |
| 034 | `GET /api/v1/products` | Bearer | Query §8.2 |
| 035 | `POST /api/v1/products` | Bearer | Body §8.3 |
| 036 | `GET /api/v1/products/{id}` | Bearer | |
| 037 | `PATCH /api/v1/products/{id}` | Bearer | Partial body |
| 038 | `DELETE /api/v1/products/{id}` | Bearer | **Chỉ Owner** — **OQ-6(a)** |
| 039 | `POST /api/v1/products/{id}/images` | Bearer | **`application/json`** hoặc **`multipart/form-data`** — §8.6 |
| 041 | `POST /api/v1/products/bulk-delete` | Bearer | Body `{ "ids": [] }` — **chỉ Owner** — **OQ-6(a)** |

### 8.2 `GET /api/v1/products` — query

| Param | Kiểu | Mặc định | Validation |
| :--- | :--- | :--- | :--- |
| `search` | string | — | `ILIKE` trên `name`, `sku_code`, `barcode` |
| `categoryId` | int | — | `> 0`, filter `products.category_id` |
| `status` | string | `all` | `all` \| `Active` \| `Inactive` |
| `page` | int | `1` | ≥ 1 |
| `limit` | int | `20` | 1–100 |
| `sort` | string | `id:asc` | **Whitelist:** `id:asc`, `id:desc`, `name:asc`, `name:desc`, `skuCode:asc`, `skuCode:desc`, `updatedAt:asc`, `updatedAt:desc`, `createdAt:asc`, `createdAt:desc` — khác → **400**. Với mọi giá trị whitelist **trừ** `id:asc` / `id:desc`, server áp dụng **tie-break** `products.id ASC` sau cột sort chính (tránh thứ tự không xác định khi trùng giá trị sort). |

**Ví dụ response 200 (rút gọn):** tham [`API_Task034_products_get_list.md`](../../../frontend/docs/api/API_Task034_products_get_list.md) §6.

**Quy ước — `currentPrice` khi chưa có lịch sử giá:** trả **`null`** (không dùng `0`) để tránh nhầm “miễn phí”.

### 8.3 `POST /api/v1/products` — body (đầy đủ)

```json
{
  "skuCode": "SP0001",
  "barcode": "8934563123456",
  "name": "Nước suối 500ml",
  "categoryId": 2,
  "description": null,
  "weight": 500,
  "status": "Active",
  "imageUrl": null,
  "baseUnitName": "Chai",
  "costPrice": 4000,
  "salePrice": 6000,
  "priceEffectiveDate": "2026-04-23"
}
```

**201 — ví dụ (shape tối thiểu):**

```json
{
  "success": true,
  "data": {
    "id": 12,
    "skuCode": "SP0001",
    "barcode": "8934563123456",
    "name": "Nước suối 500ml",
    "categoryId": 2,
    "categoryName": "Đồ khô",
    "imageUrl": null,
    "status": "Active",
    "currentStock": 0,
    "currentPrice": 6000,
    "createdAt": "2026-04-27T10:00:00Z",
    "updatedAt": "2026-04-27T10:00:00Z",
    "unitId": 101
  },
  "message": "Đã tạo sản phẩm"
}
```

**Lỗi (mỗi mã một ví dụ):**

**400 — validation**

```json
{
  "success": false,
  "error": "BAD_REQUEST",
  "message": "Dữ liệu không hợp lệ",
  "details": { "skuCode": "Bắt buộc" }
}
```

**404 — `categoryId` không tồn tại** *(không có row `categories.id`)*

```json
{
  "success": false,
  "error": "NOT_FOUND",
  "message": "Danh mục không tồn tại",
  "details": { "categoryId": 99999 }
}
```

**400 — `categoryId` trỏ tới danh mục đã soft-delete** *(**OQ-2(a)**)*

```json
{
  "success": false,
  "error": "BAD_REQUEST",
  "message": "Danh mục không còn hiệu lực",
  "details": { "categoryId": 2, "code": "INVALID_CATEGORY" }
}
```

**409 — SKU trùng**

```json
{
  "success": false,
  "error": "CONFLICT",
  "message": "Mã SKU đã tồn tại",
  "details": { "skuCode": "SP0001" }
}
```

**401 / 403 / 500** — cùng envelope chuẩn dự án.

### 8.4 `GET /api/v1/products/{id}` — 200

Tham chiếu Task036 §4 (đủ `units`, `images`).

**404:**

```json
{
  "success": false,
  "error": "NOT_FOUND",
  "message": "Không tìm thấy sản phẩm",
  "details": {}
}
```

### 8.5 `PATCH /api/v1/products/{id}` — body ví dụ

Task037 mẫu §4 — ít nhất một field; nếu đổi giá phải có **đủ** `salePrice` và `costPrice`.

**200:** trả object chi tiết gọn như Task036 hoặc item Task034 (team chốt một shape — khuyến nghị **Task036 gọn**).

**409** SKU trùng bản ghi khác.

### 8.6 `POST /api/v1/products/{id}/images` — hai cách (JSON và multipart)

Cùng path **`/api/v1/products/{id}/images`**, cùng **`201`**, cùng shape response `ProductImageData` (`id`, `productId`, `url`, `sortOrder`, `isPrimary`). **`can_manage_products`** + JWT (xem `ProductsController`).

#### 8.6.1 `Content-Type: application/json`

```json
{
  "url": "https://cdn.example/p/12/b.jpg",
  "sortOrder": 1,
  "isPrimary": false
}
```

**201** (ví dụ):

```json
{
  "success": true,
  "data": {
    "id": 9,
    "productId": 12,
    "url": "https://cdn.example/p/12/b.jpg",
    "sortOrder": 1,
    "isPrimary": false
  },
  "message": "Đã thêm ảnh"
}
```

#### 8.6.2 `Content-Type: multipart/form-data`

| Part / field | Bắt buộc | Mô tả |
| :--- | :---: | :--- |
| `file` | Có | Nội dung ảnh; MIME **jpeg / png / webp**; kích thước ≤ `app.cloudinary.max-file-size-bytes` (và ≤ giới hạn Spring multipart **5MB** mỗi part) |
| `sortOrder` | Không | Số nguyên ≥ 0, mặc định `0` |
| `isPrimary` | Không | `true` / `false`, mặc định `false` |

- Luồng: validate file → **Cloudinary** `uploader().upload(…)` → `secure_url` → cùng logic persist như JSON (**§4.3**).
- **`app.cloudinary.enabled=false`** hoặc bean không tạo được → **400**, message hướng dẫn bật `CLOUDINARY_*` / `app.cloudinary.enabled=true` (không fallback tự lưu file local).

**201** — `data.url` thường dạng `https://res.cloudinary.com/.../image/upload/...`.

**400 — multipart khi Cloudinary tắt (ví dụ)**

```json
{
  "success": false,
  "error": "BAD_REQUEST",
  "message": "Upload file chưa bật: đặt app.cloudinary.enabled=true và biến môi trường CLOUDINARY_*.",
  "details": {}
}
```

### 8.7 `DELETE /api/v1/products/{id}` — 200

```json
{
  "success": true,
  "data": { "id": 12, "deleted": true },
  "message": "Đã xóa sản phẩm"
}
```

**409** (tổng hợp một trong các lý do — message cụ thể theo ưu tiên Dev, **không** đổi mã):

```json
{
  "success": false,
  "error": "CONFLICT",
  "message": "Không thể xóa sản phẩm đã xuất hiện trên phiếu nhập hoặc đơn hàng hoặc còn tồn kho",
  "details": { "reason": "HAS_ORDER_LINES" }
}
```

### 8.8 `POST /api/v1/products/bulk-delete` — body

```json
{
  "ids": [12, 15, 18]
}
```

**200 — bulk-delete all-or-nothing (đã xóa hết — **OQ-3(a)**):**

```json
{
  "success": true,
  "data": { "deletedIds": [12, 15, 18], "deletedCount": 3 },
  "message": "Đã xóa các sản phẩm"
}
```

**409 — một `id` lỗi → không xóa cái nào (**OQ-3(a)**):**

```json
{
  "success": false,
  "error": "CONFLICT",
  "message": "Không thể xóa toàn bộ: ít nhất một sản phẩm không đủ điều kiện",
  "details": { "failedId": 18, "reason": "HAS_STOCK" }
}
```

### 8.9 Ghi chú envelope

- Bám `success`, `data`, `message`, `error`, `details` như các SRS trước; field `details.reason` là **gợi ý** để FE map.

---

## 9. Quy tắc nghiệp vụ

| Mã | Điều kiện | Hành động / kết quả |
| :--- | :--- | :--- |
| BR-1 | Mỗi `products` sau create | Đúng **một** `product_units` với `is_base_unit = TRUE`, `conversion_rate = 1` |
| BR-2 | Giá “hiện hành” | `effective_date` ≤ **`CURRENT_DATE`** (**OQ-1(a)**); order `effective_date DESC, id DESC`; áp dụng **per unit** (list chỉ base; detail mọi unit) |
| BR-3 | PATCH đổi `salePrice` hoặc `costPrice` | Luôn **INSERT** dòng `product_price_history` mới; không UPDATE dòng cũ |
| BR-4 | PATCH có `categoryId: null` (key có trong body) | `UPDATE products SET category_id = NULL` — SP “chưa phân loại” |
| BR-5 | Xóa SP | Chặn nếu tồn tại dòng `stock_receipt_details` hoặc `order_details` với `product_id`; chặn nếu `SUM(inventory.quantity) > 0` (an toàn Task038) |
| BR-6 | `bulk-delete` | **OQ-3(a):** validate **tất cả** `id` trước → nếu OK mới `DELETE … WHERE id = ANY(:ids)` trong **một** transaction; một lỗi → **409**, không xóa dòng nào |
| BR-7 | `POST …/images` multipart | Chỉ chấp nhận MIME **jpeg/png/webp** và size ≤ **`app.cloudinary.max-file-size-bytes`**; Cloudinary **tắt** → **400**, không lưu file local; sau upload, `secure_url` lưu `image_url` (giới hạn 500 ký tự). |
| **BR-8** | `PATCH` — phạm vi “có thay đổi” | Tính **`hasImageChange`** (so sánh tập `productimages`/primary/order/url với payload) **bên cạnh** meta/giá; nếu **chỉ** ảnh thay đổi, **vẫn 200** và cập nhật — chi tiết **§14.1** |
| **BR-9** | `POST` tạo — ảnh cùng request | Khi dùng **multipart** kèm nhiều file, xử lý bước I/O tốn thời gian (upload) **song song** (pool có giới hạn), rồi mới ghi `productimages` theo thứ tự transaction/ADR; validation MIME/size/Cloudinary tắt như **BR-7/§4.3** — **§14.2** |
| **BR-10** | `mini-erp` — màn **sửa** sản phẩm | Cập nhật ảnh trên server (mọi `PATCH`/`POST …/images`/`DELETE` liên quan bộ sưu tập theo nghiệp vụ) **chỉ** thực hiện khi user bấm **Lưu**; trước khi Lưu **không** mở tác vụ mạng để lưu ảnh. Trùng hướng **§1.1** cột mở rộng. |

---

## 10. Dữ liệu & SQL tham chiếu (Agent SQL)

### 10.1 Bảng / quan hệ (Flyway V1 — tên logic)

| Bảng | Read / Write | Ghi chú |
| :--- | :--- | :--- |
| `products` | R/W | `sku_code` UNIQUE |
| `categories` | R | JOIN tên; POST/PATCH: chỉ chấp nhận `category_id` có `deleted_at IS NULL` — nếu soft-deleted → **400** (**OQ-2(a)**) |
| `product_units` | R/W | FK `product_id` CASCADE DELETE |
| `product_price_history` | R/W | FK product, unit |
| `productimages` | R/W | V1 `ProductImages` → tên thực thi JDBC; FK `product_id` CASCADE |
| `inventory` | R | SUM quantity; CASCADE delete khi xóa product |
| `stock_receipt_details` | R | `product_id` **RESTRICT** |
| `order_details` | R | `product_id` **RESTRICT** |

### 10.2 SQL gợi ý — list (đếm total tách query hoặc window — tối thiểu)

```sql
-- Đếm total (filter giống list)
SELECT COUNT(*)::bigint
FROM products p
JOIN product_units pu ON pu.product_id = p.id AND pu.is_base_unit = TRUE
WHERE (:search IS NULL OR p.name ILIKE '%' || :search || '%' OR p.sku_code ILIKE '%' || :search || '%' OR p.barcode ILIKE '%' || :search || '%')
  AND (:category_id IS NULL OR p.category_id = :category_id)
  AND (:status = 'all' OR p.status = :status);

-- Trang dữ liệu (JOIN category, inv aggregate, lateral price) — pattern Task034 §7.1, đổi tên bảng thường
-- ORDER BY: mặc định `p.id ASC`; hoặc cột whitelist + tie-break `p.id ASC` (trừ khi sort chính đã là `p.id`).
```

Transaction **POST product** (pseudo):

```sql
BEGIN;
INSERT INTO products (category_id, sku_code, barcode, name, image_url, description, weight, status)
VALUES ($1,$2,$3,$4,$5,$6,$7,$8) RETURNING id;
INSERT INTO product_units (product_id, unit_name, conversion_rate, is_base_unit)
VALUES ($pid, $uname, 1, TRUE) RETURNING id;
INSERT INTO product_price_history (product_id, unit_id, cost_price, sale_price, effective_date)
VALUES ($pid, $uid, $cost, $sale, $eff);
COMMIT;
```

### 10.3 Index

- Đã có: `idx_products_sku`, `idx_products_name`, `idx_price_lookup`, `idx_pi_product`.
- **V15:** `uq_productimages_one_primary` (partial unique, `is_primary = TRUE`).
- Cân nhắc: composite `(category_id, status)` nếu list theo danh mục lớn — đo `EXPLAIN` sau triển khai.

### 10.4 Kiểm chứng Tester

- Tạo SP → list có `currentStock=0`, `currentPrice` khớp insert.
- PATCH giá → 2 dòng `product_price_history` cho cùng unit.
- Xóa SP có tồn → 409; xóa SP có dòng order_details (seed) → 409.
- Primary image: index **V15** + transaction reset `is_primary` / `products.image_url`.
- Multipart: môi trường **không** `CLOUDINARY_ENABLED=true` → **400** multipart; JSON URL vẫn **201**.

---

## 11. Acceptance criteria (Given / When / Then)

```text
Given user có can_manage_products và có categories + products seed
When GET /api/v1/products?page=1&limit=20&status=Active (không truyền `sort`)
Then 200 và data.total khớp COUNT filter và items.length <= 20 và **thứ tự `items[].id` không giảm** (mặc định **tăng dần theo ID** — **CR Task034**)

Given user có can_manage_products
When GET /api/v1/products?sort=id:desc
Then 200 và thứ tự `items[].id` không tăng (giảm dần theo ID)

Given SKU mới hợp lệ
When POST /api/v1/products (đủ body Task035)
Then 201 và DB có 1 products + 1 product_units base + 1 product_price_history

Given product tồn tại
When PATCH /api/v1/products/{id} chỉ { "name": "X" }
Then 200 và name đổi, giá history không thêm dòng

Given product tồn tại
When PATCH với salePrice+costPrice khác latest
Then 200 và thêm đúng 1 dòng product_price_history

Given product có inventory.quantity tổng > 0
When DELETE /api/v1/products/{id}
Then 409 và product vẫn tồn tại

Given ba id đều xóa được
When POST /api/v1/products/bulk-delete (all-or-nothing)
Then 200 và cả ba bị xóa

Given một trong ba không xóa được
When POST bulk-delete (all-or-nothing)
Then 409 và không id nào bị xóa

Given Cloudinary bật (env + app.cloudinary.enabled=true) và sản phẩm tồn tại
When POST multipart /api/v1/products/{id}/images với part file PNG hợp lệ
Then 201 và data.url là HTTPS (Cloudinary secure_url)

Given Cloudinary tắt
When POST multipart /api/v1/products/{id}/images có file
Then 400 và vẫn có thể thêm ảnh bằng POST JSON url

Given tạo SP theo phụ lục §14 (multipart metadata + 2+ file) và Cloudinary bật
When POST /api/v1/products
Then upload các file thực hiện theo tác vụ song song (cùng tối đa N luồng theo cấu hình) trước khi 201 và DB có đủ ảnh ứng với từng `secure_url` hợp lệ (hoặc 4xx/rollback theo OQ-7, contract)

Given sản phẩm tồn tại, meta+giá trùng DB, gallery ảnh khác so với bản lưu
When PATCH /api/v1/products/{id} theo body chỉ mô tả/ảnh
Then 200 và tập `productimages` cập nhật khớp, không 400/409 vì thiếu thay đổi văn bản

Given cùng product, thay đổi tối thiểu (chỉ `name` hoặc chỉ ảnh hoặc chỉ cặp giá)
When PATCH
Then 200 theo từng trường hợp, đúng nghiệp vụ lịch sử giá tại **BR-3** khi đổi giá

Given user mở form sửa sản phẩm và thêm/xóa/đổi ảnh trong giao diện
When chưa bấm Lưu
Then client không gọi API cập nhật ảnh (và không persist ảnh lên server)

Given user mở form sửa và thay đổi ảnh (state cục bộ)
When bấm Lưu
Then client mới gửi lệnh API tương ứng (một `PATCH` và/hoặc `Task039` theo bước submit — **§14.5**) và dữ liệu server cập nhật
```

---

## 12. GAP & giả định

| GAP / Giả định | Tác động | Hành động đề xuất |
| :--- | :--- | :--- |
| Task039 DDL trùng `product_images` | Tránh migration sai | Dùng bảng V1 + map `url` ↔ `image_url` (§0.1) — **giữ** |
| Phân nhánh lỗi `categoryId` | FE map message | **Đã chốt:** không tồn tại → **404**; soft-deleted → **400** + `INVALID_CATEGORY` (§8.3) |
| RBAC Admin đọc list | Task034 ghi Admin | Giả định Admin có `can_manage_products` seed — nếu không → bổ sung seed hoặc GAP |
| API markdown Task039 vs BE | Task039 có thể chưa ghi rõ multipart + env | **GAP doc API:** cập nhật `API_Task039_products_post_image.md` khi rảnh — SRS §4.3 + §8.6 là nguồn hành vi BE |
| **API markdown Task034 vs SRS (sort)** | `API_Task034_products_get_list.md` vẫn ghi mặc định `updatedAt:desc` | **GAP:** cập nhật mặc định `sort` = `id:asc`, whitelist + `id:asc`/`id:desc`, ghi tie-break `id` — khớp §8.2 SRS (**CR Task034**) |
| **CR §14** vs `API_Task035`/`Task037` | Tạo multipart + `PATCH` có ảnh / `hasImageChange` cần doc + samples mới | **GAP:** cập nhật API markdown + `samples/` — **mục §14.6**, **`API_BRIDGE` `Mode=fix-doc`** tại **§15.2** |

---

## 13. PO sign-off (Approved)

- [x] Đã trả lời / đóng các **OQ** §4.2 (OQ-1 … OQ-6)
- [x] JSON / status codes (§8) và RBAC (§6) khớp quyết định PO
- [x] In/Out scope §3 đã đồng ý; **bổ sung mã:** JSON URL + multipart Cloudinary (§4.3) — đã phản ánh vào SRS
- [x] **Drift doc ↔ code** (upload ảnh): đối chiếu `ProductsController`, `CloudinaryMediaService`, `CLOUDINARY_SETUP.md`, Flyway **V15**
- [x] **Phụ lục CR §14–§15** (tạo kèm ảnh song song, PATCH `hasImageChange`, màn sửa **Lưu** mới cập nhật ảnh, OQ-7/8, `API_BRIDGE` + mock) — *OQ-7, OQ-8 chốt tại §14.5; ủy quyền 27/04/2026*

**Chữ ký / nhãn PR:** PO — 27/04/2026 *(cập nhật nhãn ticket/PR theo quy trình team)*

---

## 14. Phụ lục CR — Tạo sản phẩm kèm upload ảnh (xử lý song song) & cập nhật khi thay đổi ảnh (PATCH)

> **Tham chiếu quy tắc gốc:** `BA` [`../../AGENTS/BA_AGENT_INSTRUCTIONS.md`](../../AGENTS/BA_AGENT_INSTRUCTIONS.md); đối chiếu mã/ drift sau triển khai: `CODEBASE_ANALYST` [`../../AGENTS/CODEBASE_ANALYST_AGENT_INSTRUCTIONS.md`](../../AGENTS/CODEBASE_ANALYST_AGENT_INSTRUCTIONS.md) mục 1–2, 5–6.

### 14.1 Mục tiêu

1. **Tạo mới (`POST /api/v1/products` — Task035):** Cho phép client gửi **cùng một thao tác tạo** cả dữ liệu sản phẩm (base unit + giá) **và** một hoặc nhiều file ảnh. Phần tốn thời gian (upload lên object storage, ví dụ **Cloudinary** khi bật cấu hình — §4.3) phải được xử lý **song song nhiều luồng** (ví dụ `ExecutorService` với kích thước pool **có giới hạn** + `CompletableFuture` / tác vụ tương tự) để rút ngắn thời gian tổng, **sau** khi từng upload thành công (hoặc sau khi có `secure_url` hợp lệ) mới ghi/đồng bộ **`productimages`** cùng `product_id` trong **các giao dịch** rõ ràng theo thiết kế Tech Lead (tránh race với ràng buộc **V15** / primary).
2. **Cập nhật (`PATCH /api/v1/products/{id}` — Task037):** Server **phải** xét **thay đổi tập ảnh** (thêm, xóa, đổi `url`/nội dung, `sortOrder`, trạng thái `isPrimary`, thay thế toàn bộ danh sách) **cùng mức** với thay đổi trường văn bản/giá. **Nếu chỉ ảnh thay đổi** còn các input meta/giá (so với DB) **trùng** thì vẫn phải **cập nhật thành công (`200`)** — tức thay đổi “chỉ từ ảnh” vẫn là **một bản cập nhật hợp lệ**. **Chỉ cần một thành phần thay đổi** (bất kỳ field nào trong phạm vi contract PATCH **hoặc** gallery) thì thực hiện cập nhật (không từ chối dạng “no fields changed” nếu ảnh đã đổi).
3. **Hành vi JSON-only hiện có (§8.3 + Task039 sau 201):** vẫn hợp lệ: tạo SP bằng **JSON** rồi gọi thêm `POST …/images` từng bước. Phụ lục này **mở rộng tùy chọn** tạo **một bước** kèm file.
4. **Mini-ERP — chức năng sửa sản phẩm (ủy quyền PO, đồng bộ BR-10, §1.1):** Thay đổi bộ sưu tập ảnh (chọn file, xóa, đổi thứ tự/ảnh bìa) ở **cấp giao diện** trước khi bấm **Lưu** = **chỉ state nội bộ**; **không** gọi `POST /products/{id}/images` hay bất kỳ API nào làm thay đổi ảnh trên server. **Khi bấm Lưu,** mới thực hiện lệnh API (cùng với cập nhật meta/giá nếu có) theo quy ước chốt **OQ-8 (§14.5)**. **Hủy/đóng** form: hủy bỏ thay đổi ảnh chưa lưu.

### 14.2 Hợp đồng hướng tới (chi tiết API doc / Dev cập nhật thêm GAP)

| Mục | Mô tả tối thiểu |
| :--- | :--- |
| **POST — `application/json`** | Giữ mẫu **§8.3**; không bắt buộc ảnh. |
| **POST — `multipart/form-data` (bổ sung)** | **Đã chốt (OQ-7):** part tên **`metadata`**, `Content-Type: text/plain` hoặc tương đương, body = chuỗi JSON cùng schema/validation **§8.3**; **một hoặc nhiều** part cùng tên **`file`** (lặp lại nhiều lần như nhiều tệp trong một request — tương thích Spring `MultipartFile[] file`). **Số tệp tối đa mỗi request:** `10` (có thể cấu hình `app.*.max-product-images-per-request` tại Dev). Thứ tự ảnh: thứ tự **các** part `file` = `sortOrder` 0, 1, 2, …; **`isPrimary` mặc định** = `file` **đầu tiên** là primary, trừ khi JSON `metadata` kèm theo tùy chọn `primaryImageIndex` (số nguyên, 0-based) — nếu có thì theo trường này. Nếu không cần metadata mở rộng, có thể chỉ dùng sắp tệp + bìa theo mặc định. |
| **Xử lý song song (đa luồng)** | Tách **validate MIME/size** theo **§4.3/BR-7**; từng file upload lên Cloudinary (khi bật) chạy **trên worker pool** song song; **chỉ khi tất cả tác vụ cần cho yêu cầu hợp lệ xong** mới persist ảnh. Giới hạn: timeout từng tác vụ, **không** vượt 10 part `file` (trừ khi cấu hình tăng có ADR). |
| **PATCH — ảnh; giao dịch với UI Lưu (OQ-8 đã chốt)** | **BE (Task037 + Task039):** Không bắt buộc gộp tất cả vào một thân `PATCH` trong v1. **Cách triển khai mặc định chấp nhận:** tại sự kiện **Lưu** trên client, thực hiện **theo thứ tự** mà `mini-erp` tập hợp: (1) `PATCH /api/v1/products/{id}` nếu có thay meta/giá; (2) các thao tác **Task039** (`POST` ảnh mới, có thể kèm `POST` URL JSON) và nếu có nghiệp vụ xóa/đổi primary — tùy cách Dev map (có thể cần endpoint xóa ảnh nếu thiếu) — **cùng một lần bấm Lưu, không tự lưu giữa chừng** (§14.1 mục 4, **BR-10**). **Tùy chọn tương lai (ADR):** một `PATCH` duy nhất mảng `images` mô tả mục tiêu. Server so sánh `hasImageChange` trên **bản gửi** khi mở rộng; hiện tài liệu **đủ** với: **chỉ gọi khi Lưu** + cập nhật đúng tập sau submit. |

### 14.3 Sơ đồ tạo mới kèm upload song song (tham chiếu)

```mermaid
sequenceDiagram
  participant U as User
  participant C as Client
  participant A as API
  participant E as Upload pool (Executor)
  participant CL as Cloudinary
  participant D as DB
  U->>C: Form tạo SP + nhiều file ảnh
  C->>A: POST /api/v1/products (multipart: metadata + files)
  A->>A: Validate JSON + số lượng/size/MIME
  A->>D: BEGIN; INSERT products, product_units, product_price_history
  D-->>A: product_id, unit_id
  par Từng file (song song tối đa N luồng)
    A->>E: submit upload task
    E->>CL: upload
    CL-->>E: secure_url
  end
  A->>A: Kết hợp kết quả, xử lý is_primary (transaction + V15)
  A->>D: INSERT productimages; COMMIT
  A-->>C: 201 + data (có thể gồm thông tin ảnh tạm/chính thức tùy shape API)
```

*(Thứ tự “INSERT sản phẩm trước, upload sau” hay “upload tạm rồi INSERT gọn gàng theo `product_id`” do Tech Lead/ADR; SRS chỉ bắt buộc **hành vi người dùng** và **song song hóa phần tốn I/O nặng**.)*

### 14.4 Ràng buộc kỹ thuật & NFR

- **Lỗi một phần khi tạo (đã chốt, 27/04/2026):** Một tệp upload thất bại (Cloudinary, validation, v.v.) → **all-or-nothing:** rollback toàn bộ request (không để sản phẩm/ảnh lệch từng phần) — cùng tinh thần **OQ-3(a)**; mã lỗi 4xx/5xx với `message` rõ, không trả 207 “thành công một nửa”.  
- **Bảo mật / ổn định:** Hạn số part, kích thước, MIME như **§4.3**; pool thread không tạo unbounded.  
- **Ghi log:** từng tác vụ upload (id request, thứ tự file) để hỗ trợ truy vết (Analyst mục 5–6).

### 14.5 Quyết định OQ-7, OQ-8 (chốt — ủy quyền PO / Owner, 27/04/2026)

| ID | Quyết định | Chi tiết |
| :--- | :--- | :--- |
| **OQ-7** | **Đã chốt** | Part `metadata` (JSON string) + nhiều part **`file`** cùng tên; tối đa **10** tệp/request; `sortOrder` theo thứ tự part; `isPrimary` = tệp đầu, hoặc tùy chọn `primaryImageIndex` trong `metadata` — xem cột **POST — multipart** tại **§14.2**. |
| **OQ-8** | **Đã chốt** | **(1) UX bắt buộc:** cập nhật ảnh khi **sửa sản phẩm** chỉ xảy ra tại sự kiện **Bấm Lưu** — **BR-10**; không auto-save. **(2) BE mặc định hợp lệ v1:** `PATCH` (meta/giá) **và** các lệnh **Task039** (và bổ sung nếu cần) **cùng một lần submit** phía client; tùy chọn sau: một `PATCH` gộp. **(3) `hasImageChange`:** so tại bước submit với dữ liệu đang gửi so DB (hoặc so state sau lần `GET` trước khi sửa). |

### 14.6 GAP tài liệu (sau G-DEV: Doc Sync + API_BRIDGE)

- Cập nhật **`API_Task035_products_post.md`**, **`API_Task037_products_patch.md`**: multipart, ví dụ JSON/ảnh, mã lỗi.  
- Bổ sung/điều chỉnh mẫu tại `frontend/docs/api/samples/Task035/`, `Task037/` nếu có.  
- Codebase đã sẵn `POST …/images` (Task039): Analyst xác minh **không drift** với flow mới tại §14.

### 14.7 Trạng thái triển khai (code — đối chiếu)

| Hạng mục | Repo |
| :--- | :--- |
| **BE** `POST` multipart + upload song song + rollback | `CatalogExecutorConfig` (`productImageUploadExecutor`), `ProductService.createWithImageFiles`, `ProductImageService.persistGalleryAfterUploads`, `ProductsController.createMultipart` |
| **FE** Lưu mới gọi API ảnh + tạo multipart | `ProductImagePanel` (`staged` / `onStagedChange`), `ProductForm`, `ProductsPage`, `postProductCreateMultipart` trong `productsApi.ts` |
| **Doc API** | `frontend/docs/api/API_Task035_products_post.md` §6b |

---

## 15. Phụ lục — Gọi Workflow chỉnh sửa (CR) & `API_BRIDGE` (mock/đồng bộ dữ liệu mẫu + contract)

> **Mục tiêu:** Khi thực hiện mục **§14**, team bám chuỗi trong [`../../AGENTS/WORKFLOW_RULE.md`](../../AGENTS/WORKFLOW_RULE.md), và bắt buộc phiên **API Bridge** cập nhật **`BRIDGE_*.md`** + **dữ liệu mẫu** (`samples/`, `endpoints/`) phục vụ mock/kiểm thử client — theo [`../../AGENTS/API_BRIDGE_AGENT_INSTRUCTIONS.md`](../../AGENTS/API_BRIDGE_AGENT_INSTRUCTIONS.md) mục 2, 3, 5–7.

### 15.1 Chuỗi Workflow (sau khi phụ lục §14 được chấp thuận)

| Bước | Agent / vai trò | Tài liệu |
| :---: | :--- | :--- |
| 0 | (Tuỳ chính sách) **BA** rà lại `§14` nếu contract mở rộng thêm (OQ-7, OQ-8 **đã chốt** tại §14.5) | [`BA_AGENT_INSTRUCTIONS.md`](../../AGENTS/BA_AGENT_INSTRUCTIONS.md) mục 2, 5F–G |
| 1 | **PM** cập nhật/ tạo ticket tại `docs/task034-041/01-pm/README.md` (việc mới, phụ thuộc) | [`WORKFLOW_RULE.md`](../../AGENTS/WORKFLOW_RULE.md) §0.1–0.2 |
| 2 | **Tech Lead** — ADR ngắn: multipart order, thread pool, transaction; tránh xung đột với V15 | `WORKFLOW_RULE` chuỗi `PM → Tech Lead` |
| 3 | **Developer** — mã theo `DEVELOPER_AGENT_INSTRUCTIONS` + `mvn verify` xanh (G-DEV) | Nhắc handoff API bridge trong G-DEV |
| 4 | **`API_BRIDGE`** — **bắt buộc** (REST `mini-erp` — `WORKFLOW_RULE` §0.3): **sau** merge BE | `Mode=verify` tối thiểu; dùng **`Mode=fix-doc`** khi cần cập nhật file `API_*.md` + **`frontend/docs/api/samples/**`** (mock lại dữ liệu mẫu) theo mục 2–3, 5–7 file bridge |
| 5 | **Tester** → **Codebase Analyst** (cập nhật drift mục 5, 6) → **Doc Sync** | `CODEBASE_ANALYST` brief; mục **§14.4** SRS |

*Sơ đồ tham chiếu:* `PM → Tech Lead → Developer → API_BRIDGE → Tester → Codebase Analyst → Doc Sync` (có thể mở nhánh `API_BRIDGE` **song song** bước tới Tester như `WORKFLOW_RULE` §0.3).

### 15.2 Khối lệnh `API_BRIDGE` — dùng sau G-DEV (cập nhật mock/contract)

Dán từng block vào chat/ticket. **Bước 0** theo hướng dẫn: đọc `frontend/AGENTS/docs/FE_API_CONNECTION_GUIDE.md` (từ repo: [`../../../frontend/AGENTS/docs/FE_API_CONNECTION_GUIDE.md`](../../../frontend/AGENTS/docs/FE_API_CONNECTION_GUIDE.md)). Một phiên = **một** `Path` (mục 1 `API_BRIDGE_AGENT_INSTRUCTIONS`).

#### Tạo sản phẩm (Task035) — đồng bộ sau thay đổi multipart/đa luồng

```text
Vai trò: API_BRIDGE. Tuân @backend/AGENTS/API_BRIDGE_AGENT_INSTRUCTIONS.md.
API_BRIDGE | Task=Task035 | Path=POST /api/v1/products | Mode=fix-doc

Context SRS: @backend/docs/srs/SRS_Task034-041_products-management.md mục §14 (multipart, upload song song).

Đọc theo thứ tự: @frontend/AGENTS/docs/FE_API_CONNECTION_GUIDE.md
→ @frontend/docs/api/API_Task035_products_post.md (bổ sung mục multipart, ví dụ đủ)
→ tạo/cập nhật mẫu tại @frontend/docs/api/samples/Task035/ nếu team dùng
→ @frontend/docs/api/endpoints/Task035.md nếu có
→ đối chiếu @backend/smart-erp/src/main/java (grep Path) — tối thiểu 1 controller/DTO

Output: @frontend/docs/api/bridge/BRIDGE_Task035_products_post.md (bảng mục 5) + mẫu request/response mock đúng thân §14/§8.
```

#### Cập nhật sản phẩm (Task037) — thay đổi ảnh trên PATCH / `hasImageChange`

```text
Vai trò: API_BRIDGE. Tuân @backend/AGENTS/API_BRIDGE_AGENT_INSTRUCTIONS.md.
API_BRIDGE | Task=Task037 | Path=PATCH /api/v1/products/{id} | Mode=fix-doc

Context SRS: @backend/docs/srs/SRS_Task034-041_products-management.md mục §14.1–14.2 (chỉ ảnh đổi vẫn 200).

Đọc: @frontend/AGENTS/docs/FE_API_CONNECTION_GUIDE.md
→ @frontend/docs/api/API_Task037_products_patch.md
→ @frontend/docs/api/samples/Task037/ (bổ sung mẫu: PATCH chỉ ảnh; mock data minh hoạ)
→ grep Path trong @backend/smart-erp/src/main/java, @frontend/mini-erp/src nếu đã móc

Output: @frontend/docs/api/bridge/BRIDGE_Task037_products_patch.md
```

#### Ảnh sản phẩm (Task039) — regression + mock JSON/multipart (sau khi C3/C5 mở rộng)

```text
Vai trò: API_BRIDGE. Tuân @backend/AGENTS/API_BRIDGE_AGENT_INSTRUCTIONS.md.
API_BRIDGE | Task=Task039 | Path=POST /api/v1/products/{id}/images | Mode=verify

Đọc: @frontend/AGENTS/docs/FE_API_CONNECTION_GUIDE.md
→ @frontend/docs/api/API_Task039_products_post_image.md
→ mẫu tại @frontend/docs/api/samples/Task039/ (nếu có)

Output: @frontend/docs/api/bridge/BRIDGE_Task039_products_post_image.md
```

**Lưu ý (mock data):** `Mode=fix-doc` nhằm **cập nhật lại** file markdown API + **`samples/*.json`** thành bộ mock mới, phục vụ `mini-erp` và Postman — **không** thay bước G-DEV; nếu chỉ đối chiếu không sửa contract, dùng `Mode=verify` thay `Mode=fix-doc` ở hai block Task035/037 ở trên.

### 15.3 Tóm tắc cho Owner

| Việc | Tài liệu |
| :--- | :--- |
| Thứ tự agent | `WORKFLOW_RULE.md` §0.1, §0.3 |
| Cập nhật bridge + mẫu (mock) | `API_BRIDGE_AGENT_INSTRUCTIONS.md` mục 1, 2b–2c, 3, 5–7 |
| Drift sau sprint | `CODEBASE_ANALYST` mục 2, 6; Doc Sync sở hữu bộ mẫu theo mục 2a/6 bridge instructions |
