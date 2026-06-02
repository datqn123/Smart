# SRS - Phase 7 AI Custom Draft

> File: `docs/dev/common/008_custom-builder-phase7-ai-custom-draft.md`  
> Agent: SRS_WRITER  
> Ngay cap nhat: 02/06/2026  
> Trang thai: DRAFT_FOR_PO_REVIEW  
> Pham vi: AI creates draft custom records only; no submit/approve/effect.

---

## 1. Objective

AI helps user enter data faster by creating draft custom records:

- User describes a desired record.
- AI resolves references through Spring.
- AI calls scoped Harness tool to create draft.
- User reviews in UI.
- User manually submits/approves through normal workflow.

AI never runs inventory effects or transitions.

---

## 2. Architecture

| Layer | Responsibility |
| :--- | :--- |
| LangGraph | Route to custom draft branch |
| Harness | Allow only scoped create-draft tool |
| Spring | Validate RBAC, metadata, references, create draft |
| Frontend | Display draft for user review |

---

## 3. Draft Tool Contract

Tool input should be structured:

```json
{
  "entityKey": "damaged_stock_report",
  "values": {
    "product": {
      "refType": "core",
      "refEntityKey": "products",
      "refId": 12
    },
    "location": {
      "refType": "core",
      "refEntityKey": "warehouse_locations",
      "refId": 3
    },
    "quantity": 5,
    "reason": "Vo trong qua trinh van chuyen"
  }
}
```

Spring fills/validates snapshots and default state.

---

## 4. Guardrails

| Risk | Guardrail |
| :--- | :--- |
| AI creates final approved record | Tool only creates draft |
| AI runs effect | No transition/effect tool allowed |
| AI chooses wrong reference | Spring resolves and validates refs |
| User lacks permission | Spring rejects |
| Metadata injection | Treat metadata labels as untrusted |

---

## 5. UI Requirements

- Show AI-created draft with badge/source.
- User can edit before submit.
- User must manually trigger submit/approve.
- If record has inventory effect later, normal dry-run/confirm rules apply.

---

## 6. Acceptance Criteria

```gherkin
Given AI tao draft custom record
When user chua submit/approve tren UI
Then khong co tac dong kho nao xay ra
```

```gherkin
Given user khong co quyen tao record cho entity custom
When AI goi create draft tool
Then Spring tra 403
And Harness audit tool call
```

## 7. Test Plan

| Test | Expected |
| :--- | :--- |
| AI create draft | Record created in draft/default state |
| AI submit attempt | Blocked |
| AI effect attempt | Blocked |
| Missing permission | 403 |
| Invalid reference | Reject |
| User review flow | Draft visible/editable before submit |

SRS handoff state: `READY_FOR_TECH_SPEC`.
