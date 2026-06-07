# SRS-006 (upgrade/ai-python): Agentic AI v3.0 Planner-Brain Upgrade

- **Status**: DRAFT - SRS_WRITER stage
- **Date**: 2026-06-07
- **Mode**: SRS only
- **Scope**: AI runtime architecture upgrade from linear/route-driven agentic v1-v2 to Planner-driven Agentic AI v3.0
- **Source input**:
  - User decision: v3.0 must treat Planner/Reasoner as the brain; Harness is execution control, validation, policy, HITL, budget, audit.
  - Current target design: `docs/dev/requires/Design Agentic AI.md`
  - Supporting assets: `docs/ai-python/agentic-ai-supporting-assets/001_index.md`, K12, K15
  - Current runtime evidence: `ai_python/app/harness/plan_graph.py`, `ai_python/app/harness/orchestrator.py`, `ai_python/app/harness/tool_registry.py`, `ai_python/app/harness/policy.py`
  - Prior remediation SRS: `docs/upgrade/ai-python/srs/005_agentic-ai-remediation-plan.md`
  - External alignment references:
    - OpenAI Agents SDK: https://openai.github.io/openai-agents-python/ref/agent/
    - OpenAI Agents SDK guardrails: https://openai.github.io/openai-agents-python/guardrails/
    - Anthropic "Building effective agents": https://www.anthropic.com/engineering/building-effective-agents
    - Anthropic "Writing effective tools for agents": https://www.anthropic.com/engineering/writing-tools-for-agents
    - LangGraph overview: https://docs.langchain.com/oss/python/langgraph/overview
- **CodeGraph**: `status --json`, `context("Agentic AI v3 Planner brain Harness execution safety boundary SRS upgrade")`
- **Superpowers alignment**: brainstorming principles for architecture framing; no production code changes in this stage.
- **Revision 2026-06-07 (review-driven)**: added execution tiering / plan templates (FR-11), observation contract (FR-12), and clarification & in-flight plan state (FR-13); hardened K15 feedback weighting, RBAC source-of-truth, degraded-answer labeling, HITL commit idempotency, manifest prompt-surface split, and side-effect taxonomy; added traceability matrix and numeric eval gate.
- **Revision 2026-06-07b (review round 2)**: replan ownership clarified — Harness only emits `replan_required`, Planner decides (FR-6.1, AR-2); added `result_ref` data-flow so artifact builders get full data via Harness handle, never the Planner (FR-12.6–12.7, FR-2.3, manifest `produces`/`consumes`); locked plan-template provenance + version pinning/invalidation so fast-path cannot become a stale v1 route (FR-11.7–11.8); gave FR-13 its own acceptance (AC-18). OQ-1 reframed: "support both modes" is the settled architectural stance; only the implementation-first choice and tier/mode thresholds stay open for PO/Tech Spec.

---

## 1. Executive Summary

Agentic AI v1 in this project is route-driven: intent selects a mostly fixed path such as SQL query, chart, query table, catalog draft, or inventory draft. Agentic AI v2 introduced the idea of a Harness loop and PlanGraph, but the design language still risked treating Harness as the "brain".

Agentic AI v3.0 changes the ownership model:

- **Planner/Reasoner owns reasoning**: understand user goal, choose tools, create plan, read observations, decide whether to call another tool, replan, ask for clarification, or finalize.
- **Harness owns execution control and safety**: policy, RBAC, budget, HITL, timeout, cache, audit, validation gates, deterministic execution envelope.
- **Tools own scoped capabilities**: SQL, schema exploration, data validation, chart building, data table building, draft creation, answer composing, clarification.

The goal is not merely to add chart/table/draft features. The goal is to make all output artifacts the result of tool selection by an agentic planner, not fixed LangGraph routes.

---

## 2. Source Conflict and GAP Analysis

