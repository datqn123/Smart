"""Entry: ``python -m app.smart_erp_mcp`` (stdio MCP)."""

from __future__ import annotations

from .server import run_stdio


def main() -> None:
    run_stdio()


if __name__ == "__main__":
    main()
