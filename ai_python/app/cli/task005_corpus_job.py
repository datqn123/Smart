"""CLI entrypoint for the Task005 batch corpus pipeline.

Usage::

    python -m app.cli.task005_corpus_job \\
        --objects ai_python/data/config/objects.json \\
        --templates ai_python/data/config/templates.json \\
        --corpus-root ai_python/data/rag_corpus

The CLI is async-friendly: tests inject a fake MCP client; the production
binding is left to a separate adapter (out of scope for v1).
"""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from app.agents.task005_corpus_job import run_corpus_job
from app.mcp.db_readonly_port import DbReadonlyMcpClient
from app.tools.task005_corpus_fs import DEFAULT_CORPUS_ROOT
from app.tools.task005_logging import get_logger, log_event


def build_arg_parser() -> argparse.ArgumentParser:
    """Construct the CLI argument parser used by ``run_cli``."""

    parser = argparse.ArgumentParser(
        prog="task005-corpus-job",
        description="Refresh ERP RAG corpus via MCP db-readonly (Option B).",
    )
    parser.add_argument(
        "--objects",
        type=Path,
        required=True,
        help="Path to JSON file with `objects` allowlist.",
    )
    parser.add_argument(
        "--templates",
        type=Path,
        required=True,
        help="Path to JSON template registry file.",
    )
    parser.add_argument(
        "--corpus-root",
        type=Path,
        default=DEFAULT_CORPUS_ROOT,
        help="Output corpus root (default: ai_python/data/rag_corpus).",
    )
    parser.add_argument(
        "--correlation-id",
        type=str,
        default=None,
        help="Optional correlation id (default: generated UUID).",
    )
    return parser


def run_cli(
    *,
    argv: list[str] | None = None,
    client: DbReadonlyMcpClient,
) -> int:
    """Run the CLI with an injected MCP client; return the process exit code."""

    parser = build_arg_parser()
    args = parser.parse_args(argv)

    logger = get_logger()
    correlation_id = args.correlation_id

    try:
        outcome = asyncio.run(
            run_corpus_job(
                client=client,
                objects_path=args.objects,
                templates_path=args.templates,
                corpus_root=args.corpus_root,
                correlation_id=correlation_id,
            )
        )
    except Exception as err:
        log_event(
            logger,
            event="run.crashed",
            correlation_id=correlation_id or "unknown",
            error=str(err),
        )
        return 2

    return outcome.exit_code