| ID | Evidence | GAP / Decision |
| :-- | :-- | :-- |
| GAP-1 | `docs/dev/requires/Design Agentic AI.md` section 2 states "Harness là não điều phối". | v3.0 supersedes this wording. Harness may run the loop, but must not own reasoning. Planner/Reasoner is the brain. |
| GAP-2 | `ai_python/app/graph/main_graph.py` has fixed route branches for chart, query table, catalog draft, inventory draft, and summarize. | This is v1 route-driven behavior. v3.0 must make artifact choice a planner/tool decision. |
| GAP-3 | `ai_python/app/harness/plan_graph.py` already has `PlanGraph`, `PlannerSubagent`, and `PlanExecutor`. | This is a useful foundation, but plan quality depends on richer tool manifests, tool schemas, observation contracts, and replan criteria. |
| GAP-4 | `ai_python/app/harness/tool_registry.py` currently exposes `ToolManifest(name, description, args_schema, has_hitl)`. | v3.0 planner needs richer metadata: capability, output artifact type, preconditions, when-to-use, when-not-to-use, risk, RBAC, cost, examples, eval coverage. |
| GAP-5 | `ai_python/app/harness/policy.py` maps only basic capabilities: data_read, draft_create, chat. | v3.0 needs policy coverage for artifact builder tools, HITL-only write flows, sensitive data controls, and tool-specific guardrails. |
| GAP-6 | K12 golden eval checks required/must-not tools, and K15 records tool success history. | v3.0 must use K12/K15 as first-class planner feedback and regression evidence, not just documentation. |
| GAP-7 | External agent frameworks separate model/agent reasoning, tools, guardrails, tracing, and evals. OpenAI Agents SDK frames agents around instructions/tools/guardrails/handoffs; Anthropic distinguishes fixed workflows from autonomous agents; LangGraph positions itself as low-level stateful agent/workflow infrastructure. | v3.0 must align with this separation: Planner/Reasoner decides, Harness/guardrails constrain and execute, tools expose ergonomic contracts, evals measure routing and outcomes. |
| GAP-8 | Section 1 states v3 should make "all output artifacts the result of tool selection by an agentic planner". Anthropic's cited guidance says use the simplest thing that works — workflows for predictable tasks, agents only when flexibility is needed. Most ERP intents (revenue this month, stock of product X, create receipt) are predictable and repetitive. | Routing every intent through a full planner LLM loop is an over-correction from v1: it regresses latency/cost on common intents. v3.0 must add an execution tier — cached plan templates / fast-path for high-confidence common intents, full planner reasoning only for novel/ambiguous/high-risk goals (FR-11). |

---

## 3. Industry Alignment

This SRS intentionally aligns Agentic AI v3.0 with current production agent patterns:

| Pattern | External alignment | v3.0 implication |
| :-- | :-- | :-- |
| Agent/model is configured with tools and guardrails. | OpenAI Agents SDK defines an agent as a model configured with instructions, tools, guardrails, handoffs, and context. | Planner/Reasoner is the reasoning owner; Harness supplies guardrail/runtime boundaries. |
| Guardrails must apply around tool calls, not only around the first input or final output. | OpenAI guardrails documentation distinguishes input, output, and tool guardrails; tool guardrails run around custom function-tool invocation. | Harness must check and validate every tool call before/after execution. |
| Workflows and agents are different. | Anthropic separates predictable workflows from agents that plan, use tools, observe results, and recover from errors. | v1 fixed LangGraph routes remain workflows; v3 Planner loop is the agentic layer. |
| Tool quality determines agent quality. | Anthropic's tool guidance emphasizes clear tool definitions, boundaries, examples, token-efficient responses, and eval-driven iteration. | Rich tool manifest and K12/K15 eval/history are required, not optional documentation. |
| Stateful agent infrastructure is not the whole architecture. | LangGraph provides persistence, HITL, memory, debugging, and deployment infrastructure for long-running workflows/agents. | LangGraph/runtime can support state/control, but v3 ownership must still separate Planner, Harness, and tools. |

This section supersedes any older project wording that describes Harness as the "brain". Harness may host or run the loop, but reasoning and next-action selection belong to Planner/Reasoner.

## 4. Scope

### In Scope

- Planner-brain architecture and ownership model.
- Tool registry contract expansion.
- Plan/replan behavior for data query, chart, data table, input table draft, and final answer.
- Artifact system for `answer`, `chart`, `data_table`, `input_table_draft`, and `summary_card`.
- Harness safety responsibilities: RBAC, tenant scope, budget, HITL, timeout, cache, audit, validation.
- Tool selection requirements using K1-K15 supporting assets.
- Evaluation requirements using K12 and K15.

