# Tech Spec - Custom Builder Basic Workflow Designer

> Agent: TECH_SPEC_WRITER  
> SRS: `docs/frontend/srs/012_custom-builder-settings-first-ui-redesign.md`  
> Superpowers alignment: writing-plans, test-driven-development, verification-before-completion.

## Scope

Implement a basic workflow designer inside the collapsed `Nâng cao` settings section:

- Workflow on/off toggle.
- State designer with key, label, type.
- Transition designer with from/to states, label, role.
- Workflow validation surfaced through the existing `Kiểm tra` section.
- Lightweight workflow preview in settings.

Out of scope: backend workflow execution, connector, inventory, AI, LangGraph/Harness runtime work, `ai_python`.

## Data Model

Extend frontend mock adapter only:

- `BuilderWorkflowDefinition.enabled`
- `states[]`: `id`, `key`, `label`, `type`
- `transitions[]`: `id`, `label`, `fromStateKey`, `toStateKey`, `allowedRoles`

Validation adds `section: "workflow"` errors/warnings.

## UI Design

Keep `Nâng cao` collapsed by default. When opened, show one workflow block first, then disabled placeholders for connector/inventory/AI. The workflow block is settings-first: toggle, state list, transition list, preview. No full-screen graph canvas.

## Verification

- Build frontend.
- Diff check.
- Browser verify advanced collapsed default, workflow toggle, validation in `Kiểm tra`, and desktop/mobile screenshots.
