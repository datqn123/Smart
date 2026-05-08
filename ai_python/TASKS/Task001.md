# Task001 — app-layer-refactor
- SRS: [`SRS_AI_Task001_app-layer-refactor.md`](../docs/srs/SRS_AI_Task001_app-layer-refactor.md)
- PRD: [`PRD_app-layer-refactor.md`](../docs/prd/PRD_app-layer-refactor.md)
- Branch: feature/ai-task001
- Owner chain: AI_DEVELOPER → AI_CODE_REVIEWER → (AI_BRIDGE) → AI_TESTER → AI_DOC_SYNC
- DoD overall: AC-1..AC-8 SRS Approved

## Unit
- [ ] Unit-T001-1 — SSE helper tests (PRD U1) | DoD: AC-4 | depends: -
- [ ] Unit-T001-2 — Config loader tests (PRD U2) | DoD: AC-4 | depends: -
- [ ] Unit-T001-3 — MKP streaming wrapper unit (PRD U3) | DoD: AC-2 | depends: -

## Feature
- [ ] Feature-T001-1 — Layout Option B + move code (PRD F1) | DoD: AC-3,AC-5 | depends: Unit-T001-3
- [ ] Feature-T001-2 — Wire main + routers (PRD F2) | DoD: AC-3 | depends: Feature-T001-1
- [ ] Feature-T001-3 — tools/stream_chat + thin router (PRD F3) | DoD: AC-2 | depends: Feature-T001-2

## Eval
- [ ] Eval-T001-1 — Smoke API health + stream (PRD E1) | DoD: AC-1,AC-2 | depends: Feature-T001-3
- [ ] Eval-T001-2 — TTFB baseline + regression note (PRD E2) | DoD: AC-6 | depends: Feature-T001-3
- [ ] Eval-T001-3 — Coverage + ruff + mypy gate (PRD E3) | DoD: AC-7,AC-8 | depends: Feature-T001-3

## Risks / Notes
- Design doc dùng tên event `token`; slice giữ `delta` theo PRD — tránh drift consumer/relay khi đổi tên sau này.
- Chưa đo TTFB baseline pre-refactor; cần số liệu trước khi đóng AC-6/NFR-1.
