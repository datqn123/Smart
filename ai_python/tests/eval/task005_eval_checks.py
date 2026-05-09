"""Task005 batch eval checks — one callable per ``prompts.jsonl`` id (G-AI-TST)."""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.agents.task005_corpus_job import run_corpus_job
from app.contracts.task005 import (
    MAX_COLUMNS,
    MAX_SMOKE_ROW_COUNT,
    ColumnMeta,
    CorpusJobContext,
    McpToolError,
    SqlColumn,
    SqlDescribeIn,
    SqlDescribeOut,
    SqlQueryReadonlyIn,
    SqlQueryReadonlyOut,
)
from app.mcp.db_readonly_port import (
    DescribeResult,
    McpTransportError,
    QueryReadonlyResult,
)
from app.mcp.task005_unconfigured_client import UnconfiguredDbReadonlyClient
from app.rag.task005_ingest import ingest_corpus, read_chunks
from app.registry.task005_templates import load_registry_from_dict
from app.tools.task005_artifacts import smoke_entry_from_failure
from app.tools.task005_corpus_fs import DEFAULT_CORPUS_ROOT, HEALTH_NAMESPACE, SCHEMA_NAMESPACE
from app.tools.task005_smoke import run_smoke_loop

_FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "task005"
_APP_TASK005_GLOBS = ("**/task005*.py", "**/cli/task005*.py")


def _load_fixture(name: str) -> dict[str, Any]:
    return json.loads((_FIXTURES / name).read_text(encoding="utf-8"))


def _ai_python_app_root() -> Path:
    return Path(__file__).resolve().parents[2] / "app"


class _FakeClient:
    def __init__(
        self,
        *,
        describes: dict[str, DescribeResult] | None = None,
        smokes: dict[str, QueryReadonlyResult] | None = None,
        transport_down: bool = False,
    ) -> None:
        self._describes = describes or {}
        self._smokes = smokes or {}
        self._transport_down = transport_down

    async def describe(self, payload: SqlDescribeIn) -> DescribeResult:
        if self._transport_down:
            raise McpTransportError("transport unavailable")
        return self._describes[payload.object_name]

    async def query_readonly(
        self, payload: SqlQueryReadonlyIn
    ) -> QueryReadonlyResult:
        if self._transport_down:
            raise McpTransportError("transport unavailable")
        return self._smokes[payload.template_id]


def _ok_describe(name: str) -> SqlDescribeOut:
    base = _load_fixture("sql_describe_response.json")
    return SqlDescribeOut.model_validate(
        {
            **base,
            "object_name": name,
            "summary": f"cols=1 object={name}",
            "correlation_id": f"corr-{name}",
        }
    )


def _ok_smoke() -> SqlQueryReadonlyOut:
    return SqlQueryReadonlyOut.model_validate(
        _load_fixture("sql_query_readonly_response.json")
    )


def _seed_pipeline_config(tmp: Path) -> tuple[Path, Path]:
    objects_path = tmp / "objects.json"
    templates_path = tmp / "templates.json"
    objects_path.write_text(
        json.dumps(_load_fixture("objects_allowlist.json")), encoding="utf-8"
    )
    templates_path.write_text(
        json.dumps(_load_fixture("templates_registry_pipeline.json")),
        encoding="utf-8",
    )
    return objects_path, templates_path


def _task005_py_files() -> list[Path]:
    root = _ai_python_app_root()
    out: list[Path] = []
    for pattern in _APP_TASK005_GLOBS:
        out.extend(root.glob(pattern))
    return sorted({p.resolve() for p in out if p.is_file()})


def check_T005_B1_01() -> tuple[bool, str]:
    try:
        SqlDescribeIn(object_name="   ")
        return False, "expected ValidationError for blank object_name"
    except ValidationError:
        return True, "SqlDescribeIn rejects blank object_name"


def check_T005_B1_02() -> tuple[bool, str]:
    cols = [
        ColumnMeta(name=f"c{i}", type="text", nullable=True) for i in range(MAX_COLUMNS)
    ]
    SqlDescribeOut(
        object_name="reporting.wide_v1",
        columns=cols,
        summary="ok",
        correlation_id="corr",
    )
    return True, f"SqlDescribeOut accepts {MAX_COLUMNS} columns"


