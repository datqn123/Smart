# Core Tables

## users
| Column | Type | Constraints |
|--------|------|-------------|
| id | VARCHAR(64) | PRIMARY KEY |
| tenant_id | VARCHAR(32) | NOT NULL DEFAULT '1' |
| username | VARCHAR(100) | UNIQUE, NOT NULL |
| email | VARCHAR(255) | UNIQUE, NOT NULL |
| password_hash | VARCHAR(255) | NOT NULL |
| full_name | VARCHAR(255) | NOT NULL |
| phone | VARCHAR(20) | |
| avatar_url | TEXT | |
| status | VARCHAR(20) | NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'locked')) |
| failed_login_attempts | INT | NOT NULL DEFAULT 0 |
| locked_until | TIMESTAMPTZ | |
| last_login_at | TIMESTAMPTZ | |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() |
| updated_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() |

## roles
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY DEFAULT gen_random_uuid() |
| tenant_id | VARCHAR(32) | NOT NULL DEFAULT '1' |
| name | VARCHAR(100) | NOT NULL |
| description | TEXT | |
| permissions | JSONB | NOT NULL DEFAULT '[]' |
| is_system | BOOLEAN | NOT NULL DEFAULT false |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() |
| updated_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() |

## user_roles
| Column | Type | Constraints |
|--------|------|-------------|
| user_id | VARCHAR(64) | FK -> users.id, PK |
| role_id | UUID | FK -> roles.id, PK |

## categories
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY DEFAULT gen_random_uuid() |
| tenant_id | VARCHAR(32) | NOT NULL DEFAULT '1' |
| name | VARCHAR(255) | NOT NULL |
| description | TEXT | |
| parent_id | UUID | FK -> categories.id |
| sort_order | INT | NOT NULL DEFAULT 0 |
| deleted_at | TIMESTAMPTZ | (soft delete) |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() |
| updated_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() |

## suppliers
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY DEFAULT gen_random_uuid() |
| tenant_id | VARCHAR(32) | NOT NULL DEFAULT '1' |
| code | VARCHAR(50) | UNIQUE, NOT NULL |
| name | VARCHAR(255) | NOT NULL |
| contact_person | VARCHAR(255) | |
| phone | VARCHAR(20) | |
| email | VARCHAR(255) | |
| address | TEXT | |
| tax_code | VARCHAR(50) | |
| payment_terms | VARCHAR(100) | |
| status | VARCHAR(20) | NOT NULL DEFAULT 'active' |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() |
| updated_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() |

## customers
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY DEFAULT gen_random_uuid() |
| tenant_id | VARCHAR(32) | NOT NULL DEFAULT '1' |
| code | VARCHAR(50) | UNIQUE, NOT NULL |
| name | VARCHAR(255) | NOT NULL |
| contact_person | VARCHAR(255) | |
| phone | VARCHAR(20) | |
| email | VARCHAR(255) | |
| address | TEXT | |
| tax_code | VARCHAR(50) | |
| credit_limit | DECIMAL(15,2) | DEFAULT 0 |
| payment_terms | VARCHAR(100) | |
| status | VARCHAR(20) | NOT NULL DEFAULT 'active' |
| deleted_at | TIMESTAMPTZ | (soft delete) |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() |
| updated_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() |

## products
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY DEFAULT gen_random_uuid() |
| tenant_id | VARCHAR(32) | NOT NULL DEFAULT '1' |
| category_id | UUID | FK -> categories.id |
| code | VARCHAR(50) | UNIQUE, NOT NULL |
| name | VARCHAR(255) | NOT NULL |
| description | TEXT | |
| unit | VARCHAR(50) | NOT NULL |
| cost_price | DECIMAL(15,2) | DEFAULT 0 |
| selling_price | DECIMAL(15,2) | DEFAULT 0 |
| min_stock | DECIMAL(15,2) | DEFAULT 0 |
| max_stock | DECIMAL(15,2) | |
| status | VARCHAR(20) | NOT NULL DEFAULT 'active' |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() |
| updated_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() |

## inventory
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY DEFAULT gen_random_uuid() |
| tenant_id | VARCHAR(32) | NOT NULL DEFAULT '1' |
| product_id | UUID | FK -> products.id |
| quantity | DECIMAL(15,2) | NOT NULL DEFAULT 0 |
| reserved_quantity | DECIMAL(15,2) | NOT NULL DEFAULT 0 |
| updated_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() |