### Out of Scope

- Direct database writes by AI without user confirmation.
- Replacing Spring as source of truth for RBAC, transactions, or persistence.
- Changing frontend visual design in this SRS stage.
- Implementing code in this SRS stage.
- Adding non-ERP general knowledge answering.

---

## 5. Definitions

| Term | Definition |
| :-- | :-- |
| Planner / Reasoner | LLM-backed decision component that chooses tools, builds plans, replans, asks clarification, and finalizes. |
| Harness | Deterministic execution and safety boundary around planner decisions and tool calls. |
| Tool | Scoped capability with input/output schema and policy requirements. |
| Artifact | Structured UI-ready output produced by tools: answer, chart, data table, input table draft, summary card. |
| Observation | Sanitized result of a tool call, visible to Planner for next decision. |
| PlanGraph | Explicit DAG of tool calls with dependencies, input bindings, expected outputs, and stopping criteria. |
| Plan Template | A previously validated PlanGraph promoted for reuse on a normalized intent key, runnable without invoking the planner LLM. |
| Execution Tier | The pre-planner decision of whether a turn runs a cached plan template (fast-path) or falls through to full Planner reasoning. |
| Observation Contract | Fixed schema for what a tool returns to Planner: enough fidelity to reason (schema, counts, aggregates, bounded masked sample) without leaking full result sets or sensitive data. |

---

## 6. Architecture Ownership

### AR-1: Planner Is the Brain

Planner/Reasoner owns:

- Goal interpretation.
- Tool choice.
- PlanGraph generation.
- Replan after failure, empty result, bad validation, or artifact mismatch.
- Clarification decision when ambiguity blocks safe execution.
- Finalization decision when required data and artifact obligations are satisfied.

### AR-2: Harness Is the Execution and Safety Boundary

Harness owns:

- Policy and RBAC enforcement before every tool call.
- Tenant and user context propagation.
- Budget controls: max steps, token, cost, wall-clock timeout.
- HITL pause/resume and confirmation gate for draft/write flows.
- Tool-call audit, trace, metrics, asset version logging.
- Cache for deterministic and tenant-safe tool outputs.
- Validation of tool input/output contracts.
- Sanitization before observations return to Planner.
- Emitting a structured `replan_required` signal on failure or failed expectation — the replan/clarify/degrade/stop decision itself belongs to Planner (AR-1), not Harness.

### AR-3: Tools Are Scoped Capabilities

Tools must not own broad planning. Each tool must expose one bounded capability, for example:

- `schema_explore`
- `sql_query` or `sql_subagent`
- `data_validator`
- `chart_builder`
- `data_table_builder`
- `input_table_draft_builder`
- `catalog_draft`
- `inventory_draft`
- `answer_composer`
- `clarify_user`

---

## 7. Target v3 Runtime Flow

```text
user goal
  -> Planner.decide(goal, memory, tools, policy hints, K assets, K15 history)
  -> Harness.check(decision)
  -> Harness.run_tool(tool, args)
  -> Harness.validate_output(tool_result)
  -> sanitized observation
  -> Planner decides next step
  -> repeat until done, clarify, HITL pending, or degraded final answer
```

The v3 loop must support both:

- **Reactive loop**: one decision at a time, useful for ambiguous or high-risk tasks.
- **PlanGraph DAG**: multi-step plan with parallel branches, useful for known report workflows.

The selected mode must be a planner/runtime decision based on task risk, ambiguity, and expected cost.

---

## 8. Functional Requirements

### FR-1: Planner-Brain Contract

- FR-1.1: Planner must receive the current user goal, memory summary, allowed tools, policy hints, relevant K asset versions, and K15 success-history summary.
- FR-1.2: Planner decisions must be structured, not free-form text.
- FR-1.3: Planner must support actions: `call_tool`, `plan_graph`, `clarify`, `final_answer`, and `degrade_final_answer`.
- FR-1.4: Planner must not be allowed to invoke tools absent from the registry.
- FR-1.5: Planner must include reasoning text for trace only; reasoning must not be exposed to end users.
- FR-1.6: A `degrade_final_answer` action must be explicitly labeled to the end user as incomplete and must state what is missing or unverified. It must never be presented as a complete, authoritative answer — partial financial/inventory data shown as complete is a business-decision hazard.