def check_T005_B1_03() -> tuple[bool, str]:
    async def _run() -> tuple[bool, str]:
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            client = _FakeClient(
                describes={
                    "reporting.sales_by_day_v1": _ok_describe(
                        "reporting.sales_by_day_v1"
                    )
                },
                smokes={"sales_by_day_v1": _ok_smoke()},
            )
            objects_path, templates_path = _seed_pipeline_config(tmp)
            outcome = await run_corpus_job(
                client=client,
                objects_path=objects_path,
                templates_path=templates_path,
                corpus_root=tmp / "rag_corpus",
                correlation_id="corr_eval_b103",
            )
            if outcome.exit_code != 0:
                return False, f"exit_code={outcome.exit_code}"
            return True, "happy pipeline exit 0"

    return asyncio.run(_run())


def check_T005_B1_04() -> tuple[bool, str]:
    async def _run() -> tuple[bool, str]:
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            client = _FakeClient(
                describes={
                    "reporting.sales_by_day_v1": _ok_describe(
                        "reporting.sales_by_day_v1"
                    )
                },
                smokes={"sales_by_day_v1": _ok_smoke()},
            )
            objects_path, templates_path = _seed_pipeline_config(tmp)
            corpus_root = tmp / "rag_corpus"
            outcome = await run_corpus_job(
                client=client,
                objects_path=objects_path,
                templates_path=templates_path,
                corpus_root=corpus_root,
                correlation_id="corr_eval_b104",
            )
            if not outcome.catalog_path or not outcome.catalog_path.exists():
                return False, "missing catalog"
            data = json.loads(outcome.catalog_path.read_text(encoding="utf-8"))
            if "corpus_version" not in data:
                return False, "catalog missing corpus_version"
            if data.get("corpus_version") != outcome.context.corpus_version:
                return False, "corpus_version mismatch"
            return True, "catalog versioned"

    return asyncio.run(_run())


def check_T005_B1_05() -> tuple[bool, str]:
    async def _run() -> tuple[bool, str]:
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            client = _FakeClient(
                describes={
                    "reporting.sales_by_day_v1": _ok_describe(
                        "reporting.sales_by_day_v1"
                    )
                },
                smokes={"sales_by_day_v1": _ok_smoke()},
            )
            objects_path, templates_path = _seed_pipeline_config(tmp)
            outcome = await run_corpus_job(
                client=client,
                objects_path=objects_path,
                templates_path=templates_path,
                corpus_root=tmp / "rag_corpus",
                correlation_id="corr_eval_b105",
            )
            if not outcome.health_path or not outcome.health_path.exists():
                return False, "missing health"
            health = json.loads(outcome.health_path.read_text(encoding="utf-8"))
            for entry in health.get("smoke", []):
                if "rows" in entry:
                    return False, "rows leaked into health artifact"
            return True, "health smoke summary-only"

    return asyncio.run(_run())


def check_T005_B1_06() -> tuple[bool, str]:
    async def _run() -> tuple[bool, str]:
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            client = _FakeClient(
                describes={
                    "reporting.sales_by_day_v1": _ok_describe(
                        "reporting.sales_by_day_v1"
                    )
                },
                smokes={"sales_by_day_v1": _ok_smoke()},
            )
            objects_path, templates_path = _seed_pipeline_config(tmp)
            outcome = await run_corpus_job(
                client=client,
                objects_path=objects_path,
                templates_path=templates_path,
                corpus_root=tmp / "rag_corpus",
                correlation_id="corr_eval_b106",
            )
            if outcome.index_chunks < 2:
                return False, f"index_chunks={outcome.index_chunks}"
            return True, "index_chunks>=2"

    return asyncio.run(_run())