## stockreceipts
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY DEFAULT gen_random_uuid() |
| tenant_id | VARCHAR(32) | NOT NULL DEFAULT '1' |
| code | VARCHAR(50) | UNIQUE, NOT NULL |
| supplier_id | UUID | FK -> suppliers.id |
| receipt_date | DATE | NOT NULL |
| total_amount | DECIMAL(15,2) | NOT NULL DEFAULT 0 |
| status | VARCHAR(20) | NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'confirmed', 'cancelled')) |
| notes | TEXT | |
| created_by | VARCHAR(64) | FK -> users.id |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() |
| updated_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() |

## stockreceiptdetails
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY DEFAULT gen_random_uuid() |
| receipt_id | UUID | FK -> stockreceipts.id |
| product_id | UUID | FK -> products.id |
| quantity | DECIMAL(15,2) | NOT NULL |
| unit_price | DECIMAL(15,2) | NOT NULL |
| total_price | DECIMAL(15,2) | NOT NULL |
| notes | TEXT | |

## stockdispatches
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY DEFAULT gen_random_uuid() |
| tenant_id | VARCHAR(32) | NOT NULL DEFAULT '1' |
| code | VARCHAR(50) | UNIQUE, NOT NULL |
| customer_id | UUID | FK -> customers.id |
| dispatch_date | DATE | NOT NULL |
| total_amount | DECIMAL(15,2) | NOT NULL DEFAULT 0 |
| status | VARCHAR(20) | NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'confirmed', 'cancelled')) |
| notes | TEXT | |
| deleted_at | TIMESTAMPTZ | (soft delete) |
| created_by | VARCHAR(64) | FK -> users.id |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() |
| updated_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() |

## stockdispatchdetails
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY DEFAULT gen_random_uuid() |
| dispatch_id | UUID | FK -> stockdispatches.id |
| product_id | UUID | FK -> products.id |
| quantity | DECIMAL(15,2) | NOT NULL |
| unit_price | DECIMAL(15,2) | NOT NULL |
| total_price | DECIMAL(15,2) | NOT NULL |
| notes | TEXT | |

## inventoryauditsessions
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY DEFAULT gen_random_uuid() |
| tenant_id | VARCHAR(32) | NOT NULL DEFAULT '1' |
| code | VARCHAR(50) | UNIQUE, NOT NULL |
| audit_date | DATE | NOT NULL |
| status | VARCHAR(20) | NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'in_progress', 'completed', 'cancelled')) |
| notes | TEXT | |
| deleted_at | TIMESTAMPTZ | (soft delete) |
| created_by | VARCHAR(64) | FK -> users.id |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() |
| updated_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() |

## inventoryauditdetails
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY DEFAULT gen_random_uuid() |
| session_id | UUID | FK -> inventoryauditsessions.id |
| product_id | UUID | FK -> products.id |
| system_quantity | DECIMAL(15,2) | NOT NULL |
| actual_quantity | DECIMAL(15,2) | |
| difference | DECIMAL(15,2) | |
| notes | TEXT | |

## salesorders
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY DEFAULT gen_random_uuid() |
| tenant_id | VARCHAR(32) | NOT NULL DEFAULT '1' |
| code | VARCHAR(50) | UNIQUE, NOT NULL |
| customer_id | UUID | FK -> customers.id |
| order_date | DATE | NOT NULL |
| total_amount | DECIMAL(15,2) | NOT NULL DEFAULT 0 |
| status | VARCHAR(20) | NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'confirmed', 'completed', 'cancelled')) |
| notes | TEXT | |
| created_by | VARCHAR(64) | FK -> users.id |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() |
| updated_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() |

## salesorderdetails
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY DEFAULT gen_random_uuid() |
| order_id | UUID | FK -> salesorders.id |
| product_id | UUID | FK -> products.id |
| quantity | DECIMAL(15,2) | NOT NULL |
| unit_price | DECIMAL(15,2) | NOT NULL |
| total_price | DECIMAL(15,2) | NOT NULL |
| notes | TEXT | |

## purchaseorders
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY DEFAULT gen_random_uuid() |
| tenant_id | VARCHAR(32) | NOT NULL DEFAULT '1' |
| code | VARCHAR(50) | UNIQUE, NOT NULL |
| supplier_id | UUID | FK -> suppliers.id |
| order_date | DATE | NOT NULL |
| total_amount | DECIMAL(15,2) | NOT NULL DEFAULT 0 |
| status | VARCHAR(20) | NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'confirmed', 'completed', 'cancelled')) |
| notes | TEXT | |
| created_by | VARCHAR(64) | FK -> users.id |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() |
| updated_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() |

## purchaseorderdetails
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY DEFAULT gen_random_uuid() |
| order_id | UUID | FK -> purchaseorders.id |
| product_id | UUID | FK -> products.id |
| quantity | DECIMAL(15,2) | NOT NULL |
| unit_price | DECIMAL(15,2) | NOT NULL |
| total_price | DECIMAL(15,2) | NOT NULL |
| notes | TEXT | |

