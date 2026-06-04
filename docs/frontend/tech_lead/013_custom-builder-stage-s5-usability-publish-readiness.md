# Tech Spec - Custom Builder Stage S5 Usability QA + Publish Readiness

> Agent: TECH_SPEC_WRITER  
> SRS: `docs/frontend/srs/012_custom-builder-settings-first-ui-redesign.md`  
> Scope: frontend settings UI and fixture/mock adapter only.

## Scope

Stage S5 hardens the existing settings-first Custom Builder flow:

- Review the full create-interface wizard path.
- Improve the edit `Kiểm tra` screen.
- Group validation by section.
- Add `Sửa lỗi đầu tiên` actions.
- Keep Publish disabled while errors remain.
- Clean up desktop/mobile layout pressure.
- Clean up fixture/mock adapter formatting and readiness metadata.

Out of scope: backend publish API, `ai_python`, workflow, connector, inventory, AI, real runtime persistence.

## Implementation Notes

- Add shared validation helpers in `CustomBuilderPage.tsx` for section labels, grouping, first-error routing, and readiness metrics.
- Reuse the grouped validation panel in wizard review, edit check section, and edit side summary.
- Keep Save Draft available when the user has a valid draft baseline, but keep Publish disabled for any validation error, dirty draft, saving, or mock conflict state.
- Use mock adapter only for persistence and publish readiness metadata.
- Preserve advanced placeholders collapsed/disabled.

## Verification

- Frontend build.
- Diff whitespace check.
- Browser pass through create wizard and edit check section at desktop/mobile with a test-only frontend session.
