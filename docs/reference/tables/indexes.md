# Indexes

| Table | Index Name | Columns | Notes |
|-------|-----------|---------|-------|
| ai_catalog_draft | ix_ai_catalog_draft_expires | expires_at | ((status)::text = 'draft'::text |
| ai_catalog_draft | ix_ai_catalog_draft_user_created | user_id, created_at DESC |  |
| ai_column_description | idx_ai_column_description_table_name | table_name |  |
| ai_column_description | uq_ai_column_description_table_column | table_name, column_name | UNIQUE |
| ai_inventory_draft | ix_ai_inventory_draft_expires | expires_at | ((status)::text = 'draft'::text |
| ai_inventory_draft | ix_ai_inventory_draft_user_created | user_id, created_at DESC |  |
| ai_relationship_description | uq_ai_rel_desc | from_table, from_column, to_table, to_column | UNIQUE |
| ai_table_description | uq_ai_table_description_table_name | table_name | UNIQUE |
| aichathistory | idx_chat_created_at | created_at |  |
| aichathistory | idx_chat_session | session_id |  |
| aichathistory | idx_chat_user | user_id |  |
| aiinsights | idx_ai_insight_owner | owner_id |  |
| alertsettings | idx_alert_owner | owner_id |  |
| alertsettings | uq_alert_settings_owner_alert_type | owner_id, alert_type | UNIQUE |
| cash_funds | idx_cash_funds_active_default | is_active, is_default |  |
| cash_funds | uq_cash_funds_code | code | UNIQUE |
| cashtransactions | cashtransactions_transaction_code_key | transaction_code | UNIQUE |
| cashtransactions | idx_cash_tx_created_at | created_at DESC, id DESC |  |
| cashtransactions | idx_cash_tx_date | transaction_date |  |
| cashtransactions | idx_cash_tx_status | status |  |
| categories | idx_categories_parent_id | parent_id |  |
| categories | uq_categories_category_code_active | category_code | UNIQUE (deleted_at IS NULL |
| custom_menu_folder_versions | custom_menu_folder_versions_folder_key_version_key | folder_key, version | UNIQUE |
| custom_menu_folders | ux_custom_menu_folders_key_active | folder_key | UNIQUE (archived_at IS NULL |
| custom_menu_page_versions | custom_menu_page_versions_page_key_version_key | page_key, version | UNIQUE |
| custom_menu_page_versions | idx_custom_menu_page_versions_lookup | page_key, version |  |
| custom_menu_pages | idx_custom_menu_pages_parent_order | parent_folder_key, sort_order | (archived_at IS NULL |
| custom_menu_pages | ux_custom_menu_pages_key_active | page_key | UNIQUE (archived_at IS NULL |
| custom_menu_pages | ux_custom_menu_pages_route_active | route_path | UNIQUE (archived_at IS NULL |
| customers | idx_customers_deleted_at | deleted_at | (deleted_at IS NOT NULL |
| customers | idx_customers_phone | phone |  |
| customers | uq_customers_customer_code_active | customer_code | UNIQUE (deleted_at IS NULL |
| financeledger | idx_finance_date | transaction_date |  |
| financeledger | idx_finance_type | transaction_type |  |
| financeledger | idx_financeledger_ref_dispatch | reference_type, reference_id | ((reference_type)::text = 'StockDispatch'::text |
| global_table_column_settings | uq_global_table_column_settings_table | table_key | UNIQUE |
| inventory | idx_inv_expiry_date | expiry_date |  |
| inventory | idx_inv_product | product_id |  |
| inventory | idx_inv_unit | unit_id |  |
| inventory | uq_inventory_product_location_batch | product_id, location_id, batch_number | UNIQUE |
| inventory_audit_session_events | idx_audit_session_events_session | session_id |  |
| inventoryauditlines | idx_audit_lines_session | session_id |  |
| inventoryauditsessions | idx_audit_sessions_status | status |  |
| inventoryauditsessions | inventoryauditsessions_audit_code_key | audit_code | UNIQUE |
| inventorylogs | idx_il_created_at | created_at |  |
| inventorylogs | idx_il_dispatch | dispatch_id |  |
| inventorylogs | idx_il_product | product_id |  |
| inventorylogs | idx_il_receipt | receipt_id |  |
| notifications | idx_notif_user_unread | user_id, is_read |  |
| orderdetails | idx_od_order | order_id |  |
| orderdetails | uq_od_order_product_unit | order_id, product_id, unit_id | UNIQUE |
| partnerdebts | idx_partner_debts_customer | customer_id |  |
| partnerdebts | idx_partner_debts_status | status |  |
| partnerdebts | idx_partner_debts_supplier | supplier_id |  |
| partnerdebts | idx_partnerdebts_updated_id | updated_at DESC, id DESC |  |
| partnerdebts | partnerdebts_debt_code_key | debt_code | UNIQUE |
| productimages | idx_pi_primary | product_id, is_primary |  |
| productimages | idx_pi_product | product_id |  |
| productimages | uq_productimages_one_primary | product_id | UNIQUE (is_primary = true |
| productpricehistory | idx_price_lookup | product_id, unit_id, effective_date DESC |  |
| products | idx_products_barcode | barcode |  |
| products | idx_products_name | name |  |
| products | idx_products_sku | sku_code |  |
| products | idx_products_status | status |  |
| products | products_sku_code_key | sku_code | UNIQUE |
| productunits | idx_pu_product | product_id |  |
| productunits | uq_product_unit_name | product_id, unit_name | UNIQUE |
| refresh_tokens | idx_refresh_tokens_user_id | user_id |  |
| refresh_tokens | refresh_tokens_token_key | token | UNIQUE |
| roles | roles_name_key | name | UNIQUE |
| salesorders | idx_salesorders_voucher | voucher_id |  |
| salesorders | idx_so_created_at | created_at |  |
| salesorders | idx_so_customer | customer_id |  |
| salesorders | idx_so_order_channel | order_channel |  |
| salesorders | idx_so_parent | parent_order_id |  |
| salesorders | idx_so_payment_status | payment_status |  |
| salesorders | idx_so_status | status |  |
| salesorders | idx_so_user | user_id |  |
| salesorders | salesorders_order_code_key | order_code | UNIQUE |
| staffpasswordresetrequests | idx_sp_reset_user_status | user_id, status |  |
| stockdispatch_lines | ix_stockdispatch_lines_dispatch | dispatch_id |  |
| stockdispatch_lines | uq_stockdispatch_line | dispatch_id, inventory_id | UNIQUE |
| stockdispatches | idx_sd_order | order_id |  |
| stockdispatches | idx_sd_status | status |  |
| stockdispatches | ix_stockdispatches_deleted_active | deleted_at | (deleted_at IS NULL |
| stockdispatches | stockdispatches_dispatch_code_key | dispatch_code | UNIQUE |
| stockreceiptdetails | idx_srd_receipt | receipt_id |  |
| stockreceiptdetails | uq_srd_receipt_product_batch | receipt_id, product_id, batch_number | UNIQUE |
| stockreceipts | idx_sr_receipt_date | receipt_date DESC, id DESC |  |
| stockreceipts | idx_sr_reviewed_at | reviewed_at DESC NULLS LAST |  |
| stockreceipts | idx_sr_status | status |  |
| stockreceipts | idx_sr_supplier | supplier_id |  |
| stockreceipts | stockreceipts_receipt_code_key | receipt_code | UNIQUE |
| storeprofiles | idx_store_profiles_owner | owner_id |  |
| storeprofiles | idx_storeprofiles_default_retail_location | default_retail_location_id |  |
| storeprofiles | storeprofiles_owner_id_key | owner_id | UNIQUE |
| suppliers | idx_suppliers_name | name |  |
| suppliers | idx_suppliers_phone | phone |  |
| suppliers | suppliers_supplier_code_key | supplier_code | UNIQUE |
| systemlogs | idx_syslog_created_at | created_at |  |
| systemlogs | idx_syslog_level | log_level |  |
| user_table_column_settings | idx_user_table_column_settings_user_id | user_id |  |
| user_table_column_settings | uq_user_table_column_settings_user_table | user_id, table_key | UNIQUE |
| users | idx_users_phone | phone |  |
| users | uq_users_staff_code | staff_code | UNIQUE (staff_code IS NOT NULL |
| users | users_email_key | email | UNIQUE |
| users | users_username_key | username | UNIQUE |
| voucher_redemptions | idx_voucher_redemptions_voucher | voucher_id |  |
| voucher_redemptions | uq_voucher_redemptions_order | sales_order_id | UNIQUE |
| vouchers | vouchers_code_key | code | UNIQUE |
| warehouselocations | uq_warehouse_shelf | warehouse_code, shelf_code | UNIQUE |