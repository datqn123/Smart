# Custom Builder Logic Connector Builder QA Spec

> Agent: QA_SPEC_WRITER  
> Source SRS: `docs/frontend/srs/012_custom-builder-settings-first-ui-redesign.md`  
> Scope: Logic Connector Builder co ban trong section Nang cao

## Acceptance Checklist

- Advanced section is collapsed by default.
- Logic automation has an explicit enable/disable toggle.
- Connector list is editable without SQL/JS/free formula/custom endpoint inputs.
- Rule builder exposes only safe selects/inputs:
  - Trigger
  - Source
  - Operation
  - Target
  - Review
- Operation allowlist is exactly:
  - `copy`
  - `set`
  - `add`
  - `subtract`
  - `multiply`
  - `sumLines`
- Dry-run preview shows mock before/after values and states that it is fixture-only.
- Rule JSON is read-only and reflects the current draft rule.
- Connector validation errors appear in `Kiem tra`.
- Publish is disabled when connector validation has errors.
- Backend, `ai_python`, inventory effect, and AI behavior are untouched.

## Test Cases

1. Initial advanced state
   - Open edit screen for fixture page.
   - Expected: Advanced section is closed and connector UI is not visible.

2. Enable connector
   - Open Advanced.
   - Toggle logic automation on.
   - Expected: connector list, step builder, dry-run, and read-only JSON are visible.

3. Operation allowlist
   - Open operation select.
   - Expected: only `copy`, `set`, `add`, `subtract`, `multiply`, `sumLines` are selectable.

4. Validation error
   - Enable logic automation and remove all connector rules.
   - Go to `Kiem tra`.
   - Expected: section `Logic field` shows an error for missing connector rule.
   - Expected: publish action is disabled.

5. Dry-run
   - Select a rule with source and target.
   - Expected: before/after preview changes using mock sample data only.

6. Responsive
   - Verify desktop and mobile viewport.
   - Expected: no overlapping panels, no cramped multi-panel layout, JSON panel wraps safely.
