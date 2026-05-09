---
name: orchestrate
description: Auto-run AI agent chain (BA → PM → TECH_LEAD → DEV → CODE_REVIEWER → BRIDGE → TESTER → DOC_SYNC) for an ai_python feature. HITL only at AI_PLANNER's option A/B/C. Auto-loop on Block max 3 rounds. Budget cap escalate.
---

# /orchestrate — Auto-runner cho ai_python

> Driver thực thi chuỗi role theo [`ai_python/AGENTS/WORKFLOW_RULE.md`](../../ai_python/AGENTS/WORKFLOW_RULE.md) + [`ai_python/AGENTS/AGENT_REGISTRY.md`](../../ai_python/AGENTS/AGENT_REGISTRY.md).
>
> Mục tiêu: **tối ưu token**. Driver **không nhúng** nội dung `*_AGENT_INSTRUCTIONS.md` vào prompt; chỉ đưa **đường dẫn file** để subagent tự đọc (và tự đọc artifact input theo path).

## Tham số (parse từ user message)

```text
/orchestrate Task=<id?> Brief="<mô tả ngắn>" [Mode=run|dry-run] [Budget=<n=20>] [SkipPlanner=false]
```

- `Task` (optional): nếu rỗng → AI_PM tự cấp ID Task tiếp theo.
- `Brief`: mô tả tính năng cho AI_PLANNER (bắt buộc nếu `SkipPlanner=false`).
- `Mode`: `run` (mặc định, launch subagent thật) | `dry-run` (in plan từng bước, không launch).
- `Budget`: trần số lần invoke subagent. Mặc định 20. Vượt → escalate.
- `SkipPlanner`: nếu PRD đã có sẵn cho task → bỏ qua planner.

## Driver state (tối thiểu; giữ trong message history)

```yaml
task_id: <Task???>
task_slug: <slug>
branch: feature/ai-task<???>
artifacts: { prd: <path?>, srs: <path?>, task_file: <path?>, adr: <path?> }
reports: { cr: <path?>, bridge: <path?>, tester: <folder?>, doc_sync: <path?>, audit: <path?> }
loops: { cr: 0, bridge: 0, tester: 0 }
budget_used: 0
budget_cap: 20
current_gate: G-AI-PLAN
```

Update state sau mỗi subagent return; chỉ in **1–2 dòng** trạng thái (gate + budget + loop counters).

## Quy tắc tuyệt đối (không vi phạm)

1. **HITL duy nhất ở AI_PLANNER**: sau khi planner trả option A/B/C → DỪNG, in prompt yêu cầu Owner gõ `A` / `B` / `C` / `pick optimal`. **Không** hỏi user ở role nào khác.
2. **STOP rules**: theo `WORKFLOW_RULE.md` §3.1 và STOP rules trong từng role instruction. Match → escalate Owner ngay, không loop.
3. **Auto-loop**: CR/TST/BRIDGE Block → relaunch DEV với feedback đính kèm, tăng `loops.<role>`. Vượt 3 → STOP escalate.
4. **Budget**: mỗi lần launch subagent → `budget_used += 1`. Vượt cap → STOP escalate.
5. **Không sửa file ngoài `ai_python/`**: nếu role nào trả output đụng `backend/` hoặc `frontend/` → STOP cross-scope.
6. **Không tự gõ `A/B/C` thay user** (ngay cả khi `pick optimal` được Owner uỷ quyền — vẫn để planner subagent quyết, driver chỉ relay).

## Nguyên tắc prompt (để giảm token mà vẫn đúng)

- **Không paste instruction**: prompt chỉ gồm (a) role name, (b) đường dẫn `*_AGENT_INSTRUCTIONS.md`, (c) I/O variables, (d) gate cần pass, (e) loop feedback (nếu có).
- **Không paste nội dung artifact**: chỉ đưa **path** + “đọc file đó” (subagent tự đọc).
- **Loop feedback**: đưa **path report** + tối đa 10 dòng trích dẫn phần `Block`/`Major` (nếu cần), không dán toàn report.

## Pipeline (mỗi step = 1 subagent qua Task tool)

### Step 0 — Pre-flight

1. Read [`ai_python/AGENTS/WORKFLOW_RULE.md`](../../ai_python/AGENTS/WORKFLOW_RULE.md) + [`ai_python/AGENTS/AGENT_REGISTRY.md`](../../ai_python/AGENTS/AGENT_REGISTRY.md).
2. Verify `ai_python/AGENTS/`, `ai_python/docs/`, `ai_python/TASKS/` tồn tại.
3. `git branch --show-current` — log branch hiện tại (kỳ vọng `develop` hoặc một branch sạch).
4. Nếu `Mode=dry-run` → in plan từng step bên dưới + dự kiến artifact, **không** launch subagent. Stop.

### Step 1 — AI_PLANNER (HITL gate)

