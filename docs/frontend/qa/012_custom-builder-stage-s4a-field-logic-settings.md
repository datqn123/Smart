# QA Spec - Custom Builder Stage S4A Field Logic Settings

> Agent: QA_SPEC_WRITER  
> SRS: `docs/frontend/srs/012_custom-builder-settings-first-ui-redesign.md`

## Test Matrix

| Area | Scenario | Expected |
| :--- | :--- | :--- |
| Validation | Set text min length greater than max length | Validation error in `logic` section |
| Validation | Enter invalid regex pattern | Validation error in `logic` section |
| Number | Set numeric min greater than max | Validation error in `logic` section |
| Default | Set select default not in options | Validation error |
| Options | Add duplicate select options | Validation error |
| Visibility | Mark required field as hidden | Validation error |
| Read-only | Mark required field read-only with no default | Warning only |
| Conditional | Condition references same field | Validation error |
| Computed | Enable computed placeholder | Disabled editor shown and warning explains it is placeholder-only |
| Preview | Hidden field in form preview | Field is omitted from preview |
| Scope | Save draft | Uses mock adapter only, no backend/ai_python change |

## Required Checks

- `npm run build` in `frontend/mini-erp`.
- `git diff --check` for touched files.
- Browser desktop/mobile if permission guard allows opening `/settings/custom-builder`.