### FR-2: Rich Tool Manifest

Each tool manifest must include:

- `name`
- `description`
- `capability`
- `args_schema`
- `output_schema`
- `output_artifact_types`
- `has_hitl`
- `preconditions`
- `when_to_use`
- `when_not_to_use`
- `risk_level`
- `rbac_required`
- `budget_class`
- `cache_policy`
- `eval_cases`
- `examples`
- `side_effect_class` (`read_only` | `idempotent_write` | `non_idempotent_write`)
- `produces` (output artifact / result types this tool emits)
- `consumes` (accepted input artifact types / `result_ref` kinds)
- `result_ref_policy` (`inline` vs `result_ref` handle for large outputs)
- `observation_schema` (the contract shape returned to Planner, per FR-12)

Manifest field governance:

- FR-2.1: Each field must be classified as **planner-visible** (injected into the planner prompt: `name`, `description`, `capability`, `args_schema`, `output_artifact_types`, `when_to_use`, `when_not_to_use`, condensed `examples`) or **governance-only** (registry/audit/eval use: full `eval_cases`, `output_schema`, `cache_policy`, internal `preconditions`). The planner prompt must not be flooded with governance-only metadata.
- FR-2.2: `side_effect_class` drives two Harness behaviors: cache eligibility (`cache_policy`) and replan/retry safety (FR-6.6). A tool with side effects must declare it honestly.
- FR-2.3: Manifest must declare `produces` and `consumes` so Planner can build a valid PlanGraph where node A's output type feeds node B's input, instead of guessing compatibility. Tools emitting large data must set `result_ref_policy` to handle-based so the binding passes a `result_ref` (FR-12.6), not inline data.

### FR-3: Artifact Selection

- FR-3.1: Planner must decide whether the user needs only an answer, a chart, a data table, an input table draft, or a summary card.
- FR-3.2: Chart/data table/input draft must be emitted as structured artifacts, not markdown embedded in final answer.
- FR-3.3: Artifact builders must be tools, not fixed route-only nodes.
- FR-3.4: `answer_composer` must summarize observations and reference emitted artifacts without duplicating large tables in text.
- FR-3.5: If chart requirements cannot be satisfied, Planner must replan to data table or summary answer when safe.

### FR-4: Data Query Behavior

- FR-4.1: For scalar questions, Planner should choose `sql_query -> data_validator -> answer_composer`.
- FR-4.2: For "liệt kê", "danh sách", "top", or row-level questions, Planner should include `data_table_builder`.
- FR-4.3: For trend/comparison/distribution requests, Planner should include `chart_builder`.
- FR-4.4: For ambiguous time/entity filters, Planner must call `clarify_user` before SQL when confidence is below threshold.
- FR-4.5: SQL must remain read-only and tenant scoped.

### FR-5: Input Table Draft Behavior

- FR-5.1: User requests to create catalog/inventory records must produce input table draft artifacts, not direct writes.
- FR-5.2: Draft tools must return HITL payloads with resume token and editable fields.
- FR-5.3: Commit must require explicit user confirmation after review.
- FR-5.4: Staff or unauthorized roles must be denied before draft creation. The **live backend/JWT permission claim is the single source of truth**; K6 is advisory for planning hints only and must never override or substitute for the live claim. On conflict or a missing claim, fail closed.
- FR-5.5: Planner must not call SQL query just because the user asks to create a draft, unless entity resolution or validation requires read-only lookup.
- FR-5.6: Draft commit after user confirmation must be idempotent on the resume token: a replayed token or double confirmation must not create duplicate records. Harness must use the existing idempotency guard.

### FR-6: Replan Behavior

- FR-6.1: Harness must emit a structured `replan_required` observation (with sanitized failure reason) when a tool fails, output expectations fail, policy blocks, data validator fails, or an artifact builder cannot render. The next-step decision — replan, clarify, degrade, or stop — belongs to Planner (AR-1); Harness must not select the next plan itself.
- FR-6.2: Planner must receive sanitized failed node details, not raw stack traces or SQL internals.
- FR-6.3: Planner may replace a failed tool, add missing prerequisite tools, ask clarification, or degrade the response.
- FR-6.4: Replan count must be bounded.
- FR-6.5: Duplicate tool calls with identical args and identical failure fingerprint must be short-circuited.
- FR-6.6: Automatic replan/retry is permitted only for `read_only` or `idempotent_write` tools (FR-2.2). A `non_idempotent_write` tool must not be silently retried; its failure must surface to Planner for an explicit new decision.

