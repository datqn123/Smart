# QA Spec - Custom Builder Settings-first UI Redesign

> Source SRS: `docs/frontend/srs/012_custom-builder-settings-first-ui-redesign.md`  
> Tech Spec: `docs/frontend/tech_lead/010_custom-builder-settings-first-ui-redesign.md`  
> Agent: QA_SPEC_WRITER  
> Readiness: QA_READY_FOR_CODING

## Scope

Verify frontend-only S1-S3:

- Builder List Page.
- Create Interface Wizard.
- Edit Interface Settings.

No backend, `ai_python`, real workflow, connector, inventory, or AI verification is required because those are out of scope.

## P0 Test Matrix

| Area | Case | Expected |
| :--- | :--- | :--- |
| List default | Open `/settings/custom-builder` | Shows builder list/empty state, not an auto-selected editor |
| List loading/error | Mock load pending/fails | Stable skeleton/error card with retry |
| Search/filter | Search by label/key and filter by status | List updates without layout break |
| Empty | Adapter returns no pages | Clear CTA `Tao giao dien moi`, no dense panels |
| Wizard step 1 | Empty/invalid name or key | Inline validation, next blocked |
| Wizard step 2 | Existing vs new menu parent | Only relevant controls are shown |
| Wizard step 3 | Add reference field | UI stores canonical `reference`, `refType`, `refEntityKey` |
| Wizard step 4 | Hide required field from form | Review validation fails |
| Wizard step 5 | Invalid config | Publish disabled and jump-to-error action exists |
| Pending | Save/create/publish pending | Related actions disabled |
| Edit | Created draft opens settings | Sections are clear: overview/data/display/permissions/check/advanced |
| Advanced | Open advanced | Disabled/collapsed placeholder, no real workflow/inventory/AI config |
| Responsive | Desktop and mobile | Stepper/summary/list do not overlap |

## Failure Modes

- Validation drift: frontend allows publish while required config is missing.
- UI density regression: list or wizard shows runtime/workflow/inventory/AI as main panels.
- Mock scattering: component hard-codes fixture catalogs instead of adapter.
- Permission confusion: disabled actions lack a short reason.
- Contrast regression: CTA text invisible on dark/primary backgrounds.

## Regression Scope

- Existing sidebar custom runtime menu still loads from mock adapter fallback.
- Runtime page remains frontend fixture-only and does not call backend for this feature.
- Existing auth no-permission view remains understandable.

## Verification Commands

Run in `frontend/mini-erp`:

```powershell
npm run build
```

Browser verification when available:

- Desktop screenshot at `/settings/custom-builder`.
- Mobile screenshot at `/settings/custom-builder`.
- Optional: click `Tao giao dien moi`, walk wizard through review, create draft, open edit sections.

## QA Readiness

`QA_READY_FOR_CODING`

Risks are acceptable for a UI-first fixture implementation. Remaining unverified browser screenshots must be reported if Browser tooling is unavailable.
