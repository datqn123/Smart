# ADR-005 — SQL DB Metadata Production

**SRS_PATH:** `d:\do_an_tot_nghiep\project\ai_python\docs\srs\SRS_AI_Task006_sql-dbmeta-production.md`  
**TASK_FILE:** `d:\do_an_tot_nghiep\project\ai_python\TASKS\Task006.md`  
**Date:** 2026-05-11

## 1. Boi canh & quyet dinh

Task006 dua SQL execution cua `ai_python` tu stub/dev sang Phase 1 production nhung van giu ranh gioi trach nhiem: Spring so huu endpoint read-only SQL, auth, audit, DB connectivity va policy production; Python chi implement executor client, config validation, defensive SQL safety, result/error mapping va workflow CLI scan/validate DB metadata YAML. Theo SRS da approved, runtime graph topology giu nguyen (`gen_sql -> sql_review -> validate_sql -> execute_sql -> validate_result -> summarize_answer`), `http_spring` la production executor duy nhat trong Phase 1, `python_ro` duoc nhan dien nhung fail-fast deferred, va runtime chi load YAML da validate thay vi scan DB tren startup/request path.

## 2. Phuong an da xem xet

- **Option A — Python direct read-only DB (`python_ro`) trong Phase 1**
  - Python ket noi truc tiep database bang read-only credential, tu thuc thi SELECT sau cac check an toan.
  - **Pros:** it phu thuoc Spring endpoint, duong request ngan hon, de debug local khi co DB RO.
  - **Cons:** vuot scope Task006, tang gan ket Python voi production DB policy, kho audit tap trung, va trai voi SRS yeu cau `python_ro` deferred.

- **Option B — Spring-owned SQL endpoint + Python `http_spring` client**
  - Python validate config/safety, gui SQL da qua graph review toi Spring read-only endpoint, roi map response/failure ve shape graph hien co.
  - **Pros:** khop SRS Option B, giu trust boundary va audit trong Spring, tach Python khoi production DB credential, de sanitize error va test bang mock HTTP.
  - **Cons:** can contract handoff voi Spring va phu thuoc endpoint downstream duoc van hanh dung timeout/row-limit/policy.

- **Option C — Runtime DB metadata auto-scan tren startup**
  - Moi lan app khoi dong, Python introspect DB de build metadata truoc khi phuc vu graph.
  - **Pros:** metadata moi hon, it thao tac thu cong cho operator.
  - **Cons:** them DB dependency vao startup, co rui ro cham/fail startup ngoai y muon, va trai SRS yeu cau runtime load YAML da tao san.

## 3. Quyet dinh

**Chon Option B cho executor production Phase 1 va CLI pre-built metadata workflow:** `SQL_EXECUTOR_MODE=http_spring` la mode production duy nhat cua Task006; `stub` giu cho local/CI; `python_ro` fail-fast voi thong diep deferred Phase 2. Python se enforce read-only SQL, timeout, row limit va config validation truoc dispatch, map Spring success/failure ve `query_result`/`validation_feedback` tuong thich graph. DB metadata duoc tao/cap nhat bang CLI scan + validate hoac validate YAML manual, sau do runtime chi load artifact YAML da validate tu `SCHEMA_DIR`.

## 4. He qua

- **Migration:** executor factory can validate mode/env/timeout/row-limit som; existing graph node contract phai duoc giu tuong thich voi `query_result.rows` trong khi bo sung `columns` va `meta`.
- **Feature flag & rollout:** production reject mode khac `http_spring`; local/dev van dung `stub`; `python_ro` khong duoc bat bang `DATABASE_URL_RO` trong Task006.
- **Spring handoff risk:** neu endpoint Spring chua san sang hoac response schema drift, Python phai tra ve sanitized upstream/config feedback thay vi leak raw error; can mock/contract tests cho success, policy/auth, timeout, 5xx va malformed response.
- **Metadata operation:** operator phai chay scan/validate truoc release co thay doi schema hoac theo chu ky freshness; runtime fail-fast khi YAML thieu/invalid, nhung khong scan DB trong request/startup path.
- **Security boundary:** DB credential production, authorization, audit va row-level policy nam o Spring; Python chi truyen context/correlation/limit/timeout can thiet va redact service credential trong log.

## 5. NFR (5 muc)

1. **An toan:** 100% non-stub execution phai reject DDL, DML, transaction-control va multi-statement SQL truoc khi goi Spring.
2. **Hieu nang:** default timeout SQL <= 10 giay, configurable trong khoang 1-30 giay; default row limit <= 100 va hard max <= 500.
3. **Bao mat loi:** graph feedback va logs khong duoc chua DB password, bearer token, credentialed URL, full auth header hoac raw upstream stack trace.
4. **Do tin cay:** executor factory va metadata modules dat muc tieu >= 90% line coverage; timeout/network/malformed response phai map thanh failure category co the test duoc.
5. **Van hanh:** non-stub execution log mode, correlation/request id khi co, duration_ms, row_count va sanitized error category; metadata artifact co `generated_at`, source mode va schema identifier.