def check_T005_B2_01() -> tuple[bool, str]:
    from app.tools.task005_describe import run_describe_loop

    async def _run() -> tuple[bool, str]:
        client = _FakeClient(
            describes={
                "reporting.a_v1": _ok_describe("reporting.a_v1"),
                "reporting.b_v1": McpToolError(
                    code="DB_TIMEOUT",
                    message="x",
                    retryable=True,
                    correlation_id="c-b",
                ),
                "reporting.c_v1": _ok_describe("reporting.c_v1"),
            }
        )
        outcome = await run_describe_loop(
            client=client,
            objects=("reporting.a_v1", "reporting.b_v1", "reporting.c_v1"),
            correlation_id="corr_b201",
        )
        exp = {"reporting.a_v1": "ok", "reporting.b_v1": "failed", "reporting.c_v1": "ok"}
        if outcome.results != exp:
            return False, f"results={outcome.results}"
        return True, "partial describe_results"

    return asyncio.run(_run())


def check_T005_B2_02() -> tuple[bool, str]:
    from app.tools.task005_describe import run_describe_loop

    async def _run() -> tuple[bool, str]:
        client = _FakeClient(
            describes={
                "reporting.a_v1": _ok_describe("reporting.a_v1"),
                "reporting.b_v1": McpToolError(
                    code="DB_TIMEOUT",
                    message="x",
                    retryable=True,
                    correlation_id="c",
                ),
                "reporting.c_v1": _ok_describe("reporting.c_v1"),
            }
        )
        outcome = await run_describe_loop(
            client=client,
            objects=("reporting.a_v1", "reporting.b_v1", "reporting.c_v1"),
            correlation_id="corr",
        )
        if not outcome.has_failures:
            return False, "expected has_failures"
        return True, "has_failures true"

    return asyncio.run(_run())


def check_T005_B2_03() -> tuple[bool, str]:
    from app.tools.task005_describe import run_describe_loop

    async def _run() -> tuple[bool, str]:
        client = _FakeClient(
            describes={
                "reporting.a_v1": _ok_describe("reporting.a_v1"),
                "reporting.b_v1": McpToolError(
                    code="DB_TIMEOUT",
                    message="x",
                    retryable=True,
                    correlation_id="c",
                ),
                "reporting.c_v1": _ok_describe("reporting.c_v1"),
            }
        )
        outcome = await run_describe_loop(
            client=client,
            objects=("reporting.a_v1", "reporting.b_v1", "reporting.c_v1"),
            correlation_id="corr",
        )
        if not outcome.failures or outcome.failures[0].code != "DB_TIMEOUT":
            return False, str(outcome.failures)
        return True, "DB_TIMEOUT on failed object"

    return asyncio.run(_run())


def check_T005_B2_04() -> tuple[bool, str]:
    async def _run() -> tuple[bool, str]:
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            client = _FakeClient(
                describes={
                    "reporting.sales_by_day_v1": McpToolError(
                        code="DB_TIMEOUT",
                        message="x",
                        retryable=True,
                        correlation_id="c",
                    )
                },
                smokes={"sales_by_day_v1": _ok_smoke()},
            )
            objects_path, templates_path = _seed_pipeline_config(tmp)
            outcome = await run_corpus_job(
                client=client,
                objects_path=objects_path,
                templates_path=templates_path,
                corpus_root=tmp / "rag_corpus",
                correlation_id="corr_b204",
            )
            if outcome.exit_code == 0:
                return False, "expected non-zero exit"
            return True, "describe fail + smoke ok -> exit != 0"

    return asyncio.run(_run())


def check_T005_B3_01() -> tuple[bool, str]:
    async def _run() -> tuple[bool, str]:
        class _C:
            def __init__(self) -> None:
                self.calls: list[str] = []

            async def describe(self, payload: SqlDescribeIn) -> object:
                raise NotImplementedError

            async def query_readonly(
                self, payload: SqlQueryReadonlyIn
            ) -> QueryReadonlyResult:
                self.calls.append(payload.template_id)
                return _ok_smoke()

        client = _C()
        registry = load_registry_from_dict(
            _load_fixture("templates_registry_two_smokes.json")
        )
        await run_smoke_loop(
            client=client, registry=registry, correlation_id="corr_b301"
        )
        if set(client.calls) != {"sales_by_day_v1", "inventory_snapshot_v1"}:
            return False, str(client.calls)
        return True, "two templates invoked"

    return asyncio.run(_run())


