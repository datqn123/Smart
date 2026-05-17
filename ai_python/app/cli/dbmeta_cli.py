"""CLI — validate or scan DB schema YAML artifacts (Task006)."""

from __future__ import annotations

import argparse
import pathlib
import sys

import yaml

from app.graph.dbmeta import load_schema_yaml_path
from app.graph.dbmeta_scan import scan_database_url


def cmd_validate(args: argparse.Namespace) -> int:
    path = pathlib.Path(args.path)
    art = load_schema_yaml_path(path)
    if getattr(args, "strict", False) and not art.generated_at and not art.updated_at:
        print(
            "validation failed: strict mode requires generated_at or updated_at",
            file=sys.stderr,
        )
        return 2
    print(f"OK schema_version={art.schema_version} tables={len(art.tables)}")
    return 0


def cmd_scan(args: argparse.Namespace) -> int:
    art = scan_database_url(args.url, schema_version=args.schema_version)
    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = art.model_dump(mode="json")
    out.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
    print(f"wrote {out} ({len(art.tables)} tables)")
    return 0


def main() -> None:
    p = argparse.ArgumentParser(prog="python -m app.cli.dbmeta_cli")
    sub = p.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("validate", help="Validate a schema YAML file against SchemaArtifact")
    v.add_argument("path", type=str)
    v.add_argument(
        "--strict",
        action="store_true",
        help="Require generated_at or updated_at",
    )
    v.set_defaults(func=cmd_validate)

    s = sub.add_parser("scan", help="Scan a database URL and write schema YAML")
    s.add_argument("--url", required=True, help="SQLAlchemy URL (e.g. sqlite:///./db.sqlite)")
    s.add_argument("--schema-version", required=True, dest="schema_version")
    s.add_argument("--out", required=True, help="Output YAML path")
    s.set_defaults(func=cmd_scan)

    args = p.parse_args()
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
