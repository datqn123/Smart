# SRS - Phase 4 Inventory Effect Engine

> File: `docs/dev/common/005_custom-builder-phase4-inventory-effect.md`  
> Agent: SRS_WRITER  
> Ngay cap nhat: 02/06/2026  
> Trang thai: DRAFT_FOR_PO_REVIEW  
> Pham vi: Safe inventory effect execution for custom workflows/connectors.

---

## 1. Objective

Phase 4 lets custom workflow affect stock safely:

- Effects are template-driven.
- Backend executor is the only service allowed to update stock.
- Transition + effect is atomic.
- Negative stock is rejected.
- Retry is idempotent.
- UI requires dry-run/confirm before risky transition.

---

## 2. Data Model

| Bang | Vai tro |
| :--- | :--- |
| `custom_inventory_effect_rules` | Effect metadata compiled from builder/connector |
| `custom_inventory_effect_events` | Execution result, idempotency, audit |
| `Inventory` | Core stock quantity |
| `InventoryLogs` | Core stock timeline |

Recommended partial unique index:

```sql
CREATE UNIQUE INDEX ux_custom_inventory_effect_applied
ON custom_inventory_effect_events(idempotency_key)
WHERE status = 'Applied';
```

---

## 3. Effect Types

| Effect type | Behavior | Required fields |
| :--- | :--- | :--- |
| `INBOUND_INCREASE` | Increase stock at target location | product, toLocation, quantity |
| `OUTBOUND_DECREASE` | Decrease stock at source location | product, fromLocation, quantity |
| `TRANSFER` | Decrease source and increase target | product, fromLocation, toLocation, quantity |
| `ADJUST_INCREASE` | Adjustment increase | product, location, quantity |
| `ADJUST_DECREASE` | Adjustment decrease | product, location, quantity |

`RESERVE` and `RELEASE_RESERVATION` are out of MVP unless reservation tables are designed.

---

## 4. Effect Rule Example

```json
{
  "rules": [
    {
      "transitionKey": "approve",
      "effectType": "ADJUST_DECREASE",
      "productField": "product",
      "locationField": "location",
      "quantityField": "quantity",
      "noteTemplate": "Hang hong: {{reason}}"
    }
  ]
}
```

For line items, compiled planned effects must include stable `sourceLineKey` or `effectIndex`.

---

## 5. Execution Pipeline

1. Lock custom record.
2. Load definition version.
3. Resolve connector/effect rules.
4. Dry-run all planned effects.
5. Build `idempotency_key = recordId + transitionKey + effectRuleId + sourceLineKey/effectIndex + definitionVersion`.
6. Check whether `custom_inventory_effect_events` has same key with status `Applied`.
7. Resolve product/location/quantity from `values_json`.
8. Validate product/location active.
9. Lock inventory rows in stable order.
10. Reject decrease/transfer if stock would become negative.
11. Update `Inventory.quantity`.
12. Insert `InventoryLogs`.
13. Insert effect event status `Applied`.
14. Update record state.
15. Commit transaction.

If any step fails, rollback state and inventory.

---

## 6. Lock Ordering

Tech Spec must define one lock order for custom and core inventory flows.

Minimum requirement:

- Do not allow one flow to lock `custom_records -> inventory` while another locks `inventory -> custom_records`.
- When multiple inventory rows are touched, lock by stable order, e.g. `inventory.id ASC`.
- Add limited deadlock retry and correlation id logging if strict ordering cannot be guaranteed.

---

## 7. Permission Guardrail

All stock-changing effects require `can_manage_inventory` or stronger permission.

Dynamic builder permission cannot lower this hard guardrail.

For bulk/high-risk effects, Tech Spec may add `can_execute_inventory_effect` or Owner/Admin-only rule.

---

## 8. UI Guardrails

| Situation | UI behavior |
| :--- | :--- |
| Transition has effect | Show dry-run preview before confirm |
| Dry-run failed | Confirm button disabled |
| Request pending | Disable all risky buttons |
| Success | Refetch record, list, inventory-related data |
| Error | Unlock UI and display business error |

No optimistic update.

---

## 9. InventoryLogs / Audit

Every applied effect must insert `InventoryLogs`. For custom source records, `reference_note` should include:

- entity key.
- record id.
- transition key.
- effect rule id.
- user id/name.

If stronger trace is needed, Tech Spec may add polymorphic columns to `InventoryLogs`; MVP can use `reference_note` plus `custom_inventory_effect_events.inventory_log_id`.

Failed effect attempts should be auditable. If DB transaction rolls back all effect writes, app-level logs must still include correlation id and failure reason.

---

## 10. API Contract

| Method | Path | Permission | Purpose |
| :--- | :--- | :--- | :--- |
| PUT | `/api/v1/custom/entities/{entityKey}/effects` | `can_manage_custom_builder` | Save effect rules |
| POST | `/api/v1/custom/records/{recordId}/dry-run/{transitionKey}` | Transition permission | Preview effects |
| POST | `/api/v1/custom/records/{recordId}/transitions/{transitionKey}` | Transition permission + inventory guardrail | Execute transition/effects |

Dry-run must not write `Inventory`, `InventoryLogs`, or `custom_record_events`.

---

## 11. Business Rules

| ID | Rule | Result |
| :--- | :--- | :--- |
| BR-INV-01 | Decrease makes stock negative | Reject 409 and rollback |
| BR-INV-02 | User lacks `can_manage_inventory` | Reject 403 |
| BR-INV-03 | Event with idempotency key Applied exists | Do not apply again |
| BR-INV-04 | Event status Failed exists | Allow retry with new attempt |
| BR-INV-05 | Product/location inactive | Reject |
| BR-INV-06 | Multi-line effect idempotency collision | Reject config/test failure |

---

## 12. Acceptance Criteria

```gherkin
Given record dang o state Submitted
And transition approve co effect ADJUST_DECREASE
When Admin approve record hop le
Then backend tru dung ton kho
And ghi InventoryLogs
And doi state record sang Approved trong cung transaction
```

```gherkin
Given effect se lam ton kho am
When Admin approve record
Then backend tra 409
And record van giu state cu
And InventoryLogs khong co dong moi
```

```gherkin
Given connector "Confirmed thi tru ton kho" da publish
And mot dong hang trong don khong du ton kho
When Admin chuyen don tu Draft sang Confirmed
Then backend tra 409
And khong dong ton kho nao bi tru
And state don hang van giu Draft
```

## 13. Test Plan

| Test | Expected |
| :--- | :--- |
| Dry-run effect | No DB mutation |
| Effect apply | Inventory, logs, state updated atomically |
| Negative stock | 409 and rollback |
| Idempotency Applied retry | No double apply |
| Idempotency Failed retry | Retry allowed |
| Multi-line idempotency | No collision |
| Missing inventory permission | 403 |
| Concurrent transitions | No deadlock or limited retry |

SRS handoff state: `READY_FOR_TECH_SPEC`.