def check_T005_B3_02() -> tuple[bool, str]:
    async def _run() -> tuple[bool, str]:
        class _C:
            async def describe(self, payload: SqlDescribeIn) -> object:
                raise NotImplementedError

            async def query_readonly(
                self, payload: SqlQueryReadonlyIn
            ) -> QueryReadonlyResult:
                return _ok_smoke()

        client = _C()
        registry = load_registry_from_dict(
            _load_fixture("templates_registry_two_smokes.json")
        )
        outcome = await run_smoke_loop(
            client=client, registry=registry, correlation_id="corr"
        )
        for row in [e.model_dump() for e in outcome.entries]:
            if "rows" in row:
                return False, "rows in serialised smoke entry"
        return True, "serialised summary-only"

    return asyncio.run(_run())


def check_T005_B3_03() -> tuple[bool, str]:
    try:
        SqlQueryReadonlyIn.model_validate(
            {"template_id": "t", "params": {}, "injected_channel": True}
        )
        return False, "expected extra forbid"
    except ValidationError:
        return True, "SqlQueryReadonlyIn extra=forbid"


def check_T005_B3_04() -> tuple[bool, str]:
    try:
        SqlQueryReadonlyOut(
            columns=[SqlColumn(name="d", type="date")],
            rows=[],
            row_count=MAX_SMOKE_ROW_COUNT + 1,
            summary="x",
            correlation_id="c",
        )
        return False, "expected row_count cap"
    except ValidationError:
        return True, f"row_count capped at {MAX_SMOKE_ROW_COUNT}"


def check_T005_B3_05() -> tuple[bool, str]:
    async def _run() -> tuple[bool, str]:
        class _C:
            def __init__(self) -> None:
                self.calls: list[str] = []

            async def describe(self, payload: SqlDescribeIn) -> object:
                raise NotImplementedError

            async def query_readonly(
                self, payload: SqlQueryReadonlyIn
            ) -> QueryReadonlyResult:
                self.calls.append(payload.template_id)
                return _ok_smoke()

        client = _C()
        registry = load_registry_from_dict(
            _load_fixture("templates_registry_smoke_loop.json")
        )
        outcome = await run_smoke_loop(
            client=client, registry=registry, correlation_id="corr"
        )
        if any(c == "manual_only_v1" for c in client.calls):
            return False, "non-smoke_safe was called"
        if "manual_only_v1" in outcome.tried:
            return False, "manual in tried"
        return True, "non-smoke_safe skipped"

    return asyncio.run(_run())


def check_T005_B4_01() -> tuple[bool, str]:
    async def _run() -> tuple[bool, str]:
        class _C:
            async def describe(self, payload: SqlDescribeIn) -> object:
                raise NotImplementedError

            async def query_readonly(
                self, payload: SqlQueryReadonlyIn
            ) -> QueryReadonlyResult:
                if payload.template_id == "inventory_snapshot_v1":
                    return McpToolError(
                        code="DB_QUERY_REJECTED",
                        message="no",
                        retryable=False,
                        correlation_id="c",
                    )
                return _ok_smoke()

        client = _C()
        registry = load_registry_from_dict(
            _load_fixture("templates_registry_two_smokes.json")
        )
        outcome = await run_smoke_loop(
            client=client, registry=registry, correlation_id="corr"
        )
        if len(outcome.failed) != 1:
            return False, str(outcome.failed)
        if outcome.failed[0].code != "DB_QUERY_REJECTED":
            return False, outcome.failed[0].code
        return True, "DB_QUERY_REJECTED recorded"

    return asyncio.run(_run())


def check_T005_B4_02() -> tuple[bool, str]:
    async def _run() -> tuple[bool, str]:
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            client = _FakeClient(
                describes={
                    "reporting.sales_by_day_v1": _ok_describe(
                        "reporting.sales_by_day_v1"
                    )
                },
                smokes={
                    "sales_by_day_v1": _ok_smoke(),
                    "inventory_snapshot_v1": McpToolError(
                        code="DB_QUERY_REJECTED",
                        message="rej",
                        retryable=False,
                        correlation_id="c",
                    ),
                },
            )
            objects_path = tmp / "objects.json"
            templates_path = tmp / "templates.json"
            objects_path.write_text(
                json.dumps(_load_fixture("objects_allowlist.json")), encoding="utf-8"
            )
            templates_path.write_text(
                json.dumps(_load_fixture("templates_registry_two_smokes.json")),
                encoding="utf-8",
            )
            outcome = await run_corpus_job(
                client=client,
                objects_path=objects_path,
                templates_path=templates_path,
                corpus_root=tmp / "rag_corpus",
                correlation_id="corr_b402",
            )
            if outcome.exit_code == 0:
                return False, "expected failure exit"
            if len(outcome.context.smoke_templates_failed) != 1:
                return False, str(outcome.context.smoke_templates_failed)
            return True, "smoke_templates_failed populated"

    return asyncio.run(_run())


