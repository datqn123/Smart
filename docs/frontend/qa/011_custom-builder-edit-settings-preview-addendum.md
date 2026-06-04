# QA Addendum - Custom Builder Edit Settings + Lightweight Preview

> Source SRS: `docs/frontend/srs/012_custom-builder-settings-first-ui-redesign.md`  
> Tech Spec: `docs/frontend/tech_lead/011_custom-builder-edit-settings-preview-addendum.md`  
> Agent: QA_SPEC_WRITER  
> Readiness: QA_READY_FOR_CODING

## Scope

Verify S3-S4 only:

- Edit Interface Settings sections.
- Lightweight preview inside settings.

## Test Matrix

| Area | Case | Expected |
| :--- | :--- | :--- |
| Edit overview | Open existing bundle | Shows status, route, field count, menu and editable name/description |
| Data section | Rename field key | Table/form selections stay aligned with new key |
| Data section | Add reference field without target | Validation reports target error |
| Display section | Toggle list/form fields | Preview updates and validation catches missing required form fields |
| Preview | Table preview | Shows sample rows when present and empty sample state when absent |
| Preview | Form preview | Shows read-only form sample using selected form fields |
| Check section | Validation errors | Jump action moves to data/display section |
| Advanced | Open advanced | Placeholder only; no real workflow/connector/inventory/AI actions |
| Pending | Save/publish | Buttons disable while pending |

## Required Verification

Run:

```powershell
npm run build
```

Browser screenshots are desirable but may be blocked by local auth permission. If blocked, report the permission state and build verification.