## financeledger
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY DEFAULT gen_random_uuid() |
| tenant_id | VARCHAR(32) | NOT NULL DEFAULT '1' |
| entry_date | DATE | NOT NULL |
| type | VARCHAR(20) | NOT NULL CHECK (type IN ('revenue', 'expense')) |
| category | VARCHAR(100) | NOT NULL |
| amount | DECIMAL(15,2) | NOT NULL |
| description | TEXT | |
| reference_type | VARCHAR(50) | |
| reference_id | UUID | |
| created_by | VARCHAR(64) | FK -> users.id |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() |

## aitabledescription
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY DEFAULT gen_random_uuid() |
| tenant_id | VARCHAR(32) | NOT NULL DEFAULT '1' |
| table_name | VARCHAR(100) | NOT NULL |
| description | TEXT | NOT NULL |
| business_context | TEXT | |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() |
| updated_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() |

## aicolumndescription
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY DEFAULT gen_random_uuid() |
| tenant_id | VARCHAR(32) | NOT NULL DEFAULT '1' |
| table_name | VARCHAR(100) | NOT NULL |
| column_name | VARCHAR(100) | NOT NULL |
| description | TEXT | NOT NULL |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() |
| updated_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() |

## notifications
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY DEFAULT gen_random_uuid() |
| tenant_id | VARCHAR(32) | NOT NULL DEFAULT '1' |
| user_id | VARCHAR(64) | FK -> users.id |
| type | VARCHAR(50) | NOT NULL |
| title | VARCHAR(255) | NOT NULL |
| message | TEXT | NOT NULL |
| is_read | BOOLEAN | NOT NULL DEFAULT false |
| metadata | JSONB | |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() |

## approvalworkflows
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY DEFAULT gen_random_uuid() |
| tenant_id | VARCHAR(32) | NOT NULL DEFAULT '1' |
| name | VARCHAR(255) | NOT NULL |
| entity_type | VARCHAR(50) | NOT NULL |
| threshold_amount | DECIMAL(15,2) | |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() |
| updated_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() |

## approvalsteps
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY DEFAULT gen_random_uuid() |
| workflow_id | UUID | FK -> approvalworkflows.id |
| step_order | INT | NOT NULL |
| approver_role_id | UUID | FK -> roles.id |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() |

## approvalrequests
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY DEFAULT gen_random_uuid() |
| tenant_id | VARCHAR(32) | NOT NULL DEFAULT '1' |
| workflow_id | UUID | FK -> approvalworkflows.id |
| entity_type | VARCHAR(50) | NOT NULL |
| entity_id | UUID | NOT NULL |
| status | VARCHAR(20) | NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'cancelled')) |
| requested_by | VARCHAR(64) | FK -> users.id |
| requested_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() |
| completed_at | TIMESTAMPTZ | |

## approvalactions
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY DEFAULT gen_random_uuid() |
| request_id | UUID | FK -> approvalrequests.id |
| step_id | UUID | FK -> approvalsteps.id |
| approver_id | VARCHAR(64) | FK -> users.id |
| action | VARCHAR(20) | NOT NULL CHECK (action IN ('approved', 'rejected')) |
| comment | TEXT | |
| acted_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() |

## ai_catalog_draft
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY DEFAULT gen_random_uuid() |
| user_id | VARCHAR(64) | NOT NULL |
| tenant_id | VARCHAR(32) | NOT NULL DEFAULT '1' |
| conversation_id | VARCHAR(128) | |
| entity_type | VARCHAR(32) | NOT NULL CHECK (entity_type IN ('product', 'category', 'supplier', 'customer')) |
| status | VARCHAR(20) | NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'committed', 'expired')) |
| payload | JSONB | NOT NULL |
| commit_result | JSONB | |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() |
| updated_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() |
| expires_at | TIMESTAMPTZ | NOT NULL |

## ai_inventory_draft
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY DEFAULT gen_random_uuid() |
| user_id | VARCHAR(64) | NOT NULL |
| tenant_id | VARCHAR(32) | NOT NULL DEFAULT '1' |
| conversation_id | VARCHAR(128) | |
| entity_type | VARCHAR(32) | NOT NULL CHECK (entity_type IN ('stock_receipt')) |
| status | VARCHAR(20) | NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'committed', 'expired')) |
| payload | JSONB | NOT NULL |
| commit_result | JSONB | |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() |
| updated_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() |
| expires_at | TIMESTAMPTZ | NOT NULL |
