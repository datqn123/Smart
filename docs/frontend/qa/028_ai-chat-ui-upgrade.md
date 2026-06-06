# TEST_PLAN-028 — AI Chat UI Upgrade

## Input

- Tech Spec: `docs/frontend/tech_lead/026_ai-chat-ui-upgrade.md`
- SRS: `docs/frontend/srs/022_ai-chat-ui-upgrade.md`

## QA Scope

- Frontend UI behavior in `ChatBotPage.tsx`.
- No API/backend validation changes.

## Horizontal QA Analysis

- Reset chat must update both rendered messages and `sessionStorage` conversation id; testing only the DOM would miss stale stream-context regressions.
- Copy action must not show on the welcome card or on the still-streaming assistant message.
- Progress relocation must not interfere with recording/transcribing banners, which remain in the input area.

## P0 Cases

1. Welcome state renders as a special intro card.
   - Expect title `Xin chào! 👋`.
   - Expect no copy button on the welcome card.

2. Legacy upload affordances are removed.
   - Expect no image/attachment buttons in the input toolbar.

3. Completed assistant message exposes copy action.
   - Simulate `startAiChatPostStream`.
   - Emit `onDeltaFull`, then `onDone`.
   - Expect assistant content plus `Sao chép tin nhắn`.
   - Click copy and assert clipboard receives `msg.content`.

4. Clear chat resets session.
   - Seed `sessionStorage` with an existing conversation id.
   - Confirm header action.
   - Expect previous streamed content removed.
   - Expect `sessionStorage["ai_chat_conversation_id"]` replaced with a fresh UUID.

## P1 Cases

1. Typing indicator shows colored dots and in-bubble progress text when `progressText` is present.
2. Mode pills show icon + label and still switch interaction mode while idle.
3. TTS button remains available for completed assistant messages when supported.

## Test Files

- Add: `frontend/mini-erp/src/features/ai/pages/ChatBotPage.test.tsx`

## Readiness

`QA_READY_FOR_CODING`

Superpowers: test-driven-development
CodeGraph: unavailable, used source-read fallback
