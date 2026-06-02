ALTER TABLE global_table_column_settings
    DROP CONSTRAINT IF EXISTS ck_global_table_column_settings_table_key;

ALTER TABLE global_table_column_settings
    ADD CONSTRAINT ck_global_table_column_settings_table_key CHECK (
        table_key IN (
            'inventory_stock',
            'inventory_receipts',
            'inventory_dispatch',
            'product_categories',
            'product_list',
            'product_suppliers',
            'product_customers'
        )
    );

ALTER TABLE user_table_column_settings
    DROP CONSTRAINT IF EXISTS ck_user_table_column_settings_table_key;

ALTER TABLE user_table_column_settings
    ADD CONSTRAINT ck_user_table_column_settings_table_key CHECK (
        table_key IN (
            'inventory_stock',
            'inventory_receipts',
            'inventory_dispatch',
            'product_categories',
            'product_list',
            'product_suppliers',
            'product_customers'
        )
    );
