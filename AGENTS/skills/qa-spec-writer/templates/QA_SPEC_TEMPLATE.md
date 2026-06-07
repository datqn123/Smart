# QA Spec / Test Plan — TaskXXX — <Feature Name>

> **File:** `<path>`  
> **Source SRS:** `<path>`  
> **Tech Spec / Handoff:** `<path>`  
> **Scope:** Backend | Frontend | Database | AI Agentic | Full-stack  
> **Agent:** QA Spec Writer  
> **Date:** <DD/MM/YYYY>  
> **Readiness:** QA_READY_FOR_CODING | QA_READY_WITH_RISKS | QA_BLOCKED

---

## 1. Test Objective

State the behavior that must be proven before release.

---

## 2. Evidence Read

| Type | Path / symbol | Notes |
| :--- | :--- | :--- |
| SRS | `<path>` | Requirement source |
| Tech Spec | `<path>` | Implementation handoff |
| Existing tests | `<path>` | Reusable pattern |
| API / docs | `<path>` | Contract source |
| Code | `<path>` | Affected module |

---

## 3. Test Scope

### In Scope

- ...

### Out of Scope

- ...

---

## 4. Horizontal QA Analysis

| Risk / pattern | Similar scopes checked | Finding | Required test |
| :--- | :--- | :--- | :--- |
| Auth/RBAC | ... | ... | ... |
| Validation | ... | ... | ... |
| Error envelope | ... | ... | ... |
| Transaction / rollback | ... | ... | ... |
| Frontend cache/state | ... | ... | ... |
| AI validation/policy | ... | ... | ... |

---

## 5. Test Matrix

| ID | Level | Scenario | Input / setup | Expected result | Priority |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TC-001 | Unit | ... | ... | ... | P0 |
| TC-002 | Integration | ... | ... | ... | P0 |
| TC-003 | Frontend | ... | ... | ... | P1 |
| TC-004 | E2E/manual | ... | ... | ... | P1 |

---

## 6. Failure Modes

| Failure | Classification | Expected behavior | Test ID |
| :--- | :--- | :--- | :--- |
| Missing permission | Backend/RBAC | 403 and Vietnamese user message | TC-... |
| Invalid input | Validation | 400 with safe message | TC-... |
| Conflict | Business rule | 409 with business reason | TC-... |
| Empty result | UX/data | Stable empty state | TC-... |
| Downstream failure | Contract drift | Sanitized error and correlation id | TC-... |

---

## 7. AI Agentic Tests

> Use only when AI is in scope.

| ID | Area | Scenario | Expected result |
| :--- | :--- | :--- | :--- |
| AI-001 | Runtime flow | ... | Correct route/state/retry |
| AI-002 | Validation/policy behavior | ... | Tool blocked or allowed deterministically |
| AI-003 | Tool integration | ... | Scoped input/output and auth propagation |
| AI-004 | Contract drift | ... | Sanitized failure and no raw internal leak |

---

## 8. Test Data / Mocks

| Data / mock | Purpose | Location / creation |
| :--- | :--- | :--- |
| ... | ... | ... |

---

## 9. Verification Commands

```powershell
# Backend
./mvnw.cmd test

# Frontend
npm test -- --run

# AI
pytest
```

Adjust commands to the actual module and scope before execution.

---

## 10. Open Questions / Gaps

| ID | Question / gap | Impact | Blocker? | Owner |
| :--- | :--- | :--- | :---: | :--- |
| OQ-1 | ... | ... | Yes / No | ... |

---

## 11. QA Readiness

**Status:** QA_READY_FOR_CODING | QA_READY_WITH_RISKS | QA_BLOCKED

**Reason:** ...

**Instructions to Coding Agent:**

1. Implement with tests mapped to P0 first.
2. Keep test names traceable to `TC-*`.
3. Report any skipped tests with reason and risk.
