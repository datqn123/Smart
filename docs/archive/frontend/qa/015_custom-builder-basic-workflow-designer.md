# QA Spec - Custom Builder Basic Workflow Designer

> Agent: QA_SPEC_WRITER  
> Superpowers alignment: test-driven-development, verification-before-completion.

## Test Matrix

| Area | Scenario | Expected |
| :--- | :--- | :--- |
| Advanced | Open edit settings | `Nâng cao` remains collapsed by default |
| Toggle | Enable workflow | State/transition editor appears |
| Validation | Enable workflow with no transitions | Error appears in `Kiểm tra` under Workflow |
| States | Add state | New draft state appears in designer and preview |
| Transitions | Add transition | Transition appears in list and preview |
| Transition validation | Transition references same from/to | Workflow error |
| Role validation | Transition has no role | Workflow warning |
| Scope | Save draft | Uses frontend mock adapter only |
| Mobile | Open advanced on mobile | Controls stack, no overlap |

## Required Checks

- `npm run build` from `frontend/mini-erp`.
- `git diff --check` for touched files.
- Playwright desktop/mobile route verification with test-only frontend session.
