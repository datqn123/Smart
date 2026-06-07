# Tech Spec / Coding Handoff — TaskXXX — <Feature Name>

> **File:** `<path>`  
> **Source SRS:** `<path>`  
> **Scope:** Backend | Frontend | Database | AI Agentic | Full-stack  
> **Agent:** Tech Spec Writer  
> **Date:** <DD/MM/YYYY>  
> **Readiness:** READY_FOR_CODING | READY_WITH_RISKS | BLOCKED

---

## 1. Goal

Briefly state the implementation outcome in user-observable terms.

---

## 2. Evidence Read

| Type | Path / symbol | Notes |
| :--- | :--- | :--- |
| SRS | `<path>` | Source requirement |
| Backend | `<controller/service/repository>` | Existing pattern or affected file |
| Frontend | `<page/api hook/component>` | Existing pattern or affected file |
| Database | `<Flyway/table/index>` | Existing schema or migration need |
| AI | `<runtime/tool/prompt>` | Only when in scope |
| Docs | `<api/adr/task>` | Contract or prior decision |

---

## 3. Scope Boundary

### In Scope

- ...

### Out of Scope

- ...

### Ownership

| Layer | Owner responsibility | Must not own |
| :--- | :--- | :--- |
| Frontend | UI state, route/menu visibility, query cache, visible errors | Server-side authorization |
| Backend | RBAC, business rules, transaction, persistence | Out-of-scope AI runtime ownership |
| AI runtime | Responsibilities defined by the active SRS or architecture handoff | Out-of-scope ownership |
| AI integrations | Scoped external or backend calls | Policy bypass |

---

## 4. Horizontal Analysis

| Pattern / risk | Similar scopes checked | Finding | Action |
| :--- | :--- | :--- | :--- |
| Auth/RBAC | ... | ... | ... |
| Error envelope | ... | ... | ... |
| Transaction / concurrency | ... | ... | ... |
| Cache invalidation | ... | ... | ... |
| AI validation/policy | ... | ... | ... |

---

## 5. Architecture Decision

### Decision

Describe the chosen design.

### Rationale

Explain why it fits existing project patterns.

### Alternatives Considered

| Option | Pros | Cons | Decision |
| :--- | :--- | :--- | :--- |
| A | ... | ... | Accepted / Rejected |

### ADR Required?

- Required: Yes / No
- ADR path: `<path or N/A>`
- Reason: ...

---

## 6. Implementation Slices

| Slice | User-visible result | Backend | Frontend | DB | AI |
| :--- | :--- | :--- | :--- | :--- | :--- |
| S1 | ... | ... | ... | ... | ... |

---

## 7. Contracts

### 7.1 HTTP / API

| Method | Path | Auth | Permission | Request | Response | Errors |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| ... | ... | Bearer | `...` | ... | ... | 400/401/403/409 |

### 7.2 Data / SQL

| Table | Read | Write | Rule |
| :--- | :---: | :---: | :--- |
| `...` | Yes | No | ... |

### 7.3 Frontend State

| UI action | Query/mutation key | Success behavior | Error behavior |
| :--- | :--- | :--- | :--- |
| ... | ... | ... | ... |

### 7.4 AI State / Tool Contract

> Use only when AI is in scope.

| Item | Contract |
| :--- | :--- |
| AI runtime component | ... |
| State keys | ... |
| AI validation/policy | ... |
| Tool input | ... |
| Tool output | ... |
| Retry/fallback | ... |
| Error masking | ... |

---

## 8. Files For Coding Agent

### Read First

- `...`

### Expected To Edit

- `...`

### Expected To Add

- `...`

### Do Not Edit

- `ai_python/...` unless explicitly in scope.
- Unrelated generated docs or moved files.

---

## 9. Test Plan

| Level | Test | Expected coverage |
| :--- | :--- | :--- |
| Unit | ... | Business rule / mapper / validator |
| Integration | ... | Controller/service/repository contract |
| Frontend | ... | Render, interaction, cache, errors |
| E2E/manual | ... | Main workflow |
| AI runtime flow | ... | Routing/state/retry |
| AI policy/tool integration | ... | Policy, validation, auth propagation |

---

## 10. Failure Modes

| Failure | Classification | Expected behavior |
| :--- | :--- | :--- |
| Missing permission | Backend/RBAC | 403 and Vietnamese user message |
| Invalid input | Validation | 400 with field detail if available |
| Tool rejected | Validation/policy behavior | Safe AI response, no raw internal error |
| Runtime wrong route | Runtime flow | Retry/fallback or clarification |
| Contract drift | Integration | Sanitized error and logged correlation id |

---

## 11. Open Questions / Gaps

| ID | Question / gap | Impact | Blocker? | Owner |
| :--- | :--- | :--- | :---: | :--- |
| OQ-1 | ... | ... | Yes / No | ... |

---

## 12. Coding Readiness

**Status:** READY_FOR_CODING | READY_WITH_RISKS | BLOCKED

**Reason:** ...

**Instructions to Coding Agent:**

1. Implement slices in order.
2. Preserve existing project patterns.
3. Add or update tests listed above.
4. Do not broaden scope without updating this handoff.
