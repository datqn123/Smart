# TECH_SPEC-026 — AI Chat UI Upgrade

## Input

- SRS: `docs/frontend/srs/022_ai-chat-ui-upgrade.md`
- Source: `frontend/mini-erp/src/features/ai/pages/ChatBotPage.tsx`

## Scope

- Frontend only.
- Keep SSE stream, TTS hook contract, artifact cards, API modules, and AI types unchanged.
- Edit target: `ChatBotPage.tsx`.

## Horizontal Analysis

- `conversationId` currently lives in component state and is also mirrored to `sessionStorage`; any reset flow must update both sources or the next stream will keep using the stale id.
- Assistant actions are currently gated by global `isTyping`; adding copy must avoid exposing controls on the actively streaming assistant message while keeping completed messages actionable.
- `progressText` is currently rendered near the input. Moving it into the typing bubble must not hide transcribing/recording states, which are separate UX states.
- Legacy image/paperclip actions are local-only UI affordances. Removing them from the toolbar does not require deleting `image` message support from `ChatMessage`; keep scope local to this page.

## Implementation Slices

1. Refresh visual primitives in `ChatBotPage.tsx`.
   - Gradient header avatar.
   - Gradient user bubble.
   - Assistant bubble with left accent border.
   - Stronger typing indicator colors.
   - Mode pills with icons.

2. Add local interaction state.
   - `copiedMessageId` with 1.5s reset timer.
   - `conversationId` setter-backed reset helper using `sessionStorage`.

3. Introduce controlled reset flow.
   - Header button `Cuộc hội thoại mới`.
   - `window.confirm`.
   - Abort active stream, stop TTS/recording timers, clear progress/input, reset messages to welcome card, generate fresh conversation id.

4. Render special welcome card.
   - Message `id === "1"` becomes a dedicated intro card.
   - No timestamp, no assistant actions.

5. Remove misleading toolbar actions.
   - Hide upload/attachment buttons from the input toolbar.
   - Preserve send/mic behavior.

## Files For Coding Agent

- Read/Edit: `frontend/mini-erp/src/features/ai/pages/ChatBotPage.tsx`
- Add tests: `frontend/mini-erp/src/features/ai/pages/ChatBotPage.test.tsx`
- Read-only reference:
  - `frontend/mini-erp/src/features/ai/types.ts`
  - `frontend/mini-erp/src/features/ai/hooks/useTextToSpeech.ts`
  - `frontend/mini-erp/src/features/ai/api/aiChatSse.ts`

## Verification Targets

- Render welcome card and header reset button.
- Ensure upload/attachment actions are absent.
- Ensure assistant copy action appears only for completed assistant messages.
- Ensure clear-chat regenerates `sessionStorage` conversation id and removes prior messages.

## Readiness

`READY_FOR_CODING`

Superpowers: writing-plans
CodeGraph: unavailable, used source-read fallback
