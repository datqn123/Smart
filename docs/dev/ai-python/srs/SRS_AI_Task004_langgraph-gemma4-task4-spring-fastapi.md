# SRS — AI Python — Task004 / LangGraph Gemma4 Task4 Spring FastAPI

**Status:** Approved  
**Date:** 2026-05-10  
**MCP_PHASE:** 0  
**PRD:** `docs/ai-python/prd/PRD_langgraph-gemma4-task4-spring-fastapi.md`  
**Task ID:** `Task004`  
**Slug:** `langgraph-gemma4-task4-spring-fastapi`

---

## 1. Summary & scope

**Locked decision:** this SRS follows PRD final architecture **Option B**:
- Spring is the trusted upstream auth/context boundary and forwards validated context to FastAPI via JWT/signed context.
- FastAPI exposes sync invoke and SSE stream touchpoints only.
- Production SQL execution path is Spring-proxy HTTP (`http_spring`), while Python-only DB paths are non-prod only.

**In-scope (`ai_python/`):**
- Define and implement stable FastAPI touchpoints for invoke and stream contracts.
- Enforce request metadata/header validation and canonical response/error envelopes.
- Propagate correlation and context into LangGraph runtime integration boundaries.
- Define integration contract for JWT/context verification and Spring-proxy SQL executor path on Python side.
- Add/maintain contract tests for invoke/stream success and failure semantics.

**Out-of-scope:**
- Any Spring controller/gateway code changes or frontend integration code.
- Database schema changes, backend authorization model redesign, or ERP policy changes.
- Changes to Task 1/2/3 core internal logic beyond API integration/wiring required by Task004.

**Handoff note (cross-scope):**
- Spring implementation artifacts (JWT issuing, upstream auth decisions, SQL proxy endpoint implementation) are managed outside this repo and must be tracked as external handoff items, not implemented under `ai_python/`.

---

## 2. Stakeholders & flows

| Actor | Role |
| :-- | :-- |
| Spring service | Trusted caller, validates user auth, sends JWT/context and correlation id to FastAPI. |
| FastAPI (`ai_python`) | Validates integration contract, calls LangGraph runtime, returns invoke/stream outputs. |
| Ops/observability maintainers | Monitor latency, stream terminal guarantees, error rates, and trace propagation. |
| Product/QA owners | Validate API contracts and acceptance criteria against PRD Task004 goals. |

**Main flow — invoke happy path:**

```text
Spring receives upstream request
  -> ensures X-Correlation-Id and signed JWT/context
  -> POST /api/v1/ai/chat/invoke with message + metadata
  -> FastAPI validates headers/body/auth contract
  -> FastAPI maps request to graph runtime
  -> returns canonical JSON envelope with final_answer
```

**Main flow — stream happy path (SSE):**

```text
Spring sends POST /api/v1/ai/chat/stream
  -> FastAPI validates request and starts SSE response
  -> emits token/partial events
  -> emits exactly one terminal event: final_answer
```

**Alternative/error flows:**
- Missing/invalid `X-Correlation-Id` or required metadata -> 4xx with standard error envelope.
- Invalid JWT/signature/issuer/audience -> 401/403 and no graph execution.
- Runtime failure during invoke/stream -> canonical `error` envelope / terminal `error` stream event.
- Stream interruption handling must still attempt terminal guarantee semantics where transport permits.

---

## 3. Functional requirements

