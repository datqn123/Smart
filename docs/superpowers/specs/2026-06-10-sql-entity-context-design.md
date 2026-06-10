# Spec: Cải Thiện Entity Context SQL & Câu Hỏi Đề Xuất

**Ngày**: 2026-06-10
**Tác giả**: opencode
**Trạng thái**: Draft

## Vấn Đề

Ba vấn đề liên quan trong pipeline sinh SQL:

1. **Entity context bị bỏ qua**: `entity_context` (tên sản phẩm khớp từ DB lookup bằng ILIKE) được truyền vào gen_sql nhưng LLM bỏ qua, vẫn tự sinh `ILIKE '%gạo%'` thay vì dùng tên chính xác đã tìm được với `IN()`.

2. **Entity context mất giữa các lượt hội thoại**: Mỗi lượt hội thoại xây dựng lại entity_context từ đầu. Tên sản phẩm đã khớp ở lượt trước không được tái sử dụng, gây ra query ILIKE thừa và mất ngữ cảnh.

3. **Câu hỏi đề xuất cứng**: `answer_composer` dùng chuỗi follow-up tĩnh không phù hợp với ngữ cảnh query hoặc kết quả trả về.

## Thiết Kế

### Fix 1: Bắt gen_sql dùng tên chính xác từ entity_context

**Vấn đề**: Entity resolution dùng `ILIKE '%gạo%'` để tìm sản phẩm → trả về danh sách khớp → nhưng gen_sql BỎ QUA danh sách này và tự sinh `ILIKE` lại từ đầu.

**Giải pháp**: Khi entity_context đã có danh sách sản phẩm khớp, gen_sql BẮT BUỘC dùng `IN()` với tên chính xác, KHÔNG dùng ILIKE lại.

**File**: `app/graph/nodes/sql_pipeline.py` → `_build_entity_context_section()`

Hiện tại output:
```
### Entity Name References (from database)
- products: Gạo ST25, Gạo Nàng Hoa, Gạo Nhật
```

Output mới:
```
### Entity Name References (from database) — DÙNG TÊN CHÍNH XÁC NÀY
Các tên sản phẩm sau được tìm thấy trong database khớp với câu hỏi của bạn.
Bạn BẮT BUỘC dùng tên chính xác này trong SQL với mệnh đề IN():
  WHERE p.name IN ('Gạo ST25', 'Gạo Nàng Hoa', 'Gạo Nhật')
KHÔNG dùng ILIKE hoặc LIKE cho các tên có trong entity context.
Chỉ được dùng ILIKE khi phần này trống hoặc không có.

- products: Gạo ST25, Gạo Nàng Hoa, Gạo Nhật
```

### Fix 2: Giữ entity_context giữa các lượt hội thoại

#### 2.1 Cache entity_context trong harness memory

**File**: `app/harness/memory_store.py`

Thêm `entity_context` vào dữ liệu lượt hội thoại được lưu:

```python
# Trong append_turn():
turn_data = {
    "intent": intent,
    "tools_used": tools,
    "entity_context": entity_context,  # MỚI
    ...
}
```

#### 2.2 Gộp entity_context từ cache khi resolution

**File**: `app/graph/tools/sql_query.py` (harness tool path) và `app/graph/nodes/sql_pipeline.py` (subgraph path)

Trước khi chạy entity resolution, kiểm tra context đã cache từ các lượt trước trong cùng thread. Gộp kết quả mới với context đã cache:

```python
def merge_entity_context(fresh: dict, cached: dict) -> dict:
    merged = dict(cached)
    for table, data in fresh.items():
        if table not in merged:
            merged[table] = data
        else:
            # Gộp exact_matches và fuzzy_matches, loại trùng
            existing_names = set(merged[table].get("exact_matches", []))
            for match_type in ("exact_matches", "fuzzy_matches"):
                for name in (data.get(match_type) or []):
                    if name not in existing_names:
                        merged[table].setdefault(match_type, []).append(name)
                        existing_names.add(name)
    return merged
```

### Fix 3: Câu hỏi đề xuất động theo ngữ cảnh

#### 3.1 Sinh follow-up theo ngữ cảnh

**File**: `app/graph/tools/answer_composer.py`

Thay thế follow-up cứng bằng hàm sinh theo ngữ cảnh:

```python
def _generate_follow_ups(
    intent: str,
    row_count: int,
    has_time_filter: bool,
    domain: str,
) -> list[str]:
    follow_ups = []

    if row_count == 0:
        follow_ups.append("Bạn có muốn thử với khoảng thời gian khác không?")
    else:
        if not has_time_filter:
            follow_ups.append("Bạn có muốn xem theo tháng/quý/năm không?")

        if domain in ("dispatch", "sales"):
            follow_ups.append("Bạn có muốn xem chi tiết theo đơn hàng không?")
        elif domain == "inventory":
            follow_ups.append("Bạn có muốn xem theo kho không?")

        if row_count > 1:
            follow_ups.append("Bạn có muốn xem top 10 chi tiết không?")

    return follow_ups[:3]  # Tối đa 3 gợi ý
```

Phương thức `invoke()` truyền ngữ cảnh từ observations:
```python
# Trích xuất ngữ cảnh từ observations
has_time_filter = any("thời gian" in obs.get("message", "") or "month" in obs.get("message", "")
                      for obs in observations)
domain = infer_domain_from_observations(observations)
```

## Thứ Tự Triển Khai

1. **Fix 1** (entity_context prompt) - thay đổi nhỏ nhất, tác động ngay
2. **Fix 3** (follow-up động) - thay đổi cô lập trong answer_composer
3. **Fix 2** (entity_context caching) - cần thay đổi harness memory

## Đánh Giá Rủi Ro

| Fix | Rủi ro | Giảm thiểu |
|-----|--------|------------|
| 1. Entity prompt | Thấp - thay đổi bổ sung | LLM có thể vẫn bỏ qua; cần theo dõi |
| 2. Entity caching | Trung bình - tăng bộ nhớ | Giới hạn kích thước cache, TTL theo thread |
| 3. Follow-up động | Thấp - thay đổi cô lập | Fallback về static nếu thiếu ngữ cảnh |

## Kiểm Thử

- Unit test: `_build_entity_context_section()` sinh đúng định dạng
- Unit test: `merge_entity_context()` loại trùng đúng cách
- Unit test: `_generate_follow_ups()` trả về gợi ý phù hợp ngữ cảnh
- Integration test: gen_sql dùng mệnh đề IN() khi entity_context có kết quả khớp
- Integration test: entity_context tồn tại qua 2+ lượt hội thoại trong cùng thread
