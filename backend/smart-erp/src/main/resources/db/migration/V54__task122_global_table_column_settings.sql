CREATE TABLE IF NOT EXISTS global_table_column_settings (
    id BIGSERIAL PRIMARY KEY,
    table_key VARCHAR(80) NOT NULL,
    hidden_columns JSONB NOT NULL DEFAULT '[]'::jsonb,
    column_order JSONB NOT NULL DEFAULT '[]'::jsonb,
    updated_by BIGINT REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_global_table_column_settings_table UNIQUE (table_key),
    CONSTRAINT ck_global_table_column_settings_table_key CHECK (
        table_key IN ('inventory_stock', 'inventory_receipts', 'inventory_dispatch')
    )
);