- Skip nếu `SkipPlanner=true` và PRD path đã có ở artifacts.prd.
- Launch:
  ```
  Task tool → subagent_type=generalPurpose
  prompt:
    - Role: AI_PLANNER
    - Read instructions: @AGENTS/AI_PLANNER_AGENT_INSTRUCTIONS.md
    - Brief: <Brief>
    - Output PRD: ai_python/docs/prd/PRD_<slug>.md
    - Requirement: provide options A/B/C + recommendation
  ```
- Subagent trả ≥ 2 option A/B/C + recommendation.
- **DỪNG**, in cho user:
  > Planner đã đề xuất options A/B/C (xem PRD <path>). Vui lòng gõ `A`, `B`, `C` hoặc `pick optimal` để tiếp tục.
- Đợi user reply. Sau khi nhận → relaunch planner với choice → planner output PRD final với option đã chọn → set `artifacts.prd`.

### Step 2 — AI_BA (G-AI-BA)

- Launch:
  - Role: AI_BA
  - Read instructions: @ai_python/AGENTS/AI_BA_AGENT_INSTRUCTIONS.md
  - Inputs: `PRD_PATH=<artifacts.prd>`
  - Outputs: `OUT_PATH=ai_python/docs/srs/SRS_AI_<task_id>_<task_slug>.md`
  - Vars: `TASK_ID`, `TASK_SLUG`, `MCP_PHASE=0`
- Verify gate exit §5 của BA. Match STOP rule → escalate. Pass → set `artifacts.srs`.

### Step 3 — AI_PM (G-AI-PM)

- Launch:
  - Role: AI_PM
  - Read instructions: @ai_python/AGENTS/AI_PM_AGENT_INSTRUCTIONS.md
  - Inputs: `SRS_PATH=<artifacts.srs>`
  - Outputs: `OUT_TASK_FILE=ai_python/TASKS/Task<XXX>.md`, `OUT_TASK_FOLDER=ai_python/docs/task<XXX>/`
  - Vars: `TASK_ID`, `BRANCH_NAME=feature/ai-task<XXX>`
- Verify branch tồn tại + `Task<XXX>.md` đúng cấu trúc → set `artifacts.task_file`, `state.branch`.

### Step 4 — AI_TECH_LEAD (G-AI-TL)

- Launch:
  - Role: AI_TECH_LEAD
  - Read instructions: @ai_python/AGENTS/AI_TECH_LEAD_AGENT_INSTRUCTIONS.md
  - Inputs: `SRS_PATH=<artifacts.srs>`, `TASK_FILE=<artifacts.task_file>`
  - Outputs: `OUT_PATH=ai_python/docs/adr/ADR-<NNN>-<task_slug>.md`
  - Vars: `ADR_NUMBER=<next>`
- Verify NFR có 5 mục số. Pass → set `artifacts.adr`.

### Step 5 — AI_DEVELOPER (G-AI-DEV)

- Launch:
  - Role: AI_DEVELOPER
  - Read instructions: @ai_python/AGENTS/AI_DEVELOPER_AGENT_INSTRUCTIONS.md
  - Inputs: `TASK_FILE=<artifacts.task_file>`, `SRS_PATH=<artifacts.srs>`, `ADR_PATH=<artifacts.adr>`
  - Vars: `BRANCH=<state.branch>`, `LOOP_FEEDBACK=<empty | report path>`
- Verify gate exit §5 (pytest/coverage/ruff/mypy + commit). Pass → đi tiếp.

### Step 6 — AI_CODE_REVIEWER (G-AI-CR) — auto-loop

- Loop rule: theo `WORKFLOW_RULE.md` §2/§3 (`Block` → loop về DEV, max 3).
- Launch each iteration:
  - Role: AI_CODE_REVIEWER
  - Read instructions: @ai_python/AGENTS/AI_CODE_REVIEWER_AGENT_INSTRUCTIONS.md
  - Inputs: `BRANCH=<state.branch>`, `BASE_REF=develop`, `SRS_PATH=<artifacts.srs>`, `ADR_PATH=<artifacts.adr>`
  - Outputs: `OUT_PATH=ai_python/docs/task<XXX>/05-code-review/CODE_REVIEW_Task<XXX>.md`
  - Vars: `ITERATION=<loops.cr+1>`

### Step 7 — AI_BRIDGE (G-AI-BRIDGE) — conditional

- Skip nếu task không tạo/đổi event SSE hoặc MCP schema (xác định bằng diff chạm `ai_python/app/api/sse.py` hoặc `ai_python/app/mcp/`).
- Launch:
  - Role: AI_BRIDGE
  - Read instructions: @ai_python/AGENTS/AI_BRIDGE_AGENT_INSTRUCTIONS.md
  - Mode: `verify`
  - Inputs: `SRS_PATH=<artifacts.srs>`, `ADR_PATH=<artifacts.adr>`, `BRANCH=<state.branch>`
  - Outputs: `OUT_PATH=ai_python/docs/api/bridge/BRIDGE_AI_Task<XXX>_<task_slug>.md`
