# Core Tables

## ai_catalog_draft
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY, NOT NULL, DEFAULT gen_random_uuid() |
| user_id | VARCHAR(64) | NOT NULL |
| tenant_id | VARCHAR(32) | NOT NULL, DEFAULT '1' varying |
| conversation_id | VARCHAR(128) |  |
| entity_type | VARCHAR(32) | NOT NULL |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'draft' varying |
| payload | JSONB | NOT NULL |
| commit_result | JSONB |  |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| expires_at | TIMESTAMPTZ | NOT NULL |

## ai_column_description
| Column | Type | Constraints |
|--------|------|-------------|
| id | BIGINT | PRIMARY KEY, NOT NULL, DEFAULT nextval('ai_column_description_id_seq') |
| table_name | VARCHAR(128) | FK -> ai_table_description(table_name), NOT NULL |
| column_name | VARCHAR(128) | NOT NULL |
| description | TEXT | NOT NULL, DEFAULT '' |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |

## ai_inventory_draft
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY, NOT NULL, DEFAULT gen_random_uuid() |
| user_id | VARCHAR(64) | NOT NULL |
| tenant_id | VARCHAR(32) | NOT NULL, DEFAULT '1' varying |
| conversation_id | VARCHAR(128) |  |
| entity_type | VARCHAR(32) | NOT NULL |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'draft' varying |
| payload | JSONB | NOT NULL |
| commit_result | JSONB |  |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| expires_at | TIMESTAMPTZ | NOT NULL |

## ai_relationship_description
| Column | Type | Constraints |
|--------|------|-------------|
| id | BIGINT | PRIMARY KEY, NOT NULL, DEFAULT nextval('ai_relationship_description_id_seq') |
| from_table | VARCHAR(128) | FK -> ai_table_description(table_name), NOT NULL |
| from_column | VARCHAR(128) | NOT NULL |
| to_table | VARCHAR(128) |  |
| to_column | VARCHAR(128) |  |
| description | TEXT | NOT NULL, DEFAULT '' |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |

## ai_table_description
| Column | Type | Constraints |
|--------|------|-------------|
| id | BIGINT | PRIMARY KEY, NOT NULL, DEFAULT nextval('ai_table_description_id_seq') |
| table_name | VARCHAR(128) | NOT NULL, UNIQUE |
| description | TEXT | NOT NULL, DEFAULT '' |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |

## aichathistory
| Column | Type | Constraints |
|--------|------|-------------|
| id | INT | PRIMARY KEY, NOT NULL, DEFAULT nextval('aichathistory_id_seq') |
| user_id | INT | FK -> users(id), NOT NULL |
| session_id | VARCHAR(100) |  |
| message | TEXT | NOT NULL |
| sender | VARCHAR(10) | NOT NULL |
| intent | JSONB |  |
| response_time_ms | INT |  |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |

## aiinsights
| Column | Type | Constraints |
|--------|------|-------------|
| id | INT | PRIMARY KEY, NOT NULL, DEFAULT nextval('aiinsights_id_seq') |
| owner_id | INT | FK -> users(id), NOT NULL |
| dashboard_snapshot | JSONB | NOT NULL |
| prompt | TEXT | NOT NULL |
| ai_advice | TEXT | NOT NULL |
| model_used | VARCHAR(100) |  |
| tokens_used | INT |  |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |

## alertsettings
| Column | Type | Constraints |
|--------|------|-------------|
| id | INT | PRIMARY KEY, NOT NULL, DEFAULT nextval('alertsettings_id_seq') |
| owner_id | INT | FK -> users(id), NOT NULL |
| alert_type | VARCHAR(30) | NOT NULL |
| threshold_value | NUMERIC |  |
| channel | VARCHAR(20) | NOT NULL |
| frequency | VARCHAR(20) | NOT NULL, DEFAULT 'Realtime' varying |
| is_enabled | BOOLEAN | NOT NULL, DEFAULT true |
| recipients | JSONB |  |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |

## cash_funds
| Column | Type | Constraints |
|--------|------|-------------|
| id | INT | PRIMARY KEY, NOT NULL, DEFAULT nextval('cash_funds_id_seq') |
| code | VARCHAR(30) | NOT NULL, UNIQUE |
| name | VARCHAR(255) | NOT NULL |
| is_default | BOOLEAN | NOT NULL, DEFAULT false |
| is_active | BOOLEAN | NOT NULL, DEFAULT true |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |

