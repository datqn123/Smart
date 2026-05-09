"""Scheduled / daily entrypoint for the Task005 corpus pipeline (SRS §7 AC6).

Resolves default paths under ``ai_python/data/config/`` and
``data/rag_corpus`` so operators can run::

    cd ai_python
    python -m app.cli.task005_daily

Pass-through arguments override defaults (same options as
:func:`app.cli.task005_corpus_job.build_arg_parser`). MCP transport is selected
via :func:`app.mcp.task005_client_factory.build_db_readonly_client_from_env`.
"""

from __future__ import annotations

import sys
from pathlib import Path

from app.cli.task005_corpus_job import run_cli
from app.mcp.task005_client_factory import build_db_readonly_client_from_env
from app.tools.task005_corpus_fs import DEFAULT_CORPUS_ROOT

_CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "config"
_DEFAULT_OBJECTS = _CONFIG_DIR / "objects.json"
_DEFAULT_TEMPLATES = _CONFIG_DIR / "templates.json"


def main() -> None:
    """Parse argv (or inject default corpus paths) and run the batch CLI."""

    argv = list(sys.argv[1:])
    if not argv:
        argv = [
            "--objects",
            str(_DEFAULT_OBJECTS),
            "--templates",
            str(_DEFAULT_TEMPLATES),
            "--corpus-root",
            str(DEFAULT_CORPUS_ROOT),
        ]
    client = build_db_readonly_client_from_env()
    raise SystemExit(run_cli(argv=argv, client=client))


if __name__ == "__main__":
    main()
