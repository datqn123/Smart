CREATE TABLE IF NOT EXISTS custom_menu_folders (
    id BIGSERIAL PRIMARY KEY,
    folder_key VARCHAR(80) NOT NULL,
    label VARCHAR(160) NOT NULL,
    icon VARCHAR(80),
    description TEXT,
    status VARCHAR(30) NOT NULL DEFAULT 'Draft',
    sort_order INT NOT NULL DEFAULT 0,
    visibility_roles JSONB NOT NULL DEFAULT '[]'::jsonb,
    visibility_permissions JSONB NOT NULL DEFAULT '[]'::jsonb,
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

CREATE TABLE IF NOT EXISTS custom_menu_pages (
    id BIGSERIAL PRIMARY KEY,
    page_key VARCHAR(80) NOT NULL,
    parent_folder_key VARCHAR(80) NOT NULL,
    label VARCHAR(160) NOT NULL,
    icon VARCHAR(80),
    description TEXT,
    route_path VARCHAR(200) NOT NULL,
    entity_key VARCHAR(80) NOT NULL,
    page_type VARCHAR(40) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'NeedsConfig',
    sort_order INT NOT NULL DEFAULT 0,
    visibility_roles JSONB NOT NULL DEFAULT '[]'::jsonb,
    entity_permission VARCHAR(80),
    data_permission VARCHAR(80),
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

CREATE TABLE IF NOT EXISTS custom_menu_folder_versions (
    id BIGSERIAL PRIMARY KEY,
    folder_key VARCHAR(80) NOT NULL,
    version INT NOT NULL,
    label VARCHAR(160) NOT NULL,
    icon VARCHAR(80),
    description TEXT,
    sort_order INT NOT NULL,
    visibility_roles JSONB NOT NULL DEFAULT '[]'::jsonb,
    published_by INT NOT NULL,
    published_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (folder_key, version)
);

CREATE TABLE IF NOT EXISTS custom_menu_page_versions (
    id BIGSERIAL PRIMARY KEY,
    page_key VARCHAR(80) NOT NULL,
    version INT NOT NULL,
    parent_folder_key VARCHAR(80) NOT NULL,
    label VARCHAR(160) NOT NULL,
    icon VARCHAR(80),
    description TEXT,
    route_path VARCHAR(200) NOT NULL,
    entity_key VARCHAR(80) NOT NULL,
    page_type VARCHAR(40) NOT NULL,
    sort_order INT NOT NULL,
    visibility_roles JSONB NOT NULL DEFAULT '[]'::jsonb,
    entity_permission VARCHAR(80),
    data_permission VARCHAR(80),
    published_by INT NOT NULL,
    published_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (page_key, version)
);

CREATE TABLE IF NOT EXISTS custom_menu_events (
    id BIGSERIAL PRIMARY KEY,
    target_type VARCHAR(30) NOT NULL,
    target_key VARCHAR(80) NOT NULL,
    event_type VARCHAR(40) NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_by INT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_custom_menu_folders_key_active
ON custom_menu_folders(folder_key)
WHERE archived_at IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS ux_custom_menu_pages_key_active
ON custom_menu_pages(page_key)
WHERE archived_at IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS ux_custom_menu_pages_route_active
ON custom_menu_pages(route_path)
WHERE archived_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_custom_menu_pages_parent_order
ON custom_menu_pages(parent_folder_key, sort_order)
WHERE archived_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_custom_menu_page_versions_lookup
ON custom_menu_page_versions(page_key, version);

UPDATE roles
SET permissions = COALESCE(permissions, '{}'::jsonb)
    || jsonb_build_object('can_manage_custom_builder', TRUE, 'can_use_custom_entities', TRUE)
WHERE name IN ('Owner', 'Admin');

UPDATE roles
SET permissions = COALESCE(permissions, '{}'::jsonb)
    || jsonb_build_object('can_manage_custom_builder', FALSE, 'can_use_custom_entities', TRUE)
WHERE name = 'Staff';

INSERT INTO custom_menu_folders (
    folder_key, label, icon, description, status, sort_order, visibility_roles,
    draft_version, published_version, etag, created_by, updated_by, published_at
)
SELECT
    'kiem_hang', 'Kiểm hàng', 'folder', 'Nhóm giao diện kiểm hàng và xử lý sự cố kho.',
    'Published', 0, '["Owner","Admin","Staff","Warehouse"]'::jsonb,
    1, 1, 'folder-kiem_hang-draft-1', 1, 1, now()
WHERE NOT EXISTS (
    SELECT 1 FROM custom_menu_folders WHERE folder_key = 'kiem_hang' AND archived_at IS NULL
);

INSERT INTO custom_menu_pages (
    page_key, parent_folder_key, label, icon, description, route_path, entity_key, page_type,
    status, sort_order, visibility_roles, entity_permission, data_permission,
    draft_version, published_version, etag, created_by, updated_by, published_at
)
SELECT
    'phieu_kiem_hang_hong', 'kiem_hang', 'Phiếu kiểm hàng hỏng', 'file',
    'Ghi nhận sản phẩm hỏng và chuẩn bị quy trình kiểm duyệt.',
    '/custom/phieu_kiem_hang_hong', 'damaged_stock_report', 'table_detail',
    'Published', 0, '["Owner","Admin","Staff","Warehouse"]'::jsonb,
    'can_manage_inventory', 'can_manage_inventory',
    1, 1, 'page-phieu_kiem_hang_hong-draft-1', 1, 1, now()
WHERE NOT EXISTS (
    SELECT 1 FROM custom_menu_pages WHERE page_key = 'phieu_kiem_hang_hong' AND archived_at IS NULL
);

INSERT INTO custom_menu_folder_versions (
    folder_key, version, label, icon, description, sort_order, visibility_roles, published_by
)
SELECT folder_key, 1, label, icon, description, sort_order, visibility_roles, 1
FROM custom_menu_folders
WHERE folder_key = 'kiem_hang'
ON CONFLICT (folder_key, version) DO NOTHING;

INSERT INTO custom_menu_page_versions (
    page_key, version, parent_folder_key, label, icon, description, route_path, entity_key,
    page_type, sort_order, visibility_roles, entity_permission, data_permission, published_by
)
SELECT page_key, 1, parent_folder_key, label, icon, description, route_path, entity_key,
       page_type, sort_order, visibility_roles, entity_permission, data_permission, 1
FROM custom_menu_pages
WHERE page_key = 'phieu_kiem_hang_hong'
ON CONFLICT (page_key, version) DO NOTHING;
