# CatalogDraftTool

> Source: `ai_python/app/graph/tools/catalog_draft.py`
> Prompts: catalog_draft.md, catalog_draft_product.md, catalog_draft_category.md, catalog_draft_supplier.md, catalog_draft_customer.md, catalog_draft_slots.md, catalog_entity_pick.md

## Overview
Creates catalog entity drafts (products, categories, suppliers, customers) with human-in-the-loop confirmation. Two-phase workflow: draft generation followed by human review and commit.

## Manifest (ToolRegistry)
| Field | Value |
|-------|-------|
| name | `catalog_draft` |
| capability | `draft_create` |
| side_effect_class | `non_idempotent_write` |
| has_hitl | `true` |
| risk_level | `high` |
| produces | `("input_table_draft",)` |
| consumes | — |
| result_ref_policy | — |
| output_artifact_types | `("input_table_draft",)` |
| rbac_required | `("draft_create",)` |
| examples | — |

## Input Schema
```json
{
  "request": "string"
}
```

## Output / Observation
**Draft phase:**
```json
{
  "catalog_draft_sse": {
    "draft_id": "abc123",
    "entity_type": "product",
    "data": {...}
  }
}
```
Observation: `"Catalog draft ready; awaiting user confirmation."`

**Commit phase (after HITL confirmation):**
```json
{
  "draft_id": "abc123",
  "commit_result": {
    "ok": true,
    "entity_id": "PROD-001"
  }
}
```

## Runtime Integration

### Harness (v3.0)
- Called by: `PlanExecutor` via `ToolRegistry`
- Node type in PlanGraph: `tool`
- Two-phase HITL: draft generation → human confirmation
- HitlSpec: `event_name="draft"`
- Resume via `_confirm()` with `commit_catalog_draft`

### LangGraph (Legacy)
- Subgraph: `catalog_draft_subgraph`
- Nodes: `classify_catalog_entity`, `resolve_catalog_draft`, `generate_catalog_draft`, `persist_catalog_draft`

## Error Handling
- **HITL_DRAFT_MISSING**: Raised if no draft found when attempting commit
- **Commit failure**: Caught and reported in `commit_result`
- **failedCount**: Determines ok status in HITL flow

## Example
**Input:**
```json
{
  "request": "Create a new product 'Laptop Pro 15' with price 25000000 VND"
}
```
**Output (draft phase):**
```json
{
  "catalog_draft_sse": {
    "draft_id": "draft_abc123",
    "entity_type": "product",
    "data": {
      "product_name": "Laptop Pro 15",
      "price": 25000000,
      "currency": "VND"
    }
  }
}
```
Observation: `"Catalog draft ready; awaiting user confirmation."`
