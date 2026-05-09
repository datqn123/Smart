"""Task005 batch corpus pipeline orchestrator.

Sequence (per ADR-003 / SRS §5):

1. Resolve config (objects allowlist + template registry).
2. Run ``sql.describe`` for each allowlisted object.
3. Persist atomic catalog artifact.
4. Run ``sql.query_readonly`` smoke for each registered ``smoke_safe`` template.
5. Persist atomic health artifact.
6. Run local RAG ingest over the fresh corpus.
7. Build a final structured summary + exit code.

Exit policy (SRS OQ-02 default): partial failures continue but produce a
non-zero exit code so cron / runner can react.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.cli.task005_config import load_job_config
from app.contracts.task005 import (
    CorpusJobContext,
    SmokeTemplateFailure,
)
from app.mcp.db_readonly_port import DbReadonlyMcpClient
from app.rag.task005_ingest import LocalRagIndex, ingest_corpus
from app.tools.task005_artifacts import (
    SchemaCatalogArtifact,
    SmokeHealthArtifact,
)
from app.tools.task005_corpus_fs import (
    atomic_write_json,
    build_corpus_paths,
    iso_corpus_version,
)
from app.tools.task005_describe import DescribeLoopOutcome, run_describe_loop
from app.tools.task005_logging import get_logger, log_event
from app.tools.task005_smoke import SmokeLoopOutcome, run_smoke_loop


@dataclass
class RunOutcome:
    """High-level result of one batch run."""

    context: CorpusJobContext
    describe_outcome: DescribeLoopOutcome
    smoke_outcome: SmokeLoopOutcome
    index: LocalRagIndex
    exit_code: int
    duration_seconds: float = 0.0
    catalog_path: Path | None = None
    health_path: Path | None = None
    log_summary: dict[str, Any] = field(default_factory=dict)

    @property
    def index_chunks(self) -> int:
        return len(self.index.chunks)


def _new_correlation_id() -> str:
    return f"corr_{uuid.uuid4().hex[:12]}"


async def run_corpus_job(
    *,
    client: DbReadonlyMcpClient,
    objects_path: Path,
    templates_path: Path,
    corpus_root: Path,
    correlation_id: str | None = None,
    now: datetime | None = None,
) -> RunOutcome:
    """Run one full batch pipeline."""

    logger = get_logger()
    started_at = now or datetime.now(tz=UTC)
    actual_correlation_id = correlation_id or _new_correlation_id()
    corpus_version = iso_corpus_version(started_at)

    config = load_job_config(
        objects_path=objects_path,
        templates_path=templates_path,
        corpus_root=corpus_root,
    )

    log_event(
        logger,
        event="run.started",
        correlation_id=actual_correlation_id,
        objects_count=len(config.objects),
        templates_count=len(config.registry.templates),
        corpus_version=corpus_version,
    )

    paths = build_corpus_paths(corpus_root, corpus_version)

    describe_outcome = await run_describe_loop(
        client=client,
        objects=config.objects,
        correlation_id=actual_correlation_id,
    )

    catalog_artifact = SchemaCatalogArtifact(
        corpus_version=corpus_version,
        correlation_id=actual_correlation_id,
        objects=describe_outcome.catalog_entries,
    )
    atomic_write_json(paths.catalog_path, catalog_artifact.model_dump())

    smoke_outcome = await run_smoke_loop(
        client=client,
        registry=config.registry,
        correlation_id=actual_correlation_id,
    )

    health_artifact = SmokeHealthArtifact(
        corpus_version=corpus_version,
        correlation_id=actual_correlation_id,
        smoke=smoke_outcome.entries,
    )
    atomic_write_json(paths.health_path, health_artifact.model_dump())

    index = ingest_corpus(corpus_root=corpus_root, corpus_version=corpus_version)

    finished_at = datetime.now(tz=UTC)
    duration = (finished_at - started_at).total_seconds()

    context = CorpusJobContext(
        correlation_id=actual_correlation_id,
        corpus_version=corpus_version,
        run_started_at=started_at,
        run_finished_at=finished_at,
        objects_allowlist=list(config.objects),
        describe_results=dict(describe_outcome.results),
        smoke_templates_tried=list(smoke_outcome.tried),
        smoke_templates_ok=list(smoke_outcome.passed),
        smoke_templates_failed=[
            SmokeTemplateFailure(template_id=fail.template_id, code=fail.code)
            for fail in smoke_outcome.failed
        ],
    )

    has_failures = describe_outcome.has_failures or smoke_outcome.has_failures
    exit_code = 1 if has_failures else 0

    summary: dict[str, Any] = {
        "objects_described_ok": sum(
            1 for status in describe_outcome.results.values() if status == "ok"
        ),
        "objects_described_failed": len(describe_outcome.failures),
        "smoke_templates_ok": len(smoke_outcome.passed),
        "smoke_templates_failed": len(smoke_outcome.failed),
        "index_chunks": len(index.chunks),
        "duration_seconds": duration,
        "exit_code": exit_code,
    }

    log_event(
        logger,
        event="run.finished",
        correlation_id=actual_correlation_id,
        **summary,
    )

    return RunOutcome(
        context=context,
        describe_outcome=describe_outcome,
        smoke_outcome=smoke_outcome,
        index=index,
        exit_code=exit_code,
        duration_seconds=duration,
        catalog_path=paths.catalog_path,
        health_path=paths.health_path,
        log_summary=summary,
    )