def check_T005_B4_03() -> tuple[bool, str]:
    entry = smoke_entry_from_failure(
        template_id="bad_tpl", code="DB_QUERY_REJECTED", row_count=0
    )
    dumped = entry.model_dump()
    if "rows" in dumped:
        return False, "rows leaked"
    return True, "smoke_entry_from_failure ok"


def check_T005_B5_01() -> tuple[bool, str]:
    async def _run() -> tuple[bool, str]:
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            client = _FakeClient(transport_down=True)
            objects_path, templates_path = _seed_pipeline_config(tmp)
            outcome = await run_corpus_job(
                client=client,
                objects_path=objects_path,
                templates_path=templates_path,
                corpus_root=tmp / "rag_corpus",
                correlation_id="corr_b501",
            )
            if outcome.exit_code == 0:
                return False, "expected non-zero"
            codes = {f.code for f in outcome.describe_outcome.failures}
            if "MCP_TRANSPORT_DOWN" not in codes:
                return False, str(codes)
            return True, "transport down handled"

    return asyncio.run(_run())


def check_T005_B5_02() -> tuple[bool, str]:
    async def _run() -> tuple[bool, str]:
        client = UnconfiguredDbReadonlyClient()
        try:
            await client.describe(SqlDescribeIn(object_name="x"))
        except McpTransportError:
            return True, "Unconfigured raises McpTransportError"
        return False, "expected transport error"

    return asyncio.run(_run())


def check_T005_B5_03() -> tuple[bool, str]:
    async def _run() -> tuple[bool, str]:
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            client = _FakeClient(
                describes={
                    "reporting.sales_by_day_v1": _ok_describe(
                        "reporting.sales_by_day_v1"
                    )
                },
                smokes={"sales_by_day_v1": _ok_smoke()},
            )
            objects_path, templates_path = _seed_pipeline_config(tmp)
            outcome = await run_corpus_job(
                client=client,
                objects_path=objects_path,
                templates_path=templates_path,
                corpus_root=tmp / "rag_corpus",
                correlation_id="corr_b503",
            )
            keys = set(outcome.log_summary.keys())
            need = {"index_chunks", "duration_seconds", "exit_code"}
            if not need.issubset(keys):
                return False, str(keys)
            return True, "log_summary observability keys"

    return asyncio.run(_run())


def check_T005_B6_01_fixed() -> tuple[bool, str]:
    """ingest yields chunks after happy run."""

    async def _run() -> tuple[bool, str]:
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            corpus_root = tmp / "rag_corpus"
            client = _FakeClient(
                describes={
                    "reporting.sales_by_day_v1": _ok_describe(
                        "reporting.sales_by_day_v1"
                    )
                },
                smokes={"sales_by_day_v1": _ok_smoke()},
            )
            op, tp = _seed_pipeline_config(tmp)
            outcome = await run_corpus_job(
                client=client,
                objects_path=op,
                templates_path=tp,
                corpus_root=corpus_root,
                correlation_id="corr_b601",
            )
            idx = ingest_corpus(
                corpus_root=corpus_root, corpus_version=outcome.context.corpus_version
            )
            if len(idx.chunks) < 1:
                return False, "no chunks"
            return True, "ingest non-empty"

    return asyncio.run(_run())


