# Custom Builder Display Polish QA Spec

> Agent: QA_SPEC_WRITER  
> Source SRS: `docs/frontend/srs/012_custom-builder-settings-first-ui-redesign.md`  
> Tech Spec: `docs/frontend/tech_lead/011_custom-builder-edit-settings-preview-addendum.md`  
> Scope: Display tab polish, frontend fixture/mock only

## Acceptance Checklist

- Display tab lets Admin choose list columns without leaving settings.
- Each selected column exposes:
  - width editor
  - align picker: `left`, `center`, `right`
  - format picker: `text`, `number`, `currency`, `date`, `badge`
- Default sort picker is visible and updates `views.defaultSort`.
- Filter field configuration is visible and updates `views.filterFields`.
- Form builder supports multiple form sections.
- Form sections can be added, removed, renamed, and reordered.
- Form field membership can be configured per section.
- Required fields missing from every form section still produce validation in `Kiem tra`.
- Publish remains disabled when display validation has errors.
- No backend, `ai_python`, connector, inventory, or AI behavior changes.

## Test Cases

1. Column settings
   - Open `/settings/custom-builder`, edit a page, open `Hien thi`.
   - Toggle a field into table columns.
   - Change width, align, and format.
   - Expected: preview remains visible and no layout overlap occurs.

2. Default sort
   - Pick a field and direction.
   - Expected: `views.defaultSort` changes and Save Draft becomes dirty.

3. Filter fields
   - Toggle a filter field.
   - Expected: selection persists in the settings draft and no backend call is made.

4. Multi-section form
   - Add a section, rename it, move it up/down, and assign fields.
   - Expected: form preview uses section membership and validation still checks required fields.

5. Validation jump
   - Remove a required field from all form sections.
   - Go to `Kiem tra` and click `Sua loi dau tien`.
   - Expected: UI jumps to `Hien thi`.

6. Responsive
   - Verify desktop and mobile screenshots.
   - Expected: display controls stack cleanly without hidden controls or text overlap.
