# InventoryDraftTool

> Source: `ai_python/app/graph/tools/inventory_draft.py`
> Prompts: inventory_draft.md, inventory_draft_stock_receipt.md, inventory_draft_stock_dispatch.md, inventory_draft_slots.md, inventory_entity_pick.md

## Overview
Creates inventory document drafts (stock receipts, stock dispatches) with human-in-the-loop confirmation. Two-phase workflow: draft generation followed by human review and commit.

## Manifest (ToolRegistry)
| Field | Value |
|-------|-------|
| name | `inventory_draft` |
| capability | `draft_create` |
| side_effect_class | `non_idempotent_write` |
| has_hitl | `true` |
| risk_level | `high` |
| produces | `("inventory_draft",)` |
| consumes | — |
| result_ref_policy | — |
| output_artifact_types | `("inventory_draft",)` |
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
  "inventory_draft_sse": {
    "draft_id": "inv_abc123",
    "doc_type": "stock_receipt",
    "data": {...}
  }
}
```
Observation: `"Inventory draft ready; awaiting user confirmation."`

**Commit phase (after HITL confirmation):**
```json
{
  "draft_id": "inv_abc123",
  "commit_result": {
    "ok": true,
    "doc_id": "SR-2026-001"
  }
}
```

## Runtime Integration

### Harness (v3.0)
- Called by: `PlanExecutor` via `ToolRegistry`
- Node type in PlanGraph: `tool`
- Two-phase HITL: draft generation → human confirmation
- HitlSpec: `event_name="inventory_draft"`
- Resume via `_confirm()` with `commit_inventory_draft`

### LangGraph (Legacy)
- Subgraph: `inventory_draft_subgraph`
- Nodes: `classify_inventory_doc`, `resolve_inventory_draft`, `generate_inventory_draft`, `persist_inventory_draft`

## Error Handling
- **HITL_DRAFT_MISSING**: Raised if no draft found when attempting commit
- **Commit failure**: Caught; uses `committed.get("ok", True)` to determine status

## Example
**Input:**
```json
{
  "request": "Create stock receipt for 50 units of 'Laptop Pro 15' from supplier ABC"
}
```
**Output (draft phase):**
```json
{
  "inventory_draft_sse": {
    "draft_id": "draft_inv_001",
    "doc_type": "stock_receipt",
    "data": {
      "supplier": "ABC",
      "items": [
        {"product": "Laptop Pro 15", "quantity": 50}
      ]
    }
  }
}
```
Observation: `"Inventory draft ready; awaiting user confirmation."`