## cashtransactions
| Column | Type | Constraints |
|--------|------|-------------|
| id | INT | PRIMARY KEY, NOT NULL, DEFAULT nextval('cashtransactions_id_seq') |
| transaction_code | VARCHAR(50) | NOT NULL, UNIQUE |
| direction | VARCHAR(10) | NOT NULL |
| amount | NUMERIC | NOT NULL |
| category | VARCHAR(500) | NOT NULL |
| description | TEXT |  |
| payment_method | VARCHAR(30) | NOT NULL, DEFAULT 'Cash' varying |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'Pending' varying |
| transaction_date | DATE | NOT NULL |
| finance_ledger_id | INT | FK -> financeledger(id) |
| created_by | INT | FK -> users(id), NOT NULL |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| performed_by | INT | FK -> users(id), NOT NULL |
| fund_id | INT | FK -> cash_funds(id), NOT NULL |

## categories
| Column | Type | Constraints |
|--------|------|-------------|
| id | INT | PRIMARY KEY, NOT NULL, DEFAULT nextval('categories_id_seq') |
| category_code | VARCHAR(50) | NOT NULL |
| name | VARCHAR(255) | NOT NULL |
| description | TEXT |  |
| parent_id | INT | FK -> categories(id) |
| sort_order | INT | NOT NULL, DEFAULT 0 |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'Active' varying |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| deleted_at | TIMESTAMPTZ | (soft delete) |

## custom_menu_events
| Column | Type | Constraints |
|--------|------|-------------|
| id | BIGINT | PRIMARY KEY, NOT NULL, DEFAULT nextval('custom_menu_events_id_seq') |
| target_type | VARCHAR(30) | NOT NULL |
| target_key | VARCHAR(80) | NOT NULL |
| event_type | VARCHAR(40) | NOT NULL |
| payload | JSONB | NOT NULL, DEFAULT '{}' |
| created_by | INT | NOT NULL |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

## custom_menu_folder_versions
| Column | Type | Constraints |
|--------|------|-------------|
| id | BIGINT | PRIMARY KEY, NOT NULL, DEFAULT nextval('custom_menu_folder_versions_id_seq') |
| folder_key | VARCHAR(80) | NOT NULL |
| version | INT | NOT NULL |
| label | VARCHAR(160) | NOT NULL |
| icon | VARCHAR(80) |  |
| description | TEXT |  |
| sort_order | INT | NOT NULL |
| visibility_roles | JSONB | NOT NULL, DEFAULT '[]' |
| published_by | INT | NOT NULL |
| published_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

## custom_menu_folders
| Column | Type | Constraints |
|--------|------|-------------|
| id | BIGINT | PRIMARY KEY, NOT NULL, DEFAULT nextval('custom_menu_folders_id_seq') |
| folder_key | VARCHAR(80) | NOT NULL |
| label | VARCHAR(160) | NOT NULL |
| icon | VARCHAR(80) |  |
| description | TEXT |  |
| status | VARCHAR(30) | NOT NULL, DEFAULT 'Draft' varying |
| sort_order | INT | NOT NULL, DEFAULT 0 |
| visibility_roles | JSONB | NOT NULL, DEFAULT '[]' |
| visibility_permissions | JSONB | NOT NULL, DEFAULT '[]' |
| draft_version | INT | NOT NULL, DEFAULT 1 |
| published_version | INT |  |
| etag | VARCHAR(160) | NOT NULL |
| created_by | INT | NOT NULL |
| updated_by | INT |  |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| published_at | TIMESTAMPTZ |  |
| archived_at | TIMESTAMPTZ |  |

