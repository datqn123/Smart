# Custom Interface API Contracts

Base path: `/api/v1/custom`

> Response envelope: `{ success: boolean, data: T, message: string }`

---

## GET /api/v1/custom/menu-tree

**Mô tả:** Lấy cây menu bản nháp (dành cho builder).

**Auth:** JWT + `can_manage_custom_builder`

**Response 200:**
```json
{
  "success": true,
  "data": {
    "treeEtag": "string — ETag của toàn bộ cây",
    "folders": [
      {
        "nodeType": "string — 'FOLDER'",
        "id": "string — UUID",
        "key": "string — Key duy nhất",
        "label": "string — Nhãn hiển thị",
        "icon": "string — Icon class",
        "description": "string — Mô tả",
        "status": "string — 'draft' | 'published'",
        "sortOrder": "int — Thứ tự sắp xếp",
        "roles": ["string — Danh sách role được phép xem"],
        "version": "int — Phiên bản hiện tại",
        "draftVersion": "int|null — Phiên bản nháp",
        "publishedVersion": "int|null — Phiên bản đã publish",
        "hasDraft": "boolean — Có nháp chưa publish?",
        "publishedAt": "datetime|null — Thời điểm publish",
        "publishedByName": "string|null — Người publish",
        "updatedAt": "datetime — Thời điểm cập nhật",
        "updatedByName": "string — Người cập nhật",
        "etag": "string — ETag của folder",
        "validationSummary": {
          "valid": "boolean — Hợp lệ?",
          "errors": [
            { "section": "string", "message": "string", "fieldKey": "string|null" }
          ],
          "warnings": [
            { "section": "string", "message": "string", "fieldKey": "string|null" }
          ]
        },
        "children": [
          {
            "nodeType": "string — 'PAGE'",
            "id": "string — UUID",
            "key": "string — Key duy nhất",
            "label": "string — Nhãn hiển thị",
            "icon": "string — Icon class",
            "parentKey": "string — Key của folder cha",
            "routePath": "string — Đường dẫn route",
            "entityKey": "string|null — Key entity liên kết",
            "pageType": "string — Loại trang",
            "status": "string — 'draft' | 'published'",
            "sortOrder": "int — Thứ tự sắp xếp",
            "description": "string — Mô tả",
            "roles": ["string — Danh sách role được phép xem"],
            "entityPermission": "string|null — Quyền entity",
            "dataPermission": "string|null — Quyền dữ liệu",
            "version": "int — Phiên bản hiện tại",
            "draftVersion": "int|null — Phiên bản nháp",
            "publishedVersion": "int|null — Phiên bản đã publish",
            "hasDraft": "boolean — Có nháp chưa publish?",
            "publishedAt": "datetime|null — Thời điểm publish",
            "publishedByName": "string|null — Người publish",
            "updatedAt": "datetime — Thời điểm cập nhật",
            "updatedByName": "string — Người cập nhật",
            "etag": "string — ETag của page",
            "validationSummary": {
              "valid": "boolean",
              "errors": [{ "section": "string", "message": "string", "fieldKey": "string|null" }],
              "warnings": [{ "section": "string", "message": "string", "fieldKey": "string|null" }]
            }
          }
        ]
      }
    ]
  },
  "message": "Thành công"
}
```

**Errors:** 401 (unauthorized), 403 (thiếu quyền)

---

## POST /api/v1/custom/menu-folders

**Mô tả:** Tạo folder menu mới (lưu nháp).

**Auth:** JWT + `can_manage_custom_builder`

**Request body:**
```json
{
  "key": "string (required) — Key duy nhất",
  "label": "string (required) — Nhãn hiển thị",
  "icon": "string (optional) — Icon class",
  "description": "string (optional) — Mô tả",
  "visibilityRoles": ["string (optional) — Danh sách role được xem"],
  "sortOrder": "int (optional) — Thứ tự sắp xếp",
  "etag": "string (optional) — ETag để kiểm soát đồng thời"
}
```

**Response 200:** `CustomMenuTreeData` (xem GET menu-tree)

**Errors:** 400 (validation), 401, 403

**Message:** `"Đã lưu bản nháp cấu hình giao diện"`

---

## PATCH /api/v1/custom/menu-folders/{folderKey}

**Mô tả:** Cập nhật folder menu.

**Auth:** JWT + `can_manage_custom_builder`

**Request body:**
```json
{
  "key": "string (optional) — Key mới",
  "label": "string (optional) — Nhãn hiển thị",
  "icon": "string (optional) — Icon class",
  "description": "string (optional) — Mô tả",
  "visibilityRoles": ["string (optional) — Danh sách role được xem"],
  "sortOrder": "int (optional) — Thứ tự sắp xếp",
  "etag": "string (optional) — ETag để kiểm soát đồng thời"
}
```

**Response 200:** `CustomMenuTreeData`

**Errors:** 400 (validation), 401, 403, 404 (không tìm thấy folder), 409 (etag conflict)

**Message:** `"Đã lưu bản nháp cấu hình giao diện"`

---

## POST /api/v1/custom/menu-pages

**Mô tả:** Tạo page menu mới (lưu nháp).

**Auth:** JWT + `can_manage_custom_builder`

