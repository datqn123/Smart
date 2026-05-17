---
name: Spring AI table description registry
overview: "Spring Boot sở hữu PostgreSQL DDL/migration và seed cho bảng đăng ký mô tả bảng (id + tên bảng + description), quyền đọc, và (tuỳ chọn) API nội bộ để ai_python merge vào schema/YAML. Không chứa LangGraph."
consumer_plan: "Plan Python AGENT_SQL — Cursor `c:/Users/Admin/.cursor/plans/nâng_cấp_agent_sql_973e9b61.plan.md` (todo pg-reader-layer; không todo DDL)."
todos:
  - id: ddl-migration
    content: "Thêm migration Flyway/Liquibase (hoặc script SQL chuẩn repo backend) tạo bảng registry mô tả bảng + PK + index tên bảng"
    status: pending
  - id: entity-repository
    content: "Entity/JDBC repository read-only + (tuỳ chọn) service seed dữ liệu mẫu / import"
    status: pending
  - id: internal-api-optional
    content: "Tuỳ chọn endpoint nội bộ secured (vd. role ADMIN hoặc service token) trả JSON list {tableName, description} cho job merge YAML"
    status: pending
  - id: docs-handoff
    content: "Ghi rõ tên bảng vật lý, schema, contract join với SchemaArtifact.tables[].name; liên kết tới plan Python"
    status: pending
isProject: true
---

# Plan Spring — bảng mô tả bảng cho AI (PostgreSQL)

## Mục tiêu

- Tạo và duy trì **một bảng registry** trong PostgreSQL lưu mô tả nghiệp vụ theo bảng dữ liệu ERP, để downstream (Python `ai_python`) đưa vào prompt SQL **mà không** cho LLM kết nối DB.
- Toàn bộ **DDL, migration, JPA/JdbcTemplate, quyền DB** nằm trong **`backend/smart-erp`** (hoặc module DB bạn đang dùng) — **không** đặt migration tạo bảng này trong `ai_python`.

## Hợp đồng dữ liệu (tối thiểu 3 cột nghiệp vụ)

- **`id`**: khóa chính (`bigserial` hoặc `uuid`).
- **Tên bảng**: một cột duy nhất khớp tên vật lý trong PostgreSQL / khóa join với `SchemaArtifact.tables[].name` (vd. cột `table_name` hoặc `name_table` — **chốt một tên** trong migration và ghi vào handoff docs).
- **`description`**: `text`, mô tả nghiệp vụ (có thể ràng buộc độ dài ở tầng ứng dụng).

### Gợi ý kỹ thuật bổ sung (không bắt buộc tối thiểu)

- `created_at` / `updated_at`, `version` nếu cần audit.
- **Unique** trên cột tên bảng (một dòng mô tả / bảng).
- **Index** trên tên bảng (lookup theo merge).
- Đặt bảng dưới schema riêng (vd. `ai_meta`) hoặc prefix tên bảng (vd. `ai_table_description`) để tránh xung đột với bảng nghiệp vụ.

## Phạm vi triển khai Spring

1. **Migration**: script idempotent theo chuẩn dự án (Flyway trong `backend/smart-erp` nếu đã dùng).
2. **Entity + repository**: đọc danh sách mô tả (read-only use case); ghi/seed có thể qua migration SQL, data.sql, hoặc endpoint admin sau.
3. **Bảo mật**: không expose công khai không auth; nếu có API export cho Python thì **nội bộ** + Spring Security (service account / role hẹp).
4. **Handoff Python**: tài liệu một dòng ghi tên bảng + tên cột + format JSON mẫu để plan `ai_python` (`pg-reader-layer` / merge YAML) gọi hoặc để vận hành export thủ công.

## Ngoài phạm vi

- LangGraph, `gen_sql`, `SchemaLoader` implementation trong Python (thuộc plan AGENT_SQL riêng).
- Thay đổi contract executor SQL read-only hiện có (trừ khi cùng task tách biệt được review).

## Nghiệm thu

- Migration chạy trên DB dev: bảng tồn tại, unique + index đúng.
- Ít nhất một row seed hoặc hướng dẫn insert mẫu; join logic với tên bảng trong schema AI được xác nhận với team Python.

## Liên kết

- Consumer: plan nâng cấp AGENT_SQL (Python) — mục «Bảng mô tả bảng» và todo `pg-reader-layer` (merge mô tả / optional HTTP), **không** todo tạo bảng trong Python.