## custom_menu_page_versions
| Column | Type | Constraints |
|--------|------|-------------|
| id | BIGINT | PRIMARY KEY, NOT NULL, DEFAULT nextval('custom_menu_page_versions_id_seq') |
| page_key | VARCHAR(80) | NOT NULL |
| version | INT | NOT NULL |
| parent_folder_key | VARCHAR(80) | NOT NULL |
| label | VARCHAR(160) | NOT NULL |
| icon | VARCHAR(80) |  |
| description | TEXT |  |
| route_path | VARCHAR(200) | NOT NULL |
| entity_key | VARCHAR(80) | NOT NULL |
| page_type | VARCHAR(40) | NOT NULL |
| sort_order | INT | NOT NULL |
| visibility_roles | JSONB | NOT NULL, DEFAULT '[]' |
| entity_permission | VARCHAR(80) |  |
| data_permission | VARCHAR(80) |  |
| published_by | INT | NOT NULL |
| published_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

## custom_menu_pages
| Column | Type | Constraints |
|--------|------|-------------|
| id | BIGINT | PRIMARY KEY, NOT NULL, DEFAULT nextval('custom_menu_pages_id_seq') |
| page_key | VARCHAR(80) | NOT NULL |
| parent_folder_key | VARCHAR(80) | NOT NULL |
| label | VARCHAR(160) | NOT NULL |
| icon | VARCHAR(80) |  |
| description | TEXT |  |
| route_path | VARCHAR(200) | NOT NULL |
| entity_key | VARCHAR(80) | NOT NULL |
| page_type | VARCHAR(40) | NOT NULL |
| status | VARCHAR(30) | NOT NULL, DEFAULT 'NeedsConfig' varying |
| sort_order | INT | NOT NULL, DEFAULT 0 |
| visibility_roles | JSONB | NOT NULL, DEFAULT '[]' |
| entity_permission | VARCHAR(80) |  |
| data_permission | VARCHAR(80) |  |
| draft_version | INT | NOT NULL, DEFAULT 1 |
| published_version | INT |  |
| etag | VARCHAR(160) | NOT NULL |
| created_by | INT | NOT NULL |
| updated_by | INT |  |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| published_at | TIMESTAMPTZ |  |
| archived_at | TIMESTAMPTZ |  |

## customers
| Column | Type | Constraints |
|--------|------|-------------|
| id | INT | PRIMARY KEY, NOT NULL, DEFAULT nextval('customers_id_seq') |
| customer_code | VARCHAR(50) | NOT NULL |
| name | VARCHAR(255) | NOT NULL |
| phone | VARCHAR(20) | NOT NULL |
| email | VARCHAR(255) |  |
| address | TEXT |  |
| loyalty_points | INT | NOT NULL, DEFAULT 0 |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'Active' varying |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| deleted_at | TIMESTAMPTZ | (soft delete) |

## financeledger
| Column | Type | Constraints |
|--------|------|-------------|
| id | INT | PRIMARY KEY, NOT NULL, DEFAULT nextval('financeledger_id_seq') |
| transaction_date | DATE | NOT NULL |
| transaction_type | VARCHAR(30) | NOT NULL |
| reference_type | VARCHAR(50) |  |
| reference_id | INT | NOT NULL |
| amount | NUMERIC | NOT NULL |
| description | TEXT |  |
| created_by | INT | FK -> users(id), NOT NULL |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| fund_id | INT | FK -> cash_funds(id), NOT NULL |

## global_table_column_settings
| Column | Type | Constraints |
|--------|------|-------------|
| id | BIGINT | PRIMARY KEY, NOT NULL, DEFAULT nextval('global_table_column_settings_id_seq') |
| table_key | VARCHAR(80) | NOT NULL, UNIQUE |
| hidden_columns | JSONB | NOT NULL, DEFAULT '[]' |
| column_order | JSONB | NOT NULL, DEFAULT '[]' |
| updated_by | BIGINT | FK -> users(id) |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT CURRENT_TIMESTAMP |

## inventory
| Column | Type | Constraints |
|--------|------|-------------|
| id | INT | PRIMARY KEY, NOT NULL, DEFAULT nextval('inventory_id_seq') |
| product_id | INT | FK -> products(id), NOT NULL |
| location_id | INT | FK -> warehouselocations(id), NOT NULL |
| batch_number | VARCHAR(100) |  |
| expiry_date | DATE |  |
| quantity | INT | NOT NULL, DEFAULT 0 |
| min_quantity | INT | NOT NULL, DEFAULT 0 |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| unit_id | INT | FK -> productunits(id) |

