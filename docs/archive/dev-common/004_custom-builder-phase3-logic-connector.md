# SRS - Phase 3 Logic Connector / Formula Builder

> File: `docs/dev/common/004_custom-builder-phase3-logic-connector.md`  
> Agent: SRS_WRITER  
> Ngay cap nhat: 02/06/2026  
> Trang thai: DRAFT_FOR_PO_REVIEW  
> Pham vi: Visual connector/formula builder, no direct inventory mutation.

---

## 1. Objective

User can connect screens/workflows with safe structured logic:

- When an order is confirmed, prepare inventory decrease effects.
- When a receipt is approved, prepare inventory increase effects.
- Copy/set/calculate simple fields.
- Sum line item values.

Connector is visual in UI but stored as structured JSON rule. Backend does not trust canvas state.

---

## 2. Data Model

| Bang | Vai tro |
| :--- | :--- |
| `custom_logic_connectors` | Connector metadata: trigger/source/operation/target |
| `custom_connector_events` | Dry-run/publish/execution audit |

Recommended indexes:

```sql
CREATE UNIQUE INDEX ux_custom_logic_connector_key
ON custom_logic_connectors(entity_key, connector_key);

CREATE INDEX idx_custom_connector_events
ON custom_connector_events(connector_key, created_at DESC);
```

---

## 3. Connector Model

Connector has four parts:

| Part | Meaning |
| :--- | :--- |
| Trigger | e.g. transition `Draft -> Confirmed` |
| Source | field/line items/entity source |
| Operation | allowlisted operation |
| Target | field/custom entity/inventory effect target |

Example:

```json
{
  "connectorKey": "custom_order_confirm_decrease_inventory",
  "label": "Duyet don hang thi tru ton kho",
  "trigger": {
    "type": "transition",
    "entityKey": "custom_sales_order",
    "fromState": "Draft",
    "toState": "Confirmed"
  },
  "source": {
    "lineItemsField": "items",
    "productField": "items.product",
    "locationField": "warehouse",
    "quantityOperation": {
      "type": "sumLines",
      "field": "items.quantity"
    }
  },
  "operation": {
    "type": "inventoryEffect",
    "effectType": "OUTBOUND_DECREASE"
  },
  "target": {
    "refType": "core",
    "refEntityKey": "inventory"
  }
}
```

---

## 4. Operation Allowlist

| Operation | Meaning | Note |
| :--- | :--- | :--- |
| `copy` | Copy source to target | Same record or allowed target |
| `set` | Set fixed value | Normal fields only |
| `add` | Add numeric values | Not direct inventory |
| `subtract` | Subtract numeric values | Not direct inventory |
| `multiply` | Multiply values | e.g. quantity * unitPrice |
| `sumLines` | Sum line item field | bounded line items |
| `inventoryEffect` | Compile to inventory effect | Required for stock changes |

Forbidden:

- JavaScript/expression language.
- SQL.
- Arbitrary API calls.
- Access undeclared fields/entities.
- Direct update to `Inventory.quantity`.

---

## 5. Validation

Publish/dry-run must validate:

1. Trigger exists and belongs to published/draft entity version being validated.
2. Source field exists and has compatible type.
3. Target field/entity exists and user has required permission.
4. Operation is in allowlist.
5. `line_items` does not exceed configured limit.
6. Connector that touches inventory compiles to effect template.
7. No cycle/cascade loop, e.g. A updates B then B updates A.

---

## 6. API Contract

| Method | Path | Permission | Purpose |
| :--- | :--- | :--- | :--- |
| PUT | `/api/v1/custom/entities/{entityKey}/connectors` | `can_manage_custom_builder` | Save connector draft |
| POST | `/api/v1/custom/entities/{entityKey}/connectors/dry-run` | `can_manage_custom_builder` | Simulate connector |
| POST | `/api/v1/custom/entities/{entityKey}/publish` | Owner/Admin | Validate and publish connector |

Dry-run returns:

```json
{
  "valid": true,
  "plannedActions": [
    {
      "type": "inventoryEffect",
      "effectType": "OUTBOUND_DECREASE",
      "sourceLineKey": "line-1",
      "productRef": { "refType": "core", "refEntityKey": "products", "refId": 12 },
      "locationRef": { "refType": "core", "refEntityKey": "warehouse_locations", "refId": 3 },
      "quantity": 5
    }
  ],
  "warnings": []
}
```

---

## 7. Frontend Requirements

- Canvas or step builder for trigger/source/operation/target.
- Use controls, not free text, for operation choice.
- Preview/dry-run with sample data.
- Warning for inventory/cross-entity target.
- Diff before applying AI suggestion.
- Save only structured JSON rule to backend.

---

## 8. Business Rules

| ID | Rule | Result |
| :--- | :--- | :--- |
| BR-CON-01 | Operation outside allowlist | Reject 422 |
| BR-CON-02 | Connector accesses undeclared field/entity | Reject 422 |
| BR-CON-03 | Inventory connector cannot compile to effect | Reject publish/dry-run |
| BR-CON-04 | Cycle detected | Reject publish |
| BR-CON-05 | Missing read/write permission for target | Reject 403/422 |

---

## 9. Acceptance Criteria

```gherkin
Given Owner tao entity "Don hang tuy chinh"
And entity co field line_items gom product reference va quantity
And entity co field warehouse la location reference
When Owner keo-tha connector "Confirmed thi tru ton kho"
Then backend luu connector dang JSON rule co cau truc
And compile duoc thanh planned OUTBOUND_DECREASE effects theo tung dong hang
```

```gherkin
Given Owner tao connector A cap nhat B
And connector B cap nhat A
When Owner publish entity
Then backend reject vi phat hien vong lap connector
```

## 10. Test Plan

| Test | Expected |
| :--- | :--- |
| Connector allowlist | Unsafe operation rejected |
| Connector undeclared field | Rejected |
| Connector cycle | Rejected at publish |
| Inventory connector compile | Planned effects generated |
| Multi-line connector | Stable `sourceLineKey/effectIndex` |
| UI canvas state | Not treated as source of truth |

SRS handoff state: `READY_FOR_TECH_SPEC`.
