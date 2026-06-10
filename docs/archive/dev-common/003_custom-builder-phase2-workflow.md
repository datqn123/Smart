# SRS - Phase 2 Custom Workflow

> File: `docs/dev/common/003_custom-builder-phase2-workflow.md`  
> Agent: SRS_WRITER  
> Ngay cap nhat: 02/06/2026  
> Trang thai: DRAFT_FOR_PO_REVIEW  
> Pham vi: Workflow states/transitions for custom records, no connector/effect yet.

---

## 1. Objective

Phase 2 them workflow state machine cho custom entity:

- Owner/Admin thiet ke states va transitions.
- Record co `state_key`.
- User chuyen trang thai theo permission.
- Timeline ghi event.
- UI chan thao tac khi transition pending.

Phase nay chua cong/tru kho.

---

## 2. Data Model

| Bang | Vai tro |
| :--- | :--- |
| `custom_workflow_definitions` | Workflow per entity/version |
| `custom_workflow_states` | State list: key, label, initial, terminal, lock flags |
| `custom_workflow_transitions` | From/to, label, permission, validation flags |
| `custom_record_events` | Transition timeline |

`custom_records.state_key` from Phase 1 becomes required after workflow is published.

---

## 3. Workflow Rules

| Rule | Requirement |
| :--- | :--- |
| One initial state | Exactly one `initial=true` |
| Valid transition endpoints | `fromState` and `toState` must exist |
| No duplicate transition key | Unique per entity/version |
| Terminal lock | Terminal state cannot require next transition |
| Edit lock | State may lock record editing |
| Permission | Transition checks backend permission |

---

## 4. API Contract

| Method | Path | Permission | Purpose |
| :--- | :--- | :--- | :--- |
| PUT | `/api/v1/custom/entities/{entityKey}/workflow` | `can_manage_custom_builder` | Save workflow draft |
| POST | `/api/v1/custom/entities/{entityKey}/publish` | Owner/Admin | Publish with workflow validation |
| POST | `/api/v1/custom/records/{recordId}/transitions/{transitionKey}` | Transition permission | Execute transition |

Example workflow:

```json
{
  "states": [
    { "stateKey": "Draft", "label": "Nhap", "initial": true, "terminal": false },
    { "stateKey": "Submitted", "label": "Cho duyet", "initial": false, "terminal": false },
    { "stateKey": "Approved", "label": "Da duyet", "initial": false, "terminal": true },
    { "stateKey": "Cancelled", "label": "Da huy", "initial": false, "terminal": true }
  ],
  "transitions": [
    {
      "transitionKey": "submit",
      "label": "Gui duyet",
      "fromState": "Draft",
      "toState": "Submitted",
      "requiredPermission": "can_use_custom_entities"
    }
  ]
}
```

---

## 5. Transition Pipeline

1. Lock record with `SELECT ... FOR UPDATE`.
2. Load definition version attached to record.
3. Validate transition exists.
4. Validate `record.state_key == transition.fromState`.
5. Check transition permission.
6. Validate record values against definition.
7. Update `state_key`.
8. Write `custom_record_events`.
9. Commit.

If any step fails, rollback all changes.

---

## 6. UI Guardrails

| Situation | UI behavior |
| :--- | :--- |
| Transition request pending | Disable all transition buttons on the record |
| State locks edit | Disable form edit controls |
| Permission missing | Hide or disable transition button with reason |
| Transition error | Unlock UI and show backend error |
| Transition success | Refetch record detail/list/timeline |

No optimistic update for workflow transitions.

---

## 7. Business Rules

| ID | Rule | Result |
| :--- | :--- | :--- |
| BR-WF-01 | Workflow has no initial state | Reject publish 422 |
| BR-WF-02 | Transition endpoint missing | Reject publish 422 |
| BR-WF-03 | Transition current state mismatch | Reject 409 |
| BR-WF-04 | User lacks transition permission | Reject 403 |
| BR-WF-05 | Record in locked state edited | Reject 409 |

---

## 8. Acceptance Criteria

```gherkin
Given record dang o state Draft
When user co quyen goi transition submit
Then backend doi state sang Submitted
And ghi transition event
```

```gherkin
Given record dang o state Draft
When user goi transition approve yeu cau fromState Submitted
Then backend tra 409
And record khong bi mutate
```

## 9. Test Plan

| Test | Expected |
| :--- | :--- |
| Publish workflow no initial | 422 |
| Publish duplicate transition | 422 |
| Valid transition | State updated and event written |
| Invalid state transition | 409, no mutation |
| Missing permission | 403 |
| Pending double click | UI sends one request |

SRS handoff state: `READY_FOR_TECH_SPEC`.