## inventory_audit_session_events
| Column | Type | Constraints |
|--------|------|-------------|
| id | INT | PRIMARY KEY, NOT NULL, DEFAULT nextval('inventory_audit_session_events_id_seq') |
| session_id | INT | FK -> inventoryauditsessions(id), NOT NULL |
| event_type | VARCHAR(80) | NOT NULL |
| payload | JSONB |  |
| created_by | INT | FK -> users(id), NOT NULL |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT CURRENT_TIMESTAMP |

## inventoryauditlines
| Column | Type | Constraints |
|--------|------|-------------|
| id | INT | PRIMARY KEY, NOT NULL, DEFAULT nextval('inventoryauditlines_id_seq') |
| session_id | INT | FK -> inventoryauditsessions(id), NOT NULL |
| inventory_id | INT | FK -> inventory(id), NOT NULL |
| system_quantity | NUMERIC | NOT NULL |
| actual_quantity | NUMERIC |  |
| is_counted | BOOLEAN | NOT NULL, DEFAULT false |
| notes | VARCHAR(500) |  |
| variance_applied_at | TIMESTAMP |  |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |

## inventoryauditsessions
| Column | Type | Constraints |
|--------|------|-------------|
| id | INT | PRIMARY KEY, NOT NULL, DEFAULT nextval('inventoryauditsessions_id_seq') |
| audit_code | VARCHAR(50) | NOT NULL, UNIQUE |
| title | VARCHAR(255) | NOT NULL |
| audit_date | DATE | NOT NULL |
| status | VARCHAR(50) | NOT NULL |
| location_filter | VARCHAR(100) |  |
| category_filter | VARCHAR(50) |  |
| notes | TEXT |  |
| created_by | INT | FK -> users(id), NOT NULL |
| completed_at | TIMESTAMP |  |
| completed_by | INT | FK -> users(id) |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| cancel_reason | VARCHAR(1000) |  |
| deleted_at | TIMESTAMPTZ | (soft delete) |
| owner_notes | TEXT |  |

## inventorylogs
| Column | Type | Constraints |
|--------|------|-------------|
| id | INT | PRIMARY KEY, NOT NULL, DEFAULT nextval('inventorylogs_id_seq') |
| product_id | INT | FK -> products(id), NOT NULL |
| action_type | VARCHAR(20) | NOT NULL |
| quantity_change | INT | NOT NULL |
| unit_id | INT | FK -> productunits(id), NOT NULL |
| user_id | INT | FK -> users(id) |
| dispatch_id | INT | FK -> stockdispatches(id) |
| receipt_id | INT | FK -> stockreceipts(id) |
| from_location_id | INT | FK -> warehouselocations(id) |
| to_location_id | INT | FK -> warehouselocations(id) |
| reference_note | VARCHAR(255) |  |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |

## mediaaudits
| Column | Type | Constraints |
|--------|------|-------------|
| id | INT | PRIMARY KEY, NOT NULL, DEFAULT nextval('mediaaudits_id_seq') |
| file_type | VARCHAR(20) | NOT NULL |
| cloud_url | VARCHAR(1000) | NOT NULL |
| entity_type | VARCHAR(50) | NOT NULL |
| entity_id | INT | NOT NULL |
| file_size_bytes | INT |  |
| mime_type | VARCHAR(100) |  |
| uploaded_by | INT | FK -> users(id) |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |

## notifications
| Column | Type | Constraints |
|--------|------|-------------|
| id | INT | PRIMARY KEY, NOT NULL, DEFAULT nextval('notifications_id_seq') |
| user_id | INT | FK -> users(id), NOT NULL |
| notification_type | VARCHAR(30) | NOT NULL |
| title | VARCHAR(255) | NOT NULL |
| message | TEXT | NOT NULL |
| is_read | BOOLEAN | NOT NULL, DEFAULT false |
| reference_type | VARCHAR(50) |  |
| reference_id | INT |  |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| read_at | TIMESTAMP |  |

## orderdetails
| Column | Type | Constraints |
|--------|------|-------------|
| id | INT | PRIMARY KEY, NOT NULL, DEFAULT nextval('orderdetails_id_seq') |
| order_id | INT | FK -> salesorders(id), NOT NULL |
| product_id | INT | FK -> products(id), NOT NULL |
| unit_id | INT | FK -> productunits(id), NOT NULL |
| quantity | INT | NOT NULL |
| price_at_time | NUMERIC | NOT NULL |
| line_total | NUMERIC |  |
| dispatched_qty | INT | NOT NULL, DEFAULT 0 |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |

