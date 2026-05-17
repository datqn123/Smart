# Context Management System — Implementation Plan

## Goal
Design and implement a context management system for the AI chat that limits sessions to 10 turns, summarizes older messages into 8 key lines via an LLM, and retains the last 2 messages + summary.

## Constraints & Preferences
- Max 10 questions per session before triggering compaction
- Summarize old messages into exactly 8 key lines using an LLM
- Threshold: >10 turns → keep last 2, replace prior with summary
- Summarization handled by the existing model architecture
- Maintain compatibility with LangGraph `AgentState` and current checkpointing

---

## Phase 1: State & Settings

### 1.1 `state.py` — Add fields to `AgentState`
- `conversation_summary: str | None` — LLM-generated 8-line summary of older turns
- `turn_count: int` — Number of Human/AI turns in the conversation

### 1.2 `graph_settings.py` — Add configuration
| Setting | Default | Description |
|---------|---------|-------------|
| `context_compact_enabled` | `True` | Enable/disable context compaction globally |
| `context_compact_max_turns` | `10` | Max turns before triggering summarization |
| `context_compact_summary_lines` | `8` | Number of summary lines the LLM must produce |
| `context_compact_keep_last_turns` | `2` | Number of recent turns to keep verbatim |

---

## Phase 2: LLM Registry

### 2.1 `registry.py` — Add `"context_compact"` role
- Add `"context_compact"` to `_TEXT_ROLES` tuple
- Uses primary chat model for summarization (text-in, text-out)

---

## Phase 3: Context Compaction Node

### 3.1 `nodes/context_compact.py` — New node
**Logic:**
1. Count Human/AI message pairs (turns) from `state["messages"]`
2. If `turn_count <= max_turns` → pass through unchanged, increment `turn_count`
3. If `turn_count > max_turns` and no existing summary:
   - Extract messages excluding the last `keep_last_turns` pairs
   - Call LLM with `context_compact.md` system prompt
   - Store result as `conversation_summary`
4. If summary already exists → just increment `turn_count`
5. Return `{ "turn_count": N, "conversation_summary": "..." }`

### 3.2 `prompts/agents/context_compact.md` — System prompt
- Language: Vietnamese
- Instructs LLM to produce exactly 8 lines
- Focus on: user intent, key data points, decisions made, pending questions
- No markdown formatting, no preamble

---

## Phase 4: Graph Integration

### 4.1 `main_graph.py` — Insert node
- Add `context_compact` node after `domain_guard`, before `classify_intent`
- Flow: `domain_guard` → `context_compact` → `classify_intent` → ...

```
START → domain_guard → context_compact → classify_intent → ...
```

---

## Phase 5: Message Loader Updates

### 5.1 `intent.py` — `_messages_for_intent()`
- When `conversation_summary` exists:
  - Prepend `[Tóm tắt các lượt trước]\n<summary>` before recent messages
  - Take last 24 messages as before (summary + recent turns)

### 5.2 `chat_normal.py` — Message slicing
- When `conversation_summary` exists:
  - Prepend summary to the text block
  - Keep last 20 messages as before

### 5.3 `summarize.py` — `format_dialog_tail_for_sql()` usage
- Include summary in dialog tail for SQL pronoun resolution
- Format: `[Tóm tắt]\n<summary>\n\nRecent conversation:\n<dialog_tail>`

### 5.4 `chart_thread_context.py` — `format_prior_turns_for_chart()`
- Accept optional `summary` parameter
- Prepend summary when present, before prior turn pairs

---

## Phase 6: Runtime

### 6.1 `runtime.py` — `_build_state()`
- **Do NOT reset** `conversation_summary` in `_build_state()`
- **Do NOT reset** `turn_count` in `_build_state()`
- These fields should persist across turns via checkpoint
- Increment `turn_count` by 1 each new turn (handled in context_compact node)

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Summary stored in state, not replacing messages | Checkpoint history preserved; can reconstruct full thread if needed |
| Each node checks for summary independently | No single point of failure; nodes can adapt individually |
| Graceful fallback if LLM unavailable | Consistent with existing node patterns (domain_guard, intent stub) |
| Uses existing `SqliteSaver` | No new checkpoint infrastructure needed |
| Summary is Vietnamese | Matches app's primary language for user-facing content |

---

## Files to Create
- `ai_python/app/graph/nodes/context_compact.py`
- `ai_python/app/prompts/agents/context_compact.md`

## Files to Modify
- `ai_python/app/graph/state.py`
- `ai_python/app/config/graph_settings.py`
- `ai_python/app/llm/registry.py`
- `ai_python/app/graph/main_graph.py`
- `ai_python/app/graph/nodes/intent.py`
- `ai_python/app/graph/nodes/chat_normal.py`
- `ai_python/app/graph/nodes/summarize.py`
- `ai_python/app/graph/chart_thread_context.py`
- `ai_python/app/api/runtime.py`

---

## Validation
- Run `python run_test.py --group 13_multi_turn` to verify 10+ turn behavior
- Check that summary is generated at turn 11
- Verify last 2 messages remain intact
- Confirm SQL/chart nodes still resolve pronouns correctly with summary context
