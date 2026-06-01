CREATE TABLE IF NOT EXISTS user_table_column_settings (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    table_key VARCHAR(80) NOT NULL,
    hidden_columns JSONB NOT NULL DEFAULT '[]'::jsonb,
    column_order JSONB NOT NULL DEFAULT '[]'::jsonb,
    updated_by BIGINT REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_user_table_column_settings_user_table UNIQUE (user_id, table_key),
    CONSTRAINT ck_user_table_column_settings_table_key CHECK (
        table_key IN ('inventory_stock', 'inventory_receipts', 'inventory_dispatch')
    )
);

CREATE INDEX IF NOT EXISTS idx_user_table_column_settings_user_id
    ON user_table_column_settings (user_id);

