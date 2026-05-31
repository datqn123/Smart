# Indexes

| Table | Index Name | Columns | Notes |
|-------|-----------|---------|-------|
| users | ix_users_email | email | UNIQUE |
| users | ix_users_username | username | UNIQUE |
| user_roles | ix_user_roles_user_id | user_id | |
| user_roles | ix_user_roles_role_id | role_id | |
| categories | ix_categories_tenant | tenant_id | |
| categories | ix_categories_parent | parent_id | WHERE deleted_at IS NULL |
| products | ix_products_tenant | tenant_id | |
| products | ix_products_category | category_id | |
| products | ix_products_code | code | UNIQUE |
| inventory | ix_inventory_tenant_product | tenant_id, product_id | UNIQUE |
| suppliers | ix_suppliers_tenant | tenant_id | |
| suppliers | ix_suppliers_code | code | UNIQUE |
| customers | ix_customers_tenant | tenant_id | |
| customers | ix_customers_code | code | UNIQUE |
| stockreceipts | ix_stockreceipts_tenant | tenant_id | |
| stockreceipts | ix_stockreceipts_code | code | UNIQUE |
| stockreceipts | ix_stockreceipts_supplier | supplier_id | |
| stockreceipts | ix_stockreceipts_date | receipt_date | |
| stockreceiptdetails | ix_stockreceiptdetails_receipt | receipt_id | |
| stockreceiptdetails | ix_stockreceiptdetails_product | product_id | |
| stockdispatches | ix_stockdispatches_tenant | tenant_id | WHERE deleted_at IS NULL |
| stockdispatches | ix_stockdispatches_code | code | UNIQUE WHERE deleted_at IS NULL |
| stockdispatches | ix_stockdispatches_customer | customer_id | WHERE deleted_at IS NULL |
| stockdispatches | ix_stockdispatches_date | dispatch_date | WHERE deleted_at IS NULL |
| stockdispatchdetails | ix_stockdispatchdetails_dispatch | dispatch_id | |
| stockdispatchdetails | ix_stockdispatchdetails_product | product_id | |
| inventoryauditsessions | ix_inventoryaudits_tenant | tenant_id | WHERE deleted_at IS NULL |
| inventoryauditsessions | ix_inventoryaudits_code | code | UNIQUE WHERE deleted_at IS NULL |
| inventoryauditsessions | ix_inventoryaudits_date | audit_date | WHERE deleted_at IS NULL |
| inventoryauditdetails | ix_inventoryauditdetails_session | session_id | |
| inventoryauditdetails | ix_inventoryauditdetails_product | product_id | |
| salesorders | ix_salesorders_tenant | tenant_id | |
| salesorders | ix_salesorders_code | code | UNIQUE |
| salesorders | ix_salesorders_customer | customer_id | |
| salesorders | ix_salesorders_date | order_date | |
| salesorderdetails | ix_salesorderdetails_order | order_id | |
| salesorderdetails | ix_salesorderdetails_product | product_id | |
| purchaseorders | ix_purchaseorders_tenant | tenant_id | |
| purchaseorders | ix_purchaseorders_code | code | UNIQUE |
| purchaseorders | ix_purchaseorders_supplier | supplier_id | |
| purchaseorders | ix_purchaseorders_date | order_date | |
| purchaseorderdetails | ix_purchaseorderdetails_order | order_id | |
| purchaseorderdetails | ix_purchaseorderdetails_product | product_id | |
| financeledger | ix_financeledger_tenant_date | tenant_id, entry_date | |
| financeledger | ix_financeledger_type | type | |
| financeledger | ix_financeledger_category | category | |
| financeledger | ix_financeledger_reference | reference_type, reference_id | |
| aitabledescription | ix_aitabledescription_table | table_name | UNIQUE |
| aicolumndescription | ix_aicolumndescription_table_column | table_name, column_name | UNIQUE |
| notifications | ix_notifications_user_unread | user_id, is_read | WHERE is_read = false |
| notifications | ix_notifications_user_created | user_id, created_at DESC | |
| approvalworkflows | ix_approvalworkflows_entity | entity_type | |
| approvalsteps | ix_approvalsteps_workflow | workflow_id | |
| approvalrequests | ix_approvalrequests_workflow | workflow_id | |
| approvalrequests | ix_approvalrequests_entity | entity_type, entity_id | |
| approvalrequests | ix_approvalrequests_status | status | |
| approvalactions | ix_approvalactions_request | request_id | |
| approvalactions | ix_approvalactions_approver | approver_id | |
| ai_catalog_draft | ix_ai_catalog_draft_user_created | user_id, created_at DESC | |
| ai_catalog_draft | ix_ai_catalog_draft_expires | expires_at | WHERE status = 'draft' |
| ai_inventory_draft | ix_ai_inventory_draft_user_created | user_id, created_at DESC | |
| ai_inventory_draft | ix_ai_inventory_draft_expires | expires_at | WHERE status = 'draft' |