### FR-7: Harness Policy and Validation

- FR-7.1: Harness must check policy before every tool call.
- FR-7.2: Harness must validate tool input/output schema.
- FR-7.3: Harness must enforce role, tenant, HITL, and budget constraints even when Planner requests an unsafe call.
- FR-7.4: Harness must sanitize observations before sending them back to Planner.
- FR-7.5: Harness must log every tool call with correlation id and asset versions.

### FR-8: Knowledge Asset Usage

- FR-8.1: Planner must use K1, K8, K13, and K15 for plan selection. K15 bias must weight `degraded` and `hitl_pending` outcomes strictly lower than clean `success`, so a plan that only ever "succeeds degraded" is not reinforced as preferred. On cold start (no K15 history for an intent), Planner must fall back to manifest `when_to_use` and default safe plans, not to an empty-history shortcut.
- FR-8.2: SQL/data tools must use K1, K2, K3, K5, K7, and K8 where relevant.
- FR-8.3: Chart builder must use K9 and K14.
- FR-8.4: Draft tools must use K6 and K11.
- FR-8.5: Eval and observability must use K12 and K15.
- FR-8.6: Harness trace must log `asset_id + version` for all used assets with `must_log_version_in_trace=true`.

### FR-9: Observability and Success History

- FR-9.1: After every turn, runtime must append a K15-compatible event for success, failure, degraded, or HITL pending outcomes.
- FR-9.2: K15 records must include plan graph hash, tools executed, replan count, HITL count, latency, cost, budget status, and failure detail.
- FR-9.3: Planner must receive aggregate K15 history, not raw user questions or raw SQL.
- FR-9.4: Observability must expose tool route accuracy against K12 expected tools.
- FR-9.5: K15 outcome records must distinguish clean `success` from `degraded` (budget-exhausted, dedup-stopped, empty-after-retry) and `hitl_pending`, so the feedback signal in FR-8.1 can down-weight degraded plans rather than treating any non-failure as good.

### FR-10: Agentic Tool Ergonomics

- FR-10.1: Tool names and argument names must be obvious to the Planner and must not require hidden ordering knowledge.
- FR-10.2: Similar tools must have clear boundaries in `when_to_use` and `when_not_to_use`.
- FR-10.3: Tool outputs must return concise, meaningful observations for the Planner, not raw infrastructure dumps.
- FR-10.4: Every high-risk or commonly confused tool pair must have eval cases that measure correct tool selection.
- FR-10.5: Tool documentation must be treated as prompt surface and reviewed when agent routing fails.

### FR-11: Execution Tiering and Plan Templates

- FR-11.1: Runtime must support an execution tier ahead of full planner reasoning. High-confidence, low-risk, common intents may run a cached **plan template** (a previously validated PlanGraph) without invoking the planner LLM.
- FR-11.2: Novel, ambiguous, or high-risk goals must fall through to full Planner reasoning (FR-1).
- FR-11.3: A plan hash that succeeds cleanly (FR-9.5) repeatedly for a normalized intent key may be **promoted** to a reusable plan template; a template that later degrades or fails must be demoted.
- FR-11.4: Plan templates remain under full Harness safety (policy, RBAC, budget, validation, audit) exactly like planner-generated plans. Tiering is an optimization, never a safety bypass.
- FR-11.5: The execution tier that handled a turn (and why) must be observable in the trace.
- FR-11.6: Tier-selection thresholds, and the reactive-vs-PlanGraph choice within the planner, remain governed by OQ-1 and are deferred to the Tech Spec; this FR mandates the tier exists, not its exact thresholds.
- FR-11.7: A plan template may only be created by promoting a Planner-generated plan that has passed eval (K12). Templates must never be hand-authored as fixed routes — that would reintroduce v1 routing under a new name.
- FR-11.8: Each template must pin `manifest_version`, the K asset versions it relied on, and the `policy_version`. Any change to a referenced tool contract, schema, RBAC, or policy must invalidate (demote) the template and force a fresh Planner pass. A template must never run against a contract version it was not validated for.