**Request body:**
```json
{
  "parentKey": "string (required) — Key của folder cha",
  "key": "string (required) — Key duy nhất",
  "label": "string (required) — Nhãn hiển thị",
  "icon": "string (optional) — Icon class",
  "description": "string (optional) — Mô tả",
  "routePath": "string (optional) — Đường dẫn route",
  "entityKey": "string (optional) — Key entity liên kết",
  "pageType": "string (optional) — Loại trang",
  "visibilityRoles": ["string (optional) — Danh sách role được xem"],
  "entityPermission": "string (optional) — Quyền entity",
  "dataPermission": "string (optional) — Quyền dữ liệu",
  "sortOrder": "int (optional) — Thứ tự sắp xếp",
  "etag": "string (optional) — ETag để kiểm soát đồng thời"
}
```

**Response 200:** `CustomMenuTreeData`

**Errors:** 400 (validation), 401, 403

**Message:** `"Đã lưu bản nháp cấu hình giao diện"`

---

## PATCH /api/v1/custom/menu-pages/{pageKey}

**Mô tả:** Cập nhật page menu.

**Auth:** JWT + `can_manage_custom_builder`

**Request body:**
```json
{
  "parentKey": "string (optional) — Key folder cha mới",
  "key": "string (optional) — Key mới",
  "label": "string (optional) — Nhãn hiển thị",
  "icon": "string (optional) — Icon class",
  "description": "string (optional) — Mô tả",
  "routePath": "string (optional) — Đường dẫn route",
  "entityKey": "string (optional) — Key entity liên kết",
  "pageType": "string (optional) — Loại trang",
  "visibilityRoles": ["string (optional) — Danh sách role được xem"],
  "entityPermission": "string (optional) — Quyền entity",
  "dataPermission": "string (optional) — Quyền dữ liệu",
  "sortOrder": "int (optional) — Thứ tự sắp xếp",
  "etag": "string (optional) — ETag để kiểm soát đồng thời"
}
```

**Response 200:** `CustomMenuTreeData`

**Errors:** 400, 401, 403, 404, 409

**Message:** `"Đã lưu bản nháp cấu hình giao diện"`

---

## PATCH /api/v1/custom/menu-folders/{folderKey}/archive

**Mô tả:** Ẩn (archive) một folder menu.

**Auth:** JWT + `can_manage_custom_builder`

**Response 200:** `CustomMenuTreeData`

**Errors:** 401, 403, 404

**Message:** `"Đã ẩn danh mục menu"`

---

## PATCH /api/v1/custom/menu-pages/{pageKey}/archive

**Mô tả:** Ẩn (archive) một page menu.

**Auth:** JWT + `can_manage_custom_builder`

**Response 200:** `CustomMenuTreeData`

**Errors:** 401, 403, 404

**Message:** `"Đã ẩn giao diện tùy chỉnh"`

---

## POST /api/v1/custom/menu/reorder

**Mô tả:** Sắp xếp lại thứ tự folder và page.

**Auth:** JWT + `can_manage_custom_builder`

**Request body:**
```json
{
  "etag": "string (optional) — ETag để kiểm soát đồng thời",
  "folders": [
    {
      "key": "string — Key folder",
      "sortOrder": "int — Thứ tự mới",
      "pages": [
        {
          "key": "string — Key page",
          "sortOrder": "int — Thứ tự mới trong folder"
        }
      ]
    }
  ]
}
```

**Response 200:** `CustomMenuTreeData`

**Errors:** 400 (validation), 401, 403

**Message:** `"Đã cập nhật thứ tự giao diện"`

---

## POST /api/v1/custom/menu/validate

**Mô tả:** Kiểm tra tính hợp lệ của cấu hình trước khi publish.

**Auth:** JWT + `can_manage_custom_builder`

**Response 200:**
```json
{
  "success": true,
  "data": {
    "valid": "boolean — Toàn bộ cấu hình hợp lệ?",
    "errors": [
      { "section": "string", "message": "string", "fieldKey": "string|null" }
    ],
    "warnings": [
      { "section": "string", "message": "string", "fieldKey": "string|null" }
    ]
  },
  "message": "Thành công"
}
```

**Errors:** 401, 403

---

## POST /api/v1/custom/menu/publish

**Mô tả:** Publish cấu hình giao diện lên môi trường chạy thực tế.

**Auth:** JWT + `can_manage_custom_builder`

**Request body:**
```json
{
  "scope": "string (optional) — Phạm vi publish",
  "etag": "string (optional) — ETag để kiểm soát đồng thời"
}
```

**Response 200:** `CustomMenuTreeData`

**Errors:** 400 (validation lỗi), 401, 403, 409 (etag conflict)

**Message:** `"Đã publish cấu hình giao diện"`

---

## GET /api/v1/custom/runtime-menu

**Mô tả:** Lấy cây menu đã publish dành cho người dùng runtime.

**Auth:** JWT

**Response 200:** `CustomMenuTreeData` (chỉ gồm các mục đã publish)

**Errors:** 401

---

## GET /api/v1/custom/pages/{pageKey}/runtime

**Mô tả:** Lấy thông tin runtime của một page cụ thể.

**Auth:** JWT

**Path params:**
- `pageKey`: Key của page

**Response 200:** `CustomMenuTreeData`

**Errors:** 401, 404