| ID | Requirement (testable) | Trace |
| :-- | :-- | :-- |
| **FR-API-01** | FastAPI provides `POST /api/v1/ai/chat/invoke` returning canonical non-stream JSON envelope. | PRD FR-01 |
| **FR-API-02** | FastAPI provides `POST /api/v1/ai/chat/stream` over SSE (`text/event-stream`) only. | PRD FR-01, Option B |
| **FR-API-03** | Request must include `X-Correlation-Id`; if absent/invalid, return 4xx with canonical error structure. | PRD FR-02 |
| **FR-API-04** | Request body must validate required metadata: `user_id`, `tenant_id`; support optional `thread_id`, default/fallback `schema_version`. | PRD FR-02, FR-03 |
| **FR-API-05** | Invoke success response includes `correlation_id`, `thread_id`, `intent`, `final_answer`, `usage`, `error=null`. | PRD FR-04 |
| **FR-API-06** | Error response (invoke and stream terminal error) uses canonical envelope with `error.code`, `error.message`, optional `error.details`. | PRD FR-05 |
| **FR-API-07** | Stream events include minimum fields `correlation_id`, `event_type`, payload (`delta` or `data`), `is_terminal`. | PRD FR-06 |
| **FR-API-08** | Stream emits exactly one terminal event: either `final_answer` or `error`. | PRD FR-06 |
| **FR-CTX-01** | FastAPI forwards `correlation_id`, `tenant_id`, `user_id`, `thread_id`, `schema_version` into graph config/state integration points. | PRD FR-07 |
| **FR-COMP-01** | API layer remains compatible with Task1 `LlmClient`, Task2 graph/checkpointer/stream hooks, Task3 agent behavior contracts. | PRD FR-08 |
| **FR-SEC-01** | Under Option B, FastAPI accepts only valid JWT/signed context from Spring trust boundary and derives identity context from claims. | PRD Option B + Security |
| **FR-SQL-01** | Production SQL execution mode must route via Spring HTTP proxy contract (`http_spring`); Python direct DB modes are non-prod constrained. | PRD Option B non-goal note |
| **FR-TEST-01** | Contract tests cover invoke/stream success, validation failures, auth failures, and error mapping with deterministic assertions. | PRD Task 4.6 |

---

## 4. API / integration contracts

### 4.1 Endpoint contract

| Endpoint | Method | Content type | Purpose |
| :-- | :-- | :-- | :-- |
| `/api/v1/ai/chat/invoke` | POST | `application/json` | Synchronous AI response envelope |
| `/api/v1/ai/chat/stream` | POST | request `application/json`, response `text/event-stream` | Streaming events over SSE |

### 4.2 Request headers

| Header | Required | Rule |
| :-- | :-- | :-- |
| `X-Correlation-Id` | Yes | UUID/string trace id, propagated end-to-end |
| `Authorization` | Yes (Option B) | Bearer JWT/signed context from Spring trust boundary |

### 4.3 Canonical request body

```json
{
  "message": "Doanh thu thang nay cua chi nhanh HN la bao nhieu?",
  "metadata": {
    "user_id": "u-123",
    "tenant_id": "tenant-a",
    "thread_id": "t-001",
    "schema_version": "v1"
  },
  "options": {
    "stream": false,
    "locale": "vi-VN"
  }
}
```

### 4.4 Invoke success payload

```json
{
  "correlation_id": "0f8fad5b-d9cb-469f-a165-70867728950e",
  "thread_id": "t-001",
  "intent": "system_data_query",
  "final_answer": "Doanh thu thang nay cua chi nhanh HN la 1.2 ty VND.",
  "usage": {
    "input_tokens": 0,
    "output_tokens": 0
  },
  "error": null
}
```

### 4.5 Error envelope

```json
{
  "correlation_id": "0f8fad5b-d9cb-469f-a165-70867728950e",
  "error": {
    "code": "AI_VALIDATION_FAILED",
    "message": "SQL validation failed after max attempts",
    "details": {
      "attempts": 3
    }
  }
}
```

### 4.6 SSE event shapes

| `event_type` | Payload field | Terminal |
| :-- | :-- | :-- |
| `token` | `delta` | No |
| `partial_answer` | `data` | No |
| `heartbeat` (optional) | `data` | No |
| `final_answer` | `data` | Yes |
| `error` | `data` (error envelope) | Yes |

### 4.7 Integration boundaries

- **Auth/context integration:** FastAPI validates JWT/signed context (signature/issuer/audience/claims contract) and rejects invalid requests before graph execution.
- **Graph integration:** API layer maps validated request + metadata to Task2/Task3 runtime interfaces, without modifying business node behavior.
- **SQL integration:** for production mode, SQL execution calls Spring-proxy endpoint contract (`http_spring`) from Python executor abstraction only.
- **Cross-scope handoff:** Spring-side JWT issuing rules, SQL proxy service endpoint implementation, and upstream auth policy are external deliverables.

---

## 5. Data / state shapes

```python
class ChatMetadata(TypedDict, total=False):
    user_id: str
    tenant_id: str
    thread_id: str
    schema_version: str

class ChatOptions(TypedDict, total=False):
    stream: bool
    locale: str

class ChatRequest(TypedDict):
    message: str
    metadata: ChatMetadata
    options: ChatOptions

class InvokeUsage(TypedDict, total=False):
    input_tokens: int
    output_tokens: int

class ErrorObject(TypedDict, total=False):
    code: str
    message: str
    details: dict[str, object]

class InvokeResponse(TypedDict, total=False):
    correlation_id: str
    thread_id: str
    intent: str
    final_answer: str
    usage: InvokeUsage
    error: ErrorObject | None

class StreamEvent(TypedDict, total=False):
    correlation_id: str
    event_type: str
    delta: str
    data: dict[str, object] | str
    is_terminal: bool
```