### FR-12: Observation Contract

- FR-12.1: Every tool observation returned to Planner must follow a fixed observation schema, not raw tool output.
- FR-12.2: For data results, the observation must give Planner enough to reason — column schema, `row_count`, key aggregate stats, and a bounded masked sample of at most N rows — while never returning the full result set.
- FR-12.3: Observations must never contain raw PII, credentials, bearer tokens, raw SQL internals, stack traces, or provider errors (consistent with NFR-3/NFR-8).
- FR-12.4: When data is truncated or masked, the observation must carry an explicit `truncated`/`masked` flag so Planner knows the view is partial.
- FR-12.5: Sanitization must not strip the structural signals (schema, counts, types) the Planner needs for artifact selection (FR-3). Fidelity-vs-sanitization is balanced by this contract, not left to each tool's discretion.
- FR-12.6: Full tool result data must be held by Harness and addressed by an opaque `result_ref` handle. Planner sees only the observation (schema, counts, aggregates, bounded sample, `result_ref`) — never the full data.
- FR-12.7: Downstream tools that need full data (e.g. `chart_builder`, `data_table_builder`) must consume it by passing the `result_ref` back through Harness, which resolves it under policy/RBAC/tenant scope. Full result data must never round-trip through the Planner prompt, and artifacts must never be rendered from the truncated sample.

### FR-13: Clarification and In-flight Plan State

- FR-13.1: When Planner issues `clarify` mid-plan, the runtime must deterministically define whether the in-flight PlanGraph is paused-and-resumed or discarded-and-replanned after the user responds; this must not be tool-specific.
- FR-13.2: Clarification pause/resume must reuse the durable pending-state mechanism (same store family as HITL) so a clarify that spans turns survives process restart.
- FR-13.3: A resumed clarify must not silently re-execute already-completed, side-effecting plan nodes (consistent with FR-6.6 and FR-5.6).

---

## 9. Non-Functional Requirements

- NFR-1: All planner and tool decisions must be deterministic enough for test fixtures using fake LLM/tool clients.
- NFR-2: P0 eval cases in K12 must pass before v3 can be enabled for production users.
- NFR-3: Tool manifest generation must not leak credentials, raw bearer tokens, or raw PII.
- NFR-4: Planner should prefer lower-cost tools and cached deterministic outputs when they satisfy the goal.
- NFR-5: p95 successful data-query turn should stay within the SLO defined by K12/K15 for equivalent v2 cases.
- NFR-6: Frontend SSE event contracts must remain backward compatible during migration.
- NFR-7: Legacy v1/v2 route-driven mode must remain available behind a feature flag until v3 eval gates pass.
- NFR-8: Guardrail failures must be observable as structured events without exposing raw stack traces, SQL, provider errors, or reasoning text to users.
- NFR-9: Tool descriptions, examples, and eval cases must be updated together when a tool contract changes.
- NFR-10: The planner prompt must stay within a defined token budget; only planner-visible manifest fields (FR-2.1) plus summarized memory/K15 may be injected. Manifest growth must not silently inflate planner cost.
- NFR-11: Tool-route accuracy against K12 expected tools must meet a numeric threshold (defined in the QA Spec) before v3 rollout; rollout is blocked if measured accuracy drops below it.

---

## 10. Evaluation Requirements

### ER-1: Golden Eval Tool Routing

K12 expected `required_tools` and `must_not_tools` must be enforced for v3. Passing requires:

- Required tools all called.
- Forbidden tools never called.
- Tool output satisfies declared artifact expectations.
- Permission denial cases do not call protected tools.

Route accuracy must meet the numeric threshold defined in the QA Spec (NFR-11); a measured drop below it blocks rollout.

### ER-2: New v3 Eval Cases

Add eval cases for:

- User asks for a chart but data is not chartable: replan to data table or summary.
- User asks for a list: emits `data_table` artifact and answer summary.
- User asks to create inventory receipt: emits input table draft, no commit before HITL.
- Planner initially chooses wrong tool: validator failure triggers replan.
- Policy blocks sensitive finance request from staff: no data tool leak, answer uses permission template.
- K15 history biases planner away from a plan hash with repeated policy blocks.

