# Custom Builder Logic Connector Builder Tech Spec

> Agent: TECH_SPEC_WRITER  
> Source SRS: `docs/frontend/srs/012_custom-builder-settings-first-ui-redesign.md`  
> Scope: Logic Connector Builder co ban trong section Nang cao  
> Boundary: frontend fixture/mock adapter only; no backend, no ai_python, no inventory effect, no AI

## Goal

Add a settings-first Logic Connector Builder inside the collapsed Advanced section so Admin can define simple automation rules with a safe operation allowlist and inspect a mock dry-run before/after result.

## Architecture

- Extend `customBuilderMockAdapter.ts` with connector draft types, fixtures, validation, and mock dry-run helpers.
- Extend `CustomBuilderPage.tsx` with a compact connector builder component placed below Workflow Designer inside Advanced.
- Validation errors use existing `ValidationSummaryPanel`, section key `logic`, so connector errors appear in `Kiem tra` and block publish.
- Do not add SQL, JS, custom formula, custom endpoint, or real execution hooks.

## Data Model

`BuilderLogicConnectorDefinition`

- `enabled: boolean`
- `rules: BuilderLogicConnectorRule[]`

`BuilderLogicConnectorRule`

- `id`
- `name`
- `trigger`: `onCreate | onUpdate | onWorkflowTransition`
- `sourceFieldKey`
- `operation`: `copy | set | add | subtract | multiply | sumLines`
- `targetFieldKey`
- `value`

The operation list is closed. UI must render select controls only.

## Implementation Slices

1. Mock adapter model
   - Add connector types and fixture defaults.
   - Add `logicConnector` to `BuilderPageBundle`.
   - Seed damaged stock page with one safe rule.
   - New created pages start disabled with zero rules.

2. Validation
   - Disabled connector returns no validation.
   - Enabled connector requires at least one rule.
   - Each rule requires name, trigger, operation, target.
   - `copy`, `add`, `subtract`, `multiply`, `sumLines` require source field.
   - Field references must exist and cannot target archived fields.
   - No free script/custom endpoint fields.

3. UI
   - Advanced remains collapsed by default.
   - Add `LogicConnectorBuilder` under Workflow Designer.
   - Include toggle, connector list, step builder labels: Trigger, Source, Operation, Target, Review.
   - Render dry-run before/after preview from fixture sample values.
   - Render read-only JSON for current rule.
   - Keep inventory and AI placeholders disabled.

4. Verification
   - Build frontend.
   - Check diff scope excludes backend and `ai_python`.
   - Browser verify desktop/mobile:
     - Advanced collapsed initially.
     - Connector opens after Advanced expand.
     - Toggle enables rules.
     - Removing all rules creates Logic validation error in `Kiem tra`.
     - Publish remains disabled while connector has error.