- Loop only khi drift thuộc scope `ai_python` (theo instruction). Drift ngoài scope → handoff, không loop.

### Step 8 — AI_TESTER (G-AI-TST) — auto-loop

- Loop rule: `Block` → loop về DEV, max 3; security STOP (HITL bypass) → escalate ngay.
- Launch:
  - Role: AI_TESTER
  - Read instructions: @ai_python/AGENTS/AI_TESTER_AGENT_INSTRUCTIONS.md
  - Inputs: `SRS_PATH=<artifacts.srs>`, `ADR_PATH=<artifacts.adr>`
  - Outputs: `OUT_FOLDER=ai_python/docs/task<XXX>/04-tester/`
  - Vars: `TASK_ID`, `EVAL_PROMPTS=<as required by instruction>`

### Step 9 — AI_DOC_SYNC (G-AI-DS)

- Launch:
  - Role: AI_DOC_SYNC
  - Read instructions: @ai_python/AGENTS/AI_DOC_SYNC_AGENT_INSTRUCTIONS.md
  - Vars: `SCOPE=Task<XXX>`
  - Outputs: `OUT_PATH=ai_python/docs/sync_reports/SYNC_REPORT_Task<XXX>_<date>.md`
- 0 drift Block → pass.

### Step 10 — AI_ORCHESTRATOR (G-AI-OR final)

- Launch:
  - Role: AI_ORCHESTRATOR
  - Read instructions: @ai_python/AGENTS/AI_ORCHESTRATOR_AGENT_INSTRUCTIONS.md
  - Vars: `MODE=final`, `TASK_ID`
  - Outputs: `OUT_PATH=ai_python/docs/orchestration/AUDIT_<Task>_final.md`
- Verdict `PASS` → toàn task xong.
- Verdict `WARN` → in danh sách warn, hỏi Owner accept (HITL ngoại lệ duy nhất sau planner).
- Verdict `FAIL` → escalate Owner full report.

## Final summary template (driver in cho user khi xong)

```text
## /orchestrate done — Task<XXX>
- PRD: <link>
- SRS: <link>
- Task chain: <link>
- ADR: <link>
- Branch: <name> (HEAD: <hash>)
- CR iterations: <n>
- Bridge: <link or n/a>
- Tester iterations: <n>; Eval pass-rate: <%>; HITL bypass: 0%
- Doc Sync: <link>
- Final audit: <link>
- Budget used: <m>/<cap>
```

## Dry-run output template

```text
## /orchestrate DRY-RUN — Task=<id> Brief="..."
1. AI_PLANNER → ai_python/docs/prd/PRD_<slug>.md (HITL: A/B/C)
2. AI_BA → ai_python/docs/srs/SRS_AI_<task>_<slug>.md
3. AI_PM → ai_python/TASKS/<task>.md + branch feature/ai-task<task>
4. AI_TECH_LEAD → ai_python/docs/adr/ADR-<NNN>-<slug>.md
5. AI_DEVELOPER → ai_python/app/** + tests
6. AI_CODE_REVIEWER → ai_python/docs/<task>/05-code-review/CODE_REVIEW_<task>.md (auto-loop ≤3)
7. AI_BRIDGE (if SSE/MCP changed) → ai_python/docs/api/bridge/BRIDGE_AI_<task>_<slug>.md
8. AI_TESTER → ai_python/docs/<task>/04-tester/* (auto-loop ≤3)
9. AI_DOC_SYNC → ai_python/docs/sync_reports/SYNC_REPORT_<task>_<date>.md
10. AI_ORCHESTRATOR (final) → ai_python/docs/orchestration/AUDIT_<task>_final.md
Budget cap: 20. Estimated invocations: 10–18 (no loops). With max loops: ~25 (sẽ escalate).
```

## Lưu ý kỹ thuật

- Subagent có thể tự đọc repo, nên driver **ưu tiên**: đưa path + biến I/O + gate cần pass (không paste file dài).
- Driver chỉ cần nhắc subagent: “đọc instruction + đọc các artifact input theo path; không vượt scope `ai_python/`”.
- Khi loop: đưa report path + trích ngắn phần `Block`/`Major` để DEV sửa đúng điểm.

## Khi gặp escalation

In cho Owner:

```text
## /orchestrate ESCALATED at <gate>
Reason: <STOP rule | budget exceeded | loop > 3>
State: <task_id, branch, gate, budget, loops>
Last report: <link>
Suggested next steps:
1. ...
2. ...
```

Đợi Owner quyết định: `/orchestrate resume Task=<id>` (rerun từ gate kế) hoặc abort.