### ER-3: Trace Assertions

Every eval run must assert:

- Planner action sequence.
- Tool call sequence.
- Replan count.
- HITL count.
- Artifact events.
- K asset versions.
- No raw SQL/stack trace/provider error in final answer.

### ER-4: Tool Ergonomics Evaluation

For each registered v3 tool, evaluation must include at least:

- One expected-use prompt.
- One must-not-use prompt.
- One ambiguous prompt that should trigger clarification or a safer alternative.
- One failure/replan scenario.
- One assertion that the observation returned to Planner is concise and actionable.

---

## 11. Acceptance Criteria

- AC-1: SRS/Tech/QA docs define Planner as reasoning owner and Harness as execution/safety owner.
- AC-2: Tool manifest contract includes all required v3 metadata fields.
- AC-3: Planner can choose `answer`, `chart`, `data_table`, or `input_table_draft` artifacts through tools rather than fixed routes.
- AC-4: Harness blocks unauthorized tool calls even when Planner requests them.
- AC-5: Replan occurs after failed output expectation or validation failure and is bounded.
- AC-6: HITL draft creation never commits without explicit user confirmation.
- AC-7: K12 eval route assertions pass for required/must-not tools.
- AC-8: K15 success history is appended after every turn and can be queried by normalized intent key.
- AC-9: Legacy route-driven mode remains feature-flagged as rollback.
- AC-10: Frontend receives backward-compatible SSE artifact events: `chart`, `data_table`, `draft`, `inventory_draft`, `clarify`, `delta`, `done`.
- AC-11: Tool guardrail behavior is covered around each high-risk custom tool call, not only at request input or final answer output.
- AC-12: Tool selection evals prove Planner can distinguish `answer_composer`, `data_table_builder`, `chart_builder`, and `input_table_draft_builder`.
- AC-13: Common, low-risk intents can be served by a cached plan template without a planner LLM call, while still passing all Harness safety gates.
- AC-14: Observations returned to Planner follow the observation contract: bounded/masked sample with schema and counts, never the full result set (full data flows only via a Harness-held `result_ref` consumed by downstream tools, never through the Planner), never raw PII/SQL/stack traces.
- AC-15: Degraded final answers are explicitly labeled to the user as incomplete and state what is missing.
- AC-16: HITL draft commit is idempotent: a replayed resume token or double confirmation creates no duplicate records.
- AC-17: Role/capability decisions use the live backend/JWT claim as the single source of truth and fail closed; K6 never overrides it.
- AC-18: A clarification that spans turns survives process restart, resumes deterministically (paused-and-resumed or replanned per FR-13.1), and never re-executes already-completed side-effecting plan nodes.

### 11.1 Requirement Traceability (FR -> AC)

| FR | Covered by |
| :-- | :-- |
| FR-1 Planner-Brain | AC-1, AC-15 |
| FR-2 Rich Tool Manifest | AC-2 |
| FR-3 Artifact Selection | AC-3, AC-10, AC-12 |
| FR-4 Data Query | AC-7, AC-10 |
| FR-5 Input Table Draft | AC-6, AC-16, AC-17 |
| FR-6 Replan | AC-5 |
| FR-7 Policy and Validation | AC-4, AC-11 |
| FR-8 Knowledge Asset Usage | AC-7, AC-8 |
| FR-9 Observability and History | AC-8 |
| FR-10 Tool Ergonomics | AC-12 |
| FR-11 Execution Tiering | AC-13 |
| FR-12 Observation Contract | AC-14 |
| FR-13 Clarify and In-flight State | AC-6, AC-18 |

---

## 12. Open Questions