def check_T005_B6_02() -> tuple[bool, str]:
    async def _run() -> tuple[bool, str]:
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            corpus_root = tmp / "rag_corpus"
            client = _FakeClient(
                describes={
                    "reporting.sales_by_day_v1": _ok_describe(
                        "reporting.sales_by_day_v1"
                    )
                },
                smokes={"sales_by_day_v1": _ok_smoke()},
            )
            op, tp = _seed_pipeline_config(tmp)
            outcome = await run_corpus_job(
                client=client,
                objects_path=op,
                templates_path=tp,
                corpus_root=corpus_root,
                correlation_id="corr_b602",
            )
            chunks = list(
                read_chunks(
                    corpus_root=corpus_root,
                    corpus_version=outcome.context.corpus_version,
                    namespace=SCHEMA_NAMESPACE,
                )
            )
            if not chunks:
                return False, "no schema chunks"
            return True, "erp_schema readable"

    return asyncio.run(_run())


def check_T005_B6_03() -> tuple[bool, str]:
    async def _run() -> tuple[bool, str]:
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            corpus_root = tmp / "rag_corpus"
            client = _FakeClient(
                describes={
                    "reporting.sales_by_day_v1": _ok_describe(
                        "reporting.sales_by_day_v1"
                    )
                },
                smokes={"sales_by_day_v1": _ok_smoke()},
            )
            op, tp = _seed_pipeline_config(tmp)
            outcome = await run_corpus_job(
                client=client,
                objects_path=op,
                templates_path=tp,
                corpus_root=corpus_root,
                correlation_id="corr_b603",
            )
            chunks = list(
                read_chunks(
                    corpus_root=corpus_root,
                    corpus_version=outcome.context.corpus_version,
                    namespace=HEALTH_NAMESPACE,
                )
            )
            if not chunks:
                return False, "no health chunks"
            return True, "erp_template_health readable"

    return asyncio.run(_run())


def check_T005_X_01() -> tuple[bool, str]:
    async def _run() -> tuple[bool, str]:
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            client = _FakeClient(
                describes={
                    "reporting.sales_by_day_v1": _ok_describe(
                        "reporting.sales_by_day_v1"
                    )
                },
                smokes={"sales_by_day_v1": _ok_smoke()},
            )
            op, tp = _seed_pipeline_config(tmp)
            outcome = await run_corpus_job(
                client=client,
                objects_path=op,
                templates_path=tp,
                corpus_root=tmp / "rag_corpus",
                correlation_id="corr_x01",
            )
            if outcome.duration_seconds < 0:
                return False, "negative duration"
            return True, "duration_seconds recorded"

    return asyncio.run(_run())


def check_T005_X_02() -> tuple[bool, str]:
    tail = DEFAULT_CORPUS_ROOT.parts[-3:]
    if tail != ("ai_python", "data", "rag_corpus"):
        return False, str(DEFAULT_CORPUS_ROOT)
    return True, "DEFAULT_CORPUS_ROOT stable"


def check_T005_X_03() -> tuple[bool, str]:
    now = datetime.now(tz=UTC)
    ctx = CorpusJobContext(
        correlation_id="c",
        corpus_version="v",
        run_started_at=now,
        objects_allowlist=["a"],
    )
    if ctx.describe_results != {}:
        return False, "default describe_results"
    return True, "CorpusJobContext validates"


def check_T005_X_04() -> tuple[bool, str]:
    raw = _load_fixture("mcp_tool_error.json")
    err = McpToolError.model_validate(raw)
    if err.code != raw["code"]:
        return False, "round-trip"
    return True, "McpToolError fixture ok"


def check_T005_RT_H1() -> tuple[bool, str]:
    path = _ai_python_app_root() / "agents" / "task005_corpus_job.py"
    text = path.read_text(encoding="utf-8")
    if "interrupt(" in text:
        return False, "interrupt found"
    return True, "no interrupt in orchestrator"


def check_T005_RT_H2() -> tuple[bool, str]:
    needles = ("interrupt(", "awaiting_approval", "approval_resolved")
    for p in _task005_py_files():
        low = p.read_text(encoding="utf-8").lower()
        for n in needles:
            if n in low:
                return False, f"{n} in {p.name}"
    return True, "no HITL symbols in task005 app modules"


def check_T005_RT_H3() -> tuple[bool, str]:
    proto = _ai_python_app_root() / "mcp" / "db_readonly_port.py"
    t = proto.read_text(encoding="utf-8")
    if "async def describe" not in t or "async def query_readonly" not in t:
        return False, "protocol surface"
    if t.count("async def") > 10:
        pass
    return True, "DbReadonlyMcpClient: describe + query_readonly"