## partnerdebts
| Column | Type | Constraints |
|--------|------|-------------|
| id | INT | PRIMARY KEY, NOT NULL, DEFAULT nextval('partnerdebts_id_seq') |
| debt_code | VARCHAR(50) | NOT NULL, UNIQUE |
| partner_type | VARCHAR(20) | NOT NULL |
| customer_id | INT | FK -> customers(id) |
| supplier_id | INT | FK -> suppliers(id) |
| total_amount | NUMERIC | NOT NULL |
| paid_amount | NUMERIC | NOT NULL, DEFAULT 0 |
| due_date | DATE |  |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'InDebt' varying |
| notes | TEXT |  |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| created_by | INT | FK -> users(id), NOT NULL |

## productimages
| Column | Type | Constraints |
|--------|------|-------------|
| id | INT | PRIMARY KEY, NOT NULL, DEFAULT nextval('productimages_id_seq') |
| product_id | INT | FK -> products(id), NOT NULL |
| image_url | VARCHAR(500) | NOT NULL |
| alt_text | VARCHAR(255) |  |
| is_primary | BOOLEAN | NOT NULL, DEFAULT false |
| sort_order | INT | NOT NULL, DEFAULT 0 |
| file_size_bytes | INT |  |
| mime_type | VARCHAR(100) |  |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |

## productpricehistory
| Column | Type | Constraints |
|--------|------|-------------|
| id | INT | PRIMARY KEY, NOT NULL, DEFAULT nextval('productpricehistory_id_seq') |
| product_id | INT | FK -> products(id), NOT NULL |
| unit_id | INT | FK -> productunits(id), NOT NULL |
| cost_price | NUMERIC | NOT NULL |
| sale_price | NUMERIC | NOT NULL |
| effective_date | DATE | NOT NULL |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |

## products
| Column | Type | Constraints |
|--------|------|-------------|
| id | INT | PRIMARY KEY, NOT NULL, DEFAULT nextval('products_id_seq') |
| category_id | INT | FK -> categories(id) |
| sku_code | VARCHAR(50) | NOT NULL, UNIQUE |
| barcode | VARCHAR(100) |  |
| name | VARCHAR(255) | NOT NULL |
| image_url | VARCHAR(500) |  |
| description | TEXT |  |
| weight | NUMERIC |  |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'Active' varying |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |

## productunits
| Column | Type | Constraints |
|--------|------|-------------|
| id | INT | PRIMARY KEY, NOT NULL, DEFAULT nextval('productunits_id_seq') |
| product_id | INT | FK -> products(id), NOT NULL |
| unit_name | VARCHAR(50) | NOT NULL |
| conversion_rate | NUMERIC | NOT NULL |
| is_base_unit | BOOLEAN | NOT NULL, DEFAULT false |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |

## refresh_tokens
| Column | Type | Constraints |
|--------|------|-------------|
| id | INT | PRIMARY KEY, NOT NULL, DEFAULT nextval('refresh_tokens_id_seq') |
| user_id | INT | FK -> users(id), NOT NULL |
| token | VARCHAR(64) | NOT NULL, UNIQUE |
| expires_at | TIMESTAMP | NOT NULL |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| delete_ymd | TIMESTAMPTZ |  |

## roles
| Column | Type | Constraints |
|--------|------|-------------|
| id | INT | PRIMARY KEY, NOT NULL, DEFAULT nextval('roles_id_seq') |
| name | VARCHAR(50) | NOT NULL, UNIQUE |
| permissions | JSONB | NOT NULL, DEFAULT '{}' |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |

