# API Task111 — Chế độ tương tác chat AI + SSE `data_table`

## POST `/api/v1/ai/chat/stream` (Spring relay → Python)

### Request body

```json
{
  "message": "Hiển thị danh sách sản phẩm gần hết hạn",
  "conversationId": "uuid-thread",
  "interactionMode": "data_table"
}
```

| `interactionMode` | Mô tả |
|-------------------|--------|
| `auto` (mặc định) | AI phân loại intent |
| `data_query` | Truy vấn SQL + tóm tắt text |
| `data_table` | Truy vấn SQL + bảng read-only UI |
| `chart` | Pipeline biểu đồ |
| `catalog_draft` | Bảng nhập catalog (HITL) |

Relay chuyển sang Python: `options.interaction_mode` (snake_case).

### SSE events

| Event | Payload |
|-------|---------|
| `delta` | Text stream |
| `data_table` | JSON bảng kết quả (read-only) |
| `chart` | JSON chart spec |
| `draft` | JSON catalog draft |
| `done` | Kết thúc |
| `error` | Thông báo lỗi |

### `data_table` payload

```json
{
  "title": "Kết quả truy vấn",
  "columns": [{ "key": "sku", "label": "SKU", "type": "string" }],
  "rows": [{ "sku": "A001" }],
  "rowCount": 42,
  "truncated": false,
  "maxDisplayRows": 200
}
```

Tối đa **200** dòng hiển thị; `truncated: true` khi kết quả SQL dài hơn.
