# ADR-004 — LangGraph Gemma4 Task4 Spring FastAPI

**SRS_PATH:** `d:\do_an_tot_nghiep\project\ai_python\docs\srs\SRS_AI_Task004_langgraph-gemma4-task4-spring-fastapi.md`  
**TASK_FILE:** `d:\do_an_tot_nghiep\project\ai_python\TASKS\Task004.md`  
**Date:** 2026-05-10

## 1. Boi canh & quyet dinh

Task004 can mot API layer FastAPI cho LangGraph/Gemma4 de phuc vu Spring trusted boundary voi invoke dong bo va stream theo SSE. Theo SRS da approved, quyet dinh kien truc duoc khoa theo Option B: Spring xu ly auth/context o upstream, FastAPI chi chap nhan JWT/signed context hop le, va duong SQL production phai di qua Spring HTTP proxy thay vi direct DB tu Python. ADR nay chot phuong an trien khai integration de dam bao contract on dinh, de test, va an toan khi mo rong.

## 2. Phuong an da xem xet

- **Option A — Python-centric direct mode**
  - FastAPI tu xac thuc theo local secret, ho tro stream long-polling/WebSocket, SQL cho production co the goi truc tiep DB.
  - **Pros:** giam phu thuoc Spring, de prototype nhanh.
  - **Cons:** pha vo trust boundary da chot trong SRS, tang rui ro bao mat va drift contract giua he thong.

- **Option B — Spring trust boundary + JWT + SSE + Spring SQL proxy**
  - Spring la trusted upstream boundary, FastAPI validate JWT/signed context; stream chi qua SSE terminal-guarantee; production SQL qua `http_spring`.
  - **Pros:** dong bo voi SRS/PRD, ro boundary trach nhiem, de audit auth va correlation, giam coupling Python voi DB production.
  - **Cons:** can phoi hop chat voi Spring handoff contract va monitor integration points.

- **Option C — Hybrid transition mode**
  - Giu Option B cho auth/stream, nhung cho phep fallback direct SQL production khi Spring proxy loi.
  - **Pros:** co duong de phong trong giai doan dau.
  - **Cons:** tao duong bypass policy, kho kiem soat nhat quan bao mat va khong phu hop lock kien truc.

## 3. Quyet dinh

**Chon Option B va khoa theo SRS:** FastAPI trong `ai_python` se enforce JWT/signed context tu Spring trust boundary, expose `POST /api/v1/ai/chat/invoke` va `POST /api/v1/ai/chat/stream` (SSE), va route SQL production qua Spring HTTP proxy (`http_spring`) thay vi direct DB mode.

## 4. He qua

- **Migration:** can bo sung/hoan thien auth validator cho JWT claim contract (issuer/audience/signature), standardize request metadata validation, va wiring SQL executor mode `http_spring` cho production.
- **Feature flag & rollout:** direct DB mode duoc gioi han non-prod; production bat buoc Spring proxy, co the dung env/setting de chot mode theo environment.
- **Risk ky thuat:** neu contract Spring token/claims thay doi ma khong sync se gay 401/403 hoac mat context; can contract tests invoke/stream + auth failure va terminal event guarantee.
- **Van hanh & quan sat:** bat buoc propagate `X-Correlation-Id` xuyen suot logs/response/event de truy vet loi integration giua Spring ↔ FastAPI ↔ LangGraph.

## 5. NFR (5 muc)

1. **Hieu nang:** p95 invoke < 8s va p95 stream first event < 3s cho standard workload theo SRS.
2. **Do tin cay:** stream phai phat ra dung 1 terminal event (`final_answer` hoac `error`) cho 100% session hop le.
3. **Bao mat:** 100% request Option B phai validate JWT/signed context truoc khi graph execution; khong cho bypass auth sang runtime.
4. **Van hanh:** 100% request va stream event phai co `correlation_id` de trace end-to-end qua Spring/FastAPI/runtime logs.
5. **Chi phi va tuong thich:** giu canonical envelope + contract Task1/2/3, tranh duplicate xu ly stream/invoke de han che token va effort bao tri.
