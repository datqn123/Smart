-- AI catalog draft (HITL): user edits rows before commit to catalog APIs.

CREATE TABLE IF NOT EXISTS ai_catalog_draft (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         VARCHAR(64)  NOT NULL,
    tenant_id       VARCHAR(32)  NOT NULL DEFAULT '1',
    conversation_id VARCHAR(128),
    entity_type     VARCHAR(32)  NOT NULL,
    status          VARCHAR(20)  NOT NULL DEFAULT 'draft',
    payload         JSONB        NOT NULL,
    commit_result   JSONB,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    expires_at      TIMESTAMPTZ  NOT NULL,
    CONSTRAINT ck_ai_catalog_draft_entity_type
        CHECK (entity_type IN ('product', 'category', 'supplier', 'customer')),
    CONSTRAINT ck_ai_catalog_draft_status
        CHECK (status IN ('draft', 'committed', 'expired'))
);

CREATE INDEX IF NOT EXISTS ix_ai_catalog_draft_user_created
    ON ai_catalog_draft (user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS ix_ai_catalog_draft_expires
    ON ai_catalog_draft (expires_at)
    WHERE status = 'draft';

COMMENT ON TABLE ai_catalog_draft IS
    'Nháp bảng nhập liệu catalog do AI sinh; user chỉnh sửa rồi commit qua service catalog.';
