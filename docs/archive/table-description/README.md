# docs/table-description

Consolidated database schema reference for AI context. Generated from Flyway migrations V1–V52.

## Files

| File | Content |
|------|---------|
| `core_tables.md` | All tables with columns, types, constraints, and soft-delete markers |
| `indexes.md` | All indexes including unique, partial, and composite indexes |
| `foreign_keys.md` | All foreign key relationships |

## Summary

- **Total tables**: 30
- **Soft-deleted tables**: categories, customers, stockdispatches, inventoryauditsessions
- **AI draft tables**: ai_catalog_draft, ai_inventory_draft (HITL pattern)
- **AI registry tables**: aitabledescription, aicolumndescription
- **Finance fact table**: financeledger (canonical source for revenue/expense)
- **Multi-tenant**: All tables include `tenant_id` (default '1')