## salesorders
| Column | Type | Constraints |
|--------|------|-------------|
| id | INT | PRIMARY KEY, NOT NULL, DEFAULT nextval('salesorders_id_seq') |
| order_code | VARCHAR(50) | NOT NULL, UNIQUE |
| customer_id | INT | FK -> customers(id), NOT NULL |
| user_id | INT | FK -> users(id), NOT NULL |
| total_amount | NUMERIC | NOT NULL, DEFAULT 0 |
| discount_amount | NUMERIC | NOT NULL, DEFAULT 0 |
| final_amount | NUMERIC |  |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'Pending' varying |
| parent_order_id | INT | FK -> salesorders(id) |
| shipping_address | TEXT |  |
| notes | TEXT |  |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| cancelled_at | TIMESTAMP |  |
| cancelled_by | INT | FK -> users(id) |
| order_channel | VARCHAR(20) | NOT NULL, DEFAULT 'Wholesale' varying |
| payment_status | VARCHAR(20) | NOT NULL, DEFAULT 'Unpaid' varying |
| ref_sales_order_id | INT | FK -> salesorders(id) |
| voucher_id | INT | FK -> vouchers(id) |
| pos_shift_ref | VARCHAR(100) |  |

## staffpasswordresetrequests
| Column | Type | Constraints |
|--------|------|-------------|
| id | INT | PRIMARY KEY, NOT NULL, DEFAULT nextval('staffpasswordresetrequests_id_seq') |
| user_id | INT | FK -> users(id), NOT NULL |
| message | TEXT |  |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'Pending' varying |
| processed_by | INT | FK -> users(id) |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| processed_at | TIMESTAMP |  |

## stockdispatch_lines
| Column | Type | Constraints |
|--------|------|-------------|
| id | BIGINT | PRIMARY KEY, NOT NULL, DEFAULT nextval('stockdispatch_lines_id_seq') |
| dispatch_id | INT | FK -> stockdispatches(id), NOT NULL |
| inventory_id | INT | FK -> inventory(id), NOT NULL |
| quantity | INT | NOT NULL |
| unit_price_snapshot | NUMERIC |  |

## stockdispatches
| Column | Type | Constraints |
|--------|------|-------------|
| id | INT | PRIMARY KEY, NOT NULL, DEFAULT nextval('stockdispatches_id_seq') |
| dispatch_code | VARCHAR(50) | NOT NULL, UNIQUE |
| order_id | INT | FK -> salesorders(id) |
| user_id | INT | FK -> users(id), NOT NULL |
| dispatch_date | DATE | NOT NULL |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'Pending' varying |
| notes | TEXT |  |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| reference_label | VARCHAR(255) |  |
| deleted_at | TIMESTAMPTZ | (soft delete) |
| deleted_by_user_id | INT | FK -> users(id) |
| delete_reason | TEXT |  |

## stockreceiptdetails
| Column | Type | Constraints |
|--------|------|-------------|
| id | INT | PRIMARY KEY, NOT NULL, DEFAULT nextval('stockreceiptdetails_id_seq') |
| receipt_id | INT | FK -> stockreceipts(id), NOT NULL |
| product_id | INT | FK -> products(id), NOT NULL |
| unit_id | INT | FK -> productunits(id), NOT NULL |
| quantity | INT | NOT NULL |
| cost_price | NUMERIC | NOT NULL |
| batch_number | VARCHAR(100) |  |
| expiry_date | DATE |  |
| line_total | NUMERIC |  |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |

## stockreceipts
| Column | Type | Constraints |
|--------|------|-------------|
| id | INT | PRIMARY KEY, NOT NULL, DEFAULT nextval('stockreceipts_id_seq') |
| receipt_code | VARCHAR(50) | NOT NULL, UNIQUE |
| supplier_id | INT | FK -> suppliers(id), NOT NULL |
| staff_id | INT | FK -> users(id), NOT NULL |
| receipt_date | DATE | NOT NULL |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'Draft' varying |
| invoice_number | VARCHAR(100) |  |
| total_amount | NUMERIC | NOT NULL, DEFAULT 0 |
| notes | TEXT |  |
| approved_by | INT | FK -> users(id) |
| approved_at | TIMESTAMP |  |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| rejection_reason | TEXT |  |
| reviewed_at | TIMESTAMP |  |
| reviewed_by | INT | FK -> users(id) |