| ID | Question | Blocker | Default Decision |
| :-- | :-- | :--: | :-- |
| OQ-1 | Which mode does v3 implement first, and what tier/mode-selection thresholds apply? (Architecture stance "support both" is already settled.) | No (architecture) / Tech Spec (impl-first) | Architecture = support both: reactive for ambiguity/high risk, PlanGraph for known report workflows. **Open for PO/Tech Spec**: which mode to build first and the selection thresholds. Left open per PO. |
| OQ-2 | Should tool names keep v1 names (`sql_query`) or shift to asset names (`sql_subagent`)? | No | Keep current runtime names initially; manifest may expose alias/description for planner. |
| OQ-3 | Should `summary_card` be a separate artifact now? | No | Include in v3 contract, but implementation may defer until chart/table/answer tools are stable. |
| OQ-4 | Where should K15 history be persisted first? | Yes for coding | Default to a local append-only store for tests, with a production store decision in Tech Spec. |
| OQ-5 | Which claim wins when K6 and the live JWT disagree on role/capability? | Yes for coding | Live backend/JWT claim is the single source of truth; K6 is advisory for planning hints only and never overrides it; fail closed if the live claim is unavailable. (See FR-5.4.) |
| OQ-6 | Where do promoted plan templates live, and what promote/demote thresholds apply? | Yes for coding | Default to the same append-only/local store family as K15 for tests; production store and thresholds decided in Tech Spec. (See FR-11.3.) |
| OQ-7 | What is the max sample size N and stat set for the observation contract? | No | Default to a small masked sample (e.g. <= 20 rows) plus schema, row_count, and key aggregates; exact N tuned in Tech Spec/QA. (See FR-12.2.) |

---

## 13. Risks and Mitigations

| Risk | Level | Mitigation |
| :-- | :-- | :-- |
| Planner over-calls tools and increases cost. | High | Harness step/cost budgets, cache, K15 plan success history, minimal-plan prompt. |
| Planner chooses unsafe tool. | High | Harness policy blocks pre-tool; protected tools require role/capability and HITL. |
| Tool manifest too vague, leading to wrong tool choice. | High | Add when-to-use/when-not-to-use, examples, eval IDs, and output schemas. |
| Replan loops without progress. | High | Max replan, duplicate fingerprint short-circuit, degraded final answer. |
| Frontend breaks due to new artifacts. | Medium | Keep existing SSE event names; add new artifacts behind feature flag. |
| K assets drift from backend schema/RBAC. | Medium | Enforce P0/P1 gates from supporting asset index before v3 rollout. |
| Tool documentation becomes stale and Planner misroutes. | High | Treat manifest/docs/evals as one contract; block rollout when eval route accuracy drops. |
| Full planner loop on predictable common intents regresses latency/cost vs v2. | High | Fast-path / cached plan templates (FR-11); reserve full planner for novel/ambiguous/high-risk goals. |
| K15 feedback poisoning: degraded plans reinforced as preferred. | High | Down-weight `degraded`/`hitl_pending` outcomes (FR-8.1, FR-9.5); demote degrading templates (FR-11.3). |
| Observation over-sanitized (planner cannot reason) or under-sanitized (leak). | High | Fixed observation contract balancing fidelity and safety (FR-12). |
| RBAC drift between K6 and live JWT claim. | High | Live claim is single source of truth; K6 advisory only (FR-5.4, OQ-5). |
| Duplicate writes from replayed HITL confirmation. | Medium | Idempotent commit on resume token (FR-5.6); no silent retry of non-idempotent writes (FR-6.6). |

---

## 14. Rollout

Open Questions marked "Yes for coding" (OQ-4, OQ-5, OQ-6) are blockers and must be resolved before the Contract phase begins.

1. **Docs phase**: SRS -> Tech Spec -> QA Spec for v3.
2. **Contract phase**: enrich tool manifest and define artifact schemas.
3. **Runtime phase**: enable v3 planner loop behind feature flag.
4. **Eval phase**: run K12 plus new v3 eval cases; append K15 history.
5. **Beta phase**: enable for owner/admin only.
6. **Production phase**: enable role-gated usage after policy, HITL, and regression metrics pass.

---

## 15. PO Sign-off

- **Product owner decision needed**: approve v3 ownership model: Planner/Reasoner is the brain; Harness is execution control and safety boundary.
- **Engineering decision needed**: with "support both modes" settled as the architecture, choose which to build first — reactive loop first or PlanGraph first — and the tier/mode-selection thresholds (OQ-1, Tech Spec input).
- **Engineering decision needed**: approve adding an execution tier (fast-path / cached plan templates per FR-11) so predictable common intents skip the full planner LLM. This is orthogonal to OQ-1 (which is about reasoning mode inside the planner) and does not pre-resolve it.
- **Security decision needed**: confirm backend/JWT claim source for role/capability, and confirm K6 is advisory-only (FR-5.4).
