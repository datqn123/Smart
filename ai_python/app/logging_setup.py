"""Ensure ``app.*`` INFO logs reach the console when running under uvicorn.

Uvicorn's default ``LOGGING_CONFIG`` only attaches handlers to ``uvicorn*`` loggers.
The root logger stays at WARNING, so ``logger.info`` on ``app.graph…`` is dropped.
"""

from __future__ import annotations

import logging
import sys

from app.graph.correlation import CorrelationFilter

_APP_STDERR_HANDLER_ATTR = "_ai_python_app_stderr"


def setup_app_package_stderr_logging(level: int = logging.INFO) -> None:
    """Attach one stderr :class:`~logging.StreamHandler` to the ``app`` logger if missing."""
    app_pkg = logging.getLogger("app")
    app_pkg.setLevel(level)
    for h in app_pkg.handlers:
        if getattr(h, _APP_STDERR_HANDLER_ATTR, False):
            return
    handler = logging.StreamHandler(sys.stderr)
    setattr(handler, _APP_STDERR_HANDLER_ATTR, True)
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
    handler.addFilter(CorrelationFilter())
    app_pkg.addHandler(handler)
