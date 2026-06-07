# Tech Spec - Custom Builder Stage S4A Field Logic Settings

> Agent: TECH_SPEC_WRITER  
> SRS: `docs/frontend/srs/012_custom-builder-settings-first-ui-redesign.md`  
> Scope: Stage S4A, frontend settings UI only.

## Scope

Implement basic field logic inside the existing edit settings screen:

- Advanced validation metadata.
- Default value.
- Select option editor.
- Read-only and hidden flags.
- Simple conditional visibility.
- Computed field as disabled placeholder only.

Do not modify backend, `ai_python`, workflow, connector, inventory, runtime writes, or AI behavior.

## Design

Extend the frontend mock adapter `BuilderFieldDefinition` with optional draft-only metadata:

- `validation`: min/max length, numeric min/max, regex pattern, custom message.
- `defaultValue`: fixture default used by preview and validation only.
- `readOnly`, `hidden`.
- `conditionalVisibility`: source field, operator, value, effect.
- `computed`: placeholder state and label.

Render S4A in the edit settings `Dữ liệu` section. Each field remains a single card with the base row first and a compact `Logic cơ bản` block below it. Select option editor appears only for `single_select`/`select`. Reference target editor remains unchanged.

## Validation Rules

- Select field must have at least one non-empty unique option.
- Default value for select must match an option when set.
- Number/money validation bounds must be numeric and min must not exceed max.
- Text length bounds must be numeric and min must not exceed max.
- Regex pattern must compile.
- Hidden required field is an error.
- Read-only required field without default value is a warning.
- Conditional visibility cannot reference the same field and must choose a source field.
- Computed field is placeholder-only and emits a warning when enabled.

## Files

- `frontend/mini-erp/src/features/custom-builder/api/customBuilderMockAdapter.ts`
- `frontend/mini-erp/src/features/custom-builder/pages/CustomBuilderPage.tsx`

## Verification

- Type/build frontend.
- Diff check.
- Browser verification if an account/session with builder permission is available.
