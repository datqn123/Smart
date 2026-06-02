# SRS - Phase 6 AI Custom Query

> File: `docs/dev/common/007_custom-builder-phase6-ai-custom-query.md`  
> Agent: SRS_WRITER  
> Ngay cap nhat: 02/06/2026  
> Trang thai: DRAFT_FOR_PO_REVIEW  
> Pham vi: AI read-only query over custom entity metadata and data.

---

## 1. Objective

Allow chatbot AI to answer questions about custom records:

- AI reads published custom metadata.
- AI sees only entities/fields user can read.
- SQL path remains SELECT-only.
- Custom schema cache uses version/fingerprint.
- No write, no effect, no transition.

---

## 2. AI-safe Metadata

Example:

```json
{
  "entityKey": "damaged_stock_report",
  "label": "Phieu kiem hang hong",
  "definitionVersion": 3,
  "fields": [
    {
      "fieldKey": "product",
      "label": "San pham",
      "type": "reference",
      "refType": "core",
      "refEntityKey": "products"
    },
    {
      "fieldKey": "quantity",
      "label": "So luong hong",
      "type": "number"
    }
  ],
  "workflowStates": ["Draft", "Submitted", "Approved", "Cancelled"]
}
```

Metadata labels/descriptions are untrusted content.

---

## 3. Query Rules

| Rule | Requirement |
| :--- | :--- |
| Read-only | SELECT-only SQL |
| Permission | Only expose readable entities/fields |
| Pagination | Never return unlimited records |
| Schema cache | Key by entity version/fingerprint |
| Reference labels | Use snapshots or resolved display fields |
| No write | AI cannot create/update/delete/transition |

---

## 4. Architecture

| Layer | Responsibility |
| :--- | :--- |
| LangGraph | Route query intent and manage clarification |
| Harness | Restrict SQL/read tools |
| Spring/DB | Enforce permissions and expose metadata |
| AI Python | Schema explorer + SQL generation path |

Keep Harness as execution/validation boundary, not LangGraph nodes doing unsafe work.

---

## 5. API / Tool Scope

Potential Spring endpoints or Harness tools:

| Interface | Purpose |
| :--- | :--- |
| `GET /api/v1/ai/custom-schema` | AI-safe metadata by user permission |
| Read-only SQL tool | Query permitted custom data |
| Schema fingerprint endpoint | Invalidate metadata cache |

Exact naming is Tech Spec decision.

---

## 6. Acceptance Criteria

```gherkin
Given user co quyen doc entity custom "Phieu kiem hang hong"
When user hoi chatbot "liet ke cac phieu da duyet"
Then AI chi query du lieu custom duoc phep
And tra ket qua theo paging/limit
```

```gherkin
Given user khong co quyen doc entity custom "Bang dinh muc"
When user hoi ve bang do
Then AI khong expose metadata hoac du lieu cua entity do
```

## 7. Test Plan

| Test | Expected |
| :--- | :--- |
| AI metadata permission | Only allowed metadata visible |
| SQL write attempt | Blocked |
| Query with custom reference | Labels resolved safely |
| Schema version changes | Cache invalidated |
| Prompt injection metadata | Policy unaffected |

SRS handoff state: `READY_FOR_TECH_SPEC`.