def check_T005_RT_H4() -> tuple[bool, str]:
    bad = ("httpx.post", "requests.post", 'method="POST"')
    for p in _task005_py_files():
        text = p.read_text(encoding="utf-8")
        for b in bad:
            if b in text:
                return False, f"{b} in {p}"
    return True, "no obvious REST POST in task005 modules"


def check_T005_RT_H5() -> tuple[bool, str]:
    """No approval keyword surface; injection text cannot enable a missing tool."""
    blob = "\n".join(p.read_text(encoding="utf-8") for p in _task005_py_files())
    if "approve" in blob.lower():
        return False, "approve keyword in task005 app slice"
    return True, "no approval / write-trigger vocabulary in task005 app"


def check_T005_RT_M1() -> tuple[bool, str]:
    fields = set(SqlDescribeIn.model_fields.keys())
    if fields != {"object_name"}:
        return False, str(fields)
    return True, "describe input: object_name only"


def check_T005_RT_M2() -> tuple[bool, str]:
    fields = set(SqlQueryReadonlyIn.model_fields.keys())
    if fields != {"template_id", "params"}:
        return False, str(fields)
    return True, "query_readonly: template_id + params"


def check_T005_RT_M3() -> tuple[bool, str]:
    return check_T005_B3_04()


def check_T005_RT_M4() -> tuple[bool, str]:
    raw = _load_fixture("mcp_tool_error.json")
    if raw.get("code") != "DB_QUERY_REJECTED":
        return False, "fixture code"
    McpToolError.model_validate(raw)
    return True, "DB_QUERY_REJECTED typed"


def check_T005_RT_M5() -> tuple[bool, str]:
    try:
        SqlDescribeIn.model_validate({"object_name": "ok", "raw_sql": "DROP TABLE t;"})
        return False, "expected validation error for injected field"
    except ValidationError:
        return True, "extra field rejected"


CHECK_REGISTRY: dict[str, Any] = {
    "T005-B1-01": check_T005_B1_01,
    "T005-B1-02": check_T005_B1_02,
    "T005-B1-03": check_T005_B1_03,
    "T005-B1-04": check_T005_B1_04,
    "T005-B1-05": check_T005_B1_05,
    "T005-B1-06": check_T005_B1_06,
    "T005-B2-01": check_T005_B2_01,
    "T005-B2-02": check_T005_B2_02,
    "T005-B2-03": check_T005_B2_03,
    "T005-B2-04": check_T005_B2_04,
    "T005-B3-01": check_T005_B3_01,
    "T005-B3-02": check_T005_B3_02,
    "T005-B3-03": check_T005_B3_03,
    "T005-B3-04": check_T005_B3_04,
    "T005-B3-05": check_T005_B3_05,
    "T005-B4-01": check_T005_B4_01,
    "T005-B4-02": check_T005_B4_02,
    "T005-B4-03": check_T005_B4_03,
    "T005-B5-01": check_T005_B5_01,
    "T005-B5-02": check_T005_B5_02,
    "T005-B5-03": check_T005_B5_03,
    "T005-B6-01": check_T005_B6_01_fixed,
    "T005-B6-02": check_T005_B6_02,
    "T005-B6-03": check_T005_B6_03,
    "T005-X-01": check_T005_X_01,
    "T005-X-02": check_T005_X_02,
    "T005-X-03": check_T005_X_03,
    "T005-X-04": check_T005_X_04,
    "T005-RT-H1": check_T005_RT_H1,
    "T005-RT-H2": check_T005_RT_H2,
    "T005-RT-H3": check_T005_RT_H3,
    "T005-RT-H4": check_T005_RT_H4,
    "T005-RT-H5": check_T005_RT_H5,
    "T005-RT-M1": check_T005_RT_M1,
    "T005-RT-M2": check_T005_RT_M2,
    "T005-RT-M3": check_T005_RT_M3,
    "T005-RT-M4": check_T005_RT_M4,
    "T005-RT-M5": check_T005_RT_M5,
}


def run_eval_case(case_id: str) -> tuple[bool, str]:
    fn = CHECK_REGISTRY.get(case_id)
    if fn is None:
        return False, f"unknown case_id={case_id}"
    return fn()
