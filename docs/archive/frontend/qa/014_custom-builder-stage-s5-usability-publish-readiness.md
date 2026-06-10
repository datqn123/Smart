# QA Spec - Custom Builder Stage S5 Usability QA + Publish Readiness

> Agent: QA_SPEC_WRITER  
> SRS: `docs/frontend/srs/012_custom-builder-settings-first-ui-redesign.md`

## Test Matrix

| Area | Scenario | Expected |
| :--- | :--- | :--- |
| Wizard | Open create flow from list | Five clear steps, no runtime/workflow panels |
| Wizard validation | Remove required form field then review | Review groups error under display/view and shows first-error action |
| Edit check | Open `Kiểm tra` section | Shows readiness summary, grouped errors/warnings, preview |
| First error | Click `Sửa lỗi đầu tiên` | Navigates to mapped section |
| Publish | Errors exist | Publish disabled and reason visible |
| Publish | Dirty draft exists | Publish disabled until saved |
| Responsive | Desktop | Header, section nav, main, summary do not overlap |
| Responsive | Mobile | Columns stack, horizontal tables stay scrollable, action buttons wrap |
| Scope | Save draft | Uses mock adapter only |
| Scope | Advanced placeholders | Still collapsed/disabled |

## Required Checks

- `npm run build` from `frontend/mini-erp`.
- `git diff --check` on touched files.
- Browser screenshots for desktop and mobile when route permission can be supplied by test session.
