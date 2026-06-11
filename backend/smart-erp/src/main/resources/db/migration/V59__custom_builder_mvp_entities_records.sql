CREATE TABLE IF NOT EXISTS custom_entities (
    id BIGSERIAL PRIMARY KEY,
    entity_key VARCHAR(80) NOT NULL,
    label VARCHAR(160) NOT NULL,
    description TEXT,
    status VARCHAR(30) NOT NULL DEFAULT 'NeedsConfig',
    draft_version INT NOT NULL DEFAULT 1,
    published_version INT,
    etag VARCHAR(160) NOT NULL,
    created_by INT NOT NULL,
    updated_by INT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    published_at TIMESTAMPTZ,
    archived_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS custom_entity_fields (
    id BIGSERIAL PRIMARY KEY,
    entity_key VARCHAR(80) NOT NULL,
    field_key VARCHAR(80) NOT NULL,
    label VARCHAR(160) NOT NULL,
    field_type VARCHAR(40) NOT NULL,
    required BOOLEAN NOT NULL DEFAULT FALSE,
    filterable BOOLEAN NOT NULL DEFAULT FALSE,
    sortable BOOLEAN NOT NULL DEFAULT FALSE,
    searchable BOOLEAN NOT NULL DEFAULT FALSE,
    order_index INT NOT NULL DEFAULT 0,
    helper_text TEXT,
    options_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    reference_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    validation_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    default_value_json JSONB,
    status VARCHAR(30) NOT NULL DEFAULT 'Draft',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS custom_entity_views (
    id BIGSERIAL PRIMARY KEY,
    entity_key VARCHAR(80) NOT NULL,
    list_columns_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    filter_fields_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    default_sort VARCHAR(180),
    form_sections_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS custom_entity_permissions (
    id BIGSERIAL PRIMARY KEY,
    entity_key VARCHAR(80) NOT NULL,
    action VARCHAR(30) NOT NULL,
    roles_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS custom_entity_versions (
    id BIGSERIAL PRIMARY KEY,
    entity_key VARCHAR(80) NOT NULL,
    version INT NOT NULL,
    page_key VARCHAR(80) NOT NULL,
    entity_snapshot_json JSONB NOT NULL,
    fields_snapshot_json JSONB NOT NULL,
    views_snapshot_json JSONB NOT NULL,
    permissions_snapshot_json JSONB NOT NULL,
    published_by INT NOT NULL,
    published_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (entity_key, version)
);

CREATE TABLE IF NOT EXISTS custom_records (
    id BIGSERIAL PRIMARY KEY,
    entity_key VARCHAR(80) NOT NULL,
    published_version INT NOT NULL,
    values_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    state VARCHAR(30) NOT NULL DEFAULT 'Active',
    created_by INT NOT NULL,
    updated_by INT,
    deleted_by INT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_custom_entities_key_active
ON custom_entities(entity_key)
WHERE archived_at IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS ux_custom_entity_fields_key_active
ON custom_entity_fields(entity_key, field_key)
WHERE status <> 'Archived';

CREATE UNIQUE INDEX IF NOT EXISTS ux_custom_entity_permissions_action
ON custom_entity_permissions(entity_key, action);

CREATE UNIQUE INDEX IF NOT EXISTS ux_custom_entity_views_entity
ON custom_entity_views(entity_key);

CREATE INDEX IF NOT EXISTS idx_custom_entity_fields_entity_order
ON custom_entity_fields(entity_key, order_index, id);

CREATE INDEX IF NOT EXISTS idx_custom_records_entity_active
ON custom_records(entity_key, deleted_at, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_custom_records_values_gin
ON custom_records USING GIN(values_json);

INSERT INTO custom_entities (
    entity_key, label, description, status, draft_version, published_version,
    etag, created_by, updated_by, published_at
)
SELECT
    'damaged_stock_report',
    'Phiếu kiểm hàng hỏng',
    'Entity custom cho ghi nhận sản phẩm hỏng trong kho.',
    'Published',
    1,
    1,
    'entity-damaged_stock_report-draft-1',
    1,
    1,
    now()
WHERE NOT EXISTS (
    SELECT 1 FROM custom_entities WHERE entity_key = 'damaged_stock_report' AND archived_at IS NULL
);

INSERT INTO custom_entity_fields (
    entity_key, field_key, label, field_type, required, filterable, sortable,
    searchable, order_index, helper_text, reference_json, validation_json,
    default_value_json, status
)
VALUES
    ('damaged_stock_report', 'report_code', 'Mã phiếu', 'text', TRUE, TRUE, TRUE, TRUE, 0,
     'Sinh theo định dạng KH-YYYY-NNNN.', '{}'::jsonb,
     '{"pattern":"^KH-[0-9]{4}-[0-9]{4}$","message":"Mã phiếu cần theo dạng KH-YYYY-NNNN."}'::jsonb,
     '"KH-2026-0001"'::jsonb, 'Active'),
    ('damaged_stock_report', 'product_ref', 'Sản phẩm', 'reference', TRUE, TRUE, FALSE, TRUE, 1,
     'Reference canonical dùng refType/refEntityKey.',
     '{"refType":"core","refEntityKey":"products"}'::jsonb, '{}'::jsonb, NULL, 'Active'),
    ('damaged_stock_report', 'location_ref', 'Vị trí kho', 'reference', TRUE, TRUE, FALSE, FALSE, 2,
     NULL, '{"refType":"core","refEntityKey":"inventory_locations"}'::jsonb, '{}'::jsonb, NULL, 'Active'),
    ('damaged_stock_report', 'damaged_quantity', 'Số lượng hỏng', 'number', TRUE, FALSE, TRUE, FALSE, 3,
     NULL, '{}'::jsonb, '{"min":"1","max":"999"}'::jsonb, NULL, 'Active'),
    ('damaged_stock_report', 'handling_status', 'Trạng thái xử lý', 'single_select', FALSE, TRUE, FALSE, FALSE, 4,
     NULL, '{}'::jsonb, '{}'::jsonb, '"Chờ xử lý"'::jsonb, 'Active')
ON CONFLICT DO NOTHING;

INSERT INTO custom_entity_views (
    entity_key, list_columns_json, filter_fields_json, default_sort, form_sections_json
)
SELECT
    'damaged_stock_report',
    '[
      {"fieldKey":"report_code","label":"Mã phiếu","width":140,"align":"left","format":"text"},
      {"fieldKey":"product_ref","label":"Sản phẩm","width":220,"align":"left","format":"text"},
      {"fieldKey":"location_ref","label":"Vị trí","width":160,"align":"left","format":"text"},
      {"fieldKey":"damaged_quantity","label":"SL hỏng","width":120,"align":"right","format":"number"},
      {"fieldKey":"handling_status","label":"Trạng thái","width":140,"align":"left","format":"badge"}
    ]'::jsonb,
    '["report_code","product_ref","location_ref","handling_status"]'::jsonb,
    'report_code desc',
    '[
      {"id":"section-general","title":"Thông tin chung","fieldKeys":["report_code","product_ref","location_ref"]},
      {"id":"section-quantity","title":"Kiểm hàng","fieldKeys":["damaged_quantity","handling_status"]}
    ]'::jsonb
WHERE NOT EXISTS (
    SELECT 1 FROM custom_entity_views WHERE entity_key = 'damaged_stock_report'
);

INSERT INTO custom_entity_permissions(entity_key, action, roles_json)
VALUES
    ('damaged_stock_report', 'view', '["Owner","Admin","Staff","Warehouse"]'::jsonb),
    ('damaged_stock_report', 'create', '["Owner","Admin","Warehouse"]'::jsonb),
    ('damaged_stock_report', 'update', '["Owner","Admin","Warehouse"]'::jsonb),
    ('damaged_stock_report', 'delete', '["Owner","Admin"]'::jsonb)
ON CONFLICT (entity_key, action) DO NOTHING;

INSERT INTO custom_entity_versions (
    entity_key, version, page_key, entity_snapshot_json, fields_snapshot_json,
    views_snapshot_json, permissions_snapshot_json, published_by
)
SELECT
    'damaged_stock_report',
    1,
    'phieu_kiem_hang_hong',
    jsonb_build_object(
        'entityKey', e.entity_key,
        'label', e.label,
        'description', e.description,
        'status', e.status,
        'version', e.published_version
    ),
    (SELECT jsonb_agg(to_jsonb(f) ORDER BY f.order_index, f.id)
     FROM custom_entity_fields f WHERE f.entity_key = e.entity_key AND f.status <> 'Archived'),
    (SELECT to_jsonb(v) FROM custom_entity_views v WHERE v.entity_key = e.entity_key),
    (SELECT jsonb_agg(to_jsonb(p) ORDER BY p.action)
     FROM custom_entity_permissions p WHERE p.entity_key = e.entity_key),
    1
FROM custom_entities e
WHERE e.entity_key = 'damaged_stock_report'
  AND e.archived_at IS NULL
ON CONFLICT (entity_key, version) DO NOTHING;

INSERT INTO custom_records(entity_key, published_version, values_json, state, created_by, updated_by)
SELECT
    seed.entity_key,
    seed.published_version,
    seed.values_json,
    seed.state,
    seed.created_by,
    seed.updated_by
FROM (VALUES
    ('damaged_stock_report', 1,
     '{"report_code":"KH-2026-0001","product_ref":"Áo khoác chống nước","location_ref":"Kho chính / Kệ A4","damaged_quantity":6,"handling_status":"Nháp"}'::jsonb,
     'Active', 1, 1),
    ('damaged_stock_report', 1,
     '{"report_code":"KH-2026-0002","product_ref":"Bình giữ nhiệt 500ml","location_ref":"Kho phụ / Kệ B1","damaged_quantity":2,"handling_status":"Nháp"}'::jsonb,
     'Active', 1, 1)
) AS seed(entity_key, published_version, values_json, state, created_by, updated_by)
WHERE NOT EXISTS (
    SELECT 1
    FROM custom_records r
    WHERE r.entity_key = seed.entity_key
      AND r.values_json ->> 'report_code' = seed.values_json ->> 'report_code'
);
