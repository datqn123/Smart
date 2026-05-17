# Foreign Keys

| Table | Column | References |
|-------|--------|------------|
| user_roles | user_id | users(id) |
| user_roles | role_id | roles(id) |
| categories | parent_id | categories(id) |
| products | category_id | categories(id) |
| inventory | product_id | products(id) |
| stockreceipts | supplier_id | suppliers(id) |
| stockreceipts | created_by | users(id) |
| stockreceiptdetails | receipt_id | stockreceipts(id) |
| stockreceiptdetails | product_id | products(id) |
| stockdispatches | customer_id | customers(id) |
| stockdispatches | created_by | users(id) |
| stockdispatchdetails | dispatch_id | stockdispatches(id) |
| stockdispatchdetails | product_id | products(id) |
| inventoryauditsessions | created_by | users(id) |
| inventoryauditdetails | session_id | inventoryauditsessions(id) |
| inventoryauditdetails | product_id | products(id) |
| salesorders | customer_id | customers(id) |
| salesorders | created_by | users(id) |
| salesorderdetails | order_id | salesorders(id) |
| salesorderdetails | product_id | products(id) |
| purchaseorders | supplier_id | suppliers(id) |
| purchaseorders | created_by | users(id) |
| purchaseorderdetails | order_id | purchaseorders(id) |
| purchaseorderdetails | product_id | products(id) |
| financeledger | created_by | users(id) |
| notifications | user_id | users(id) |
| approvalsteps | workflow_id | approvalworkflows(id) |
| approvalsteps | approver_role_id | roles(id) |
| approvalrequests | workflow_id | approvalworkflows(id) |
| approvalrequests | requested_by | users(id) |
| approvalactions | request_id | approvalrequests(id) |
| approvalactions | step_id | approvalsteps(id) |
| approvalactions | approver_id | users(id) |