**State/context mapping constraints:**
- `correlation_id` must be available in logs and graph context for all requests.
- `tenant_id` and `user_id` derive from validated Option B trust contract.
- `thread_id` is propagated for checkpointer continuity where provided.
- `schema_version` maps to schema selector/default behavior in graph/sql pipeline.

---

## 6. Non-functional requirements (NFR)

| ID | Requirement | Target |
| :-- | :-- | :-- |
| **NFR-PERF-01** | Invoke latency for standard text prompts | p95 < 8s |
| **NFR-PERF-02** | Stream first event latency | p95 < 3s |
| **NFR-REL-01** | API 5xx rate steady-state | < 1% |
| **NFR-REL-02** | Stream terminal guarantee (`final_answer` or `error`) | 100% sessions |
| **NFR-SEC-01** | No credential leakage in logs/responses (`LLM_API_KEY`, sensitive auth headers) | 0 leaks |
| **NFR-SEC-02** | JWT/signed context validation on every Option B request | 100% enforced |
| **NFR-OBS-01** | Correlation id propagation in logs | 100% requests |
| **NFR-COMP-01** | Schema compatibility via `schema_version` handling | backward-compatible behavior |
| **NFR-TEST-01** | Contract test coverage for invoke/stream core behaviors | include success + failure paths |

---

## 7. Acceptance criteria

### 7.1 Given/When/Then checks

- **FR-API-01 / FR-API-05**
  - Given a valid invoke request with required metadata and valid JWT/context, when `POST /api/v1/ai/chat/invoke` is called, then response is 200 with canonical fields and `error=null`.
- **FR-API-02 / FR-API-08**
  - Given a valid stream request, when `POST /api/v1/ai/chat/stream` is called, then response uses SSE and emits exactly one terminal event (`final_answer` or `error`).
- **FR-API-03 / FR-API-04**
  - Given missing `X-Correlation-Id` or missing `user_id`/`tenant_id`, when request is submitted, then API returns 4xx canonical error and does not execute graph runtime.
- **FR-SEC-01**
  - Given invalid JWT signature/issuer/audience, when request is submitted, then API returns 401/403 and no downstream execution occurs.
- **FR-CTX-01**
  - Given valid request context, when runtime executes, then logs and graph context include correlation and metadata mapping.
- **FR-SQL-01**
  - Given production SQL mode enabled, when SQL execution is requested, then executor uses Spring-proxy contract path (`http_spring`) instead of direct Python DB mode.

### 7.2 Checklist acceptance

- [ ] Invoke endpoint contract matches section 4 payload and error envelope.
- [ ] Stream endpoint uses SSE and event taxonomy in section 4.6.
- [ ] Validation gates reject missing/invalid metadata and invalid auth.
- [ ] Correlation id is consistently propagated to logs and response/event envelopes.
- [ ] Compatibility with Task1/Task2/Task3 integration assumptions is preserved.
- [ ] Spring-side implementation work is tracked as handoff outside repo scope.

---

## 8. Traceability to PRD

| SRS requirement | PRD source |
| :-- | :-- |
| FR-API-01, FR-API-02 | PRD §4.2 FR-01 |
| FR-API-03, FR-API-04 | PRD §4.2 FR-02, FR-03 |
| FR-API-05 | PRD §4.2 FR-04 |
| FR-API-06 | PRD §4.2 FR-05 |
| FR-API-07, FR-API-08 | PRD §4.2 FR-06 |
| FR-CTX-01 | PRD §4.2 FR-07 |
| FR-COMP-01 | PRD §4.2 FR-08 |
| FR-SEC-01 | PRD Locked architecture Option B + Security requirements |
| FR-SQL-01 | PRD Non-goals + Locked architecture Option B SQL posture |
| NFR-PERF/REL/SEC/OBS/COMP | PRD §4.2 NFR block |
| Acceptance section 7 | PRD §4.4 Task 4.1..4.6 acceptance intent + FR/NFR mapping |

**Gate exit:** PASS — full SRS generated at `OUT_PATH`; PRD is complete, Option B reflected, no STOP triggered.
