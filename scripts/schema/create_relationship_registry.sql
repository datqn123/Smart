-- Registry mô tả quan hệ (from_table → to_table) cho AI.
-- Consumer: ai_python pg_schema_context._fetch_relationship_descriptions().
-- Phụ thuộc V44/V45 ai_table_description: FK đảm bảo chỉ mô tả quan hệ cho bảng đã đăng ký.

CREATE TABLE IF NOT EXISTS ai_relationship_description (
    id           BIGSERIAL PRIMARY KEY,
    from_table   VARCHAR(128) NOT NULL,
    from_column  VARCHAR(128) NOT NULL,
    to_table     VARCHAR(128),
    to_column    VARCHAR(128),
    description  TEXT           NOT NULL DEFAULT '',
    created_at   TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_ai_rel_desc_from_table_lower
        CHECK (from_table = lower(from_table)),
    CONSTRAINT ck_ai_rel_desc_from_table_nonempty
        CHECK (length(trim(from_table)) > 0),
    CONSTRAINT ck_ai_rel_desc_from_col_lower
        CHECK (from_column = lower(from_column)),
    CONSTRAINT ck_ai_rel_desc_from_col_nonempty
        CHECK (length(trim(from_column)) > 0),
    CONSTRAINT ck_ai_rel_desc_to_table_lower
        CHECK (to_table IS NULL OR to_table = lower(to_table)),
    CONSTRAINT ck_ai_rel_desc_to_col_lower
        CHECK (to_column IS NULL OR to_column = lower(to_column)),
    CONSTRAINT uq_ai_rel_desc
        UNIQUE (from_table, from_column, to_table, to_column),
    CONSTRAINT fk_ai_rel_desc_from_table
        FOREIGN KEY (from_table) REFERENCES ai_table_description (table_name) ON DELETE CASCADE
);

COMMENT ON TABLE ai_relationship_description IS
    'Business descriptions for FK relationships — tells LLM what the relationship means semantically.';

COMMENT ON COLUMN ai_relationship_description.from_table IS 'Source (FK) table name';
COMMENT ON COLUMN ai_relationship_description.from_column IS 'FK column in source table';
COMMENT ON COLUMN ai_relationship_description.to_table IS 'Referenced table (nullable for non-FK descriptions)';
COMMENT ON COLUMN ai_relationship_description.to_column IS 'Referenced column (nullable)';
COMMENT ON COLUMN ai_relationship_description.description IS 'Business semantics. E.g. "Mỗi sản phẩm thuộc một danh mục. Filter danh mục dùng categories.name"';

-- Register in ai_table_description metadata (idempotent)
INSERT INTO ai_table_description (table_name, description)
SELECT 'ai_relationship_description',
       'Registry mô tả quan hệ bảng (from_table → to_table) cho prompt AI; downstream merge vào enriched schema.'
WHERE NOT EXISTS (
    SELECT 1 FROM ai_table_description t WHERE t.table_name = 'ai_relationship_description'
);