## storeprofiles
| Column | Type | Constraints |
|--------|------|-------------|
| id | INT | PRIMARY KEY, NOT NULL, DEFAULT nextval('storeprofiles_id_seq') |
| owner_id | INT | FK -> users(id), NOT NULL, UNIQUE |
| name | VARCHAR(255) | NOT NULL |
| business_category | VARCHAR(255) |  |
| address | TEXT |  |
| phone | VARCHAR(30) |  |
| email | VARCHAR(255) |  |
| website | VARCHAR(500) |  |
| tax_code | VARCHAR(50) |  |
| footer_note | TEXT |  |
| logo_url | VARCHAR(500) |  |
| facebook_url | VARCHAR(500) |  |
| instagram_handle | VARCHAR(255) |  |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| default_retail_location_id | INT | FK -> warehouselocations(id) |

## suppliers
| Column | Type | Constraints |
|--------|------|-------------|
| id | INT | PRIMARY KEY, NOT NULL, DEFAULT nextval('suppliers_id_seq') |
| supplier_code | VARCHAR(50) | NOT NULL, UNIQUE |
| name | VARCHAR(255) | NOT NULL |
| contact_person | VARCHAR(255) |  |
| phone | VARCHAR(20) |  |
| email | VARCHAR(255) |  |
| address | TEXT |  |
| tax_code | VARCHAR(50) |  |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'Active' varying |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |

## systemlogs
| Column | Type | Constraints |
|--------|------|-------------|
| id | INT | PRIMARY KEY, NOT NULL, DEFAULT nextval('systemlogs_id_seq') |
| log_level | VARCHAR(20) | NOT NULL |
| module | VARCHAR(100) | NOT NULL |
| action | VARCHAR(255) | NOT NULL |
| user_id | INT | FK -> users(id) |
| message | TEXT | NOT NULL |
| stack_trace | TEXT |  |
| context_data | JSONB |  |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |

## user_table_column_settings
| Column | Type | Constraints |
|--------|------|-------------|
| id | BIGINT | PRIMARY KEY, NOT NULL, DEFAULT nextval('user_table_column_settings_id_seq') |
| user_id | BIGINT | FK -> users(id), NOT NULL |
| table_key | VARCHAR(80) | NOT NULL |
| hidden_columns | JSONB | NOT NULL, DEFAULT '[]' |
| column_order | JSONB | NOT NULL, DEFAULT '[]' |
| updated_by | BIGINT | FK -> users(id) |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT CURRENT_TIMESTAMP |

## users
| Column | Type | Constraints |
|--------|------|-------------|
| id | INT | PRIMARY KEY, NOT NULL, DEFAULT nextval('users_id_seq') |
| username | VARCHAR(100) | NOT NULL, UNIQUE |
| password_hash | VARCHAR(255) | NOT NULL |
| full_name | VARCHAR(255) | NOT NULL |
| email | VARCHAR(255) | NOT NULL, UNIQUE |
| phone | VARCHAR(20) |  |
| role_id | INT | FK -> roles(id), NOT NULL |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'Active' varying |
| last_login | TIMESTAMP |  |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| staff_code | VARCHAR(50) |  |

## voucher_redemptions
| Column | Type | Constraints |
|--------|------|-------------|
| id | INT | PRIMARY KEY, NOT NULL, DEFAULT nextval('voucher_redemptions_id_seq') |
| voucher_id | INT | FK -> vouchers(id), NOT NULL |
| sales_order_id | INT | FK -> salesorders(id), NOT NULL, UNIQUE |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |

## vouchers
| Column | Type | Constraints |
|--------|------|-------------|
| id | INT | PRIMARY KEY, NOT NULL, DEFAULT nextval('vouchers_id_seq') |
| code | VARCHAR(50) | NOT NULL, UNIQUE |
| name | VARCHAR(255) |  |
| discount_type | VARCHAR(20) | NOT NULL |
| discount_value | NUMERIC | NOT NULL |
| is_active | BOOLEAN | NOT NULL, DEFAULT true |
| valid_from | DATE |  |
| valid_to | DATE |  |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| used_count | INT | NOT NULL, DEFAULT 0 |
| max_uses | INT |  |

## warehouselocations
| Column | Type | Constraints |
|--------|------|-------------|
| id | INT | PRIMARY KEY, NOT NULL, DEFAULT nextval('warehouselocations_id_seq') |
| warehouse_code | VARCHAR(20) | NOT NULL |
| shelf_code | VARCHAR(20) | NOT NULL |
| description | VARCHAR(255) |  |
| capacity | NUMERIC |  |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'Active' varying |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
