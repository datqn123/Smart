from __future__ import annotations

import sqlglot
from sqlglot import exp


class SqlValidationError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


def _parse_single(sql_raw: str) -> exp.Expression:
    sql = sql_raw.strip()
    if not sql:
        raise SqlValidationError("VALIDATION_FAILED", "empty SQL")
    try:
        stmts = sqlglot.parse(sql, dialect="sqlite")
    except sqlglot.errors.ParseError as e:
        raise SqlValidationError("VALIDATION_FAILED", f"parse error: {e}") from e
    if len(stmts) != 1:
        raise SqlValidationError("VALIDATION_FAILED", "expected exactly one statement")
    stmt = stmts[0]
    if stmt is None:
        raise SqlValidationError("VALIDATION_FAILED", "empty parse tree")
    return stmt


def _assert_select_only(tree: exp.Expression) -> None:
    if isinstance(tree, exp.Union):
        raise SqlValidationError("VALIDATION_FAILED", "UNION is not allowed in v1")
    if not isinstance(tree, exp.Select):
        raise SqlValidationError("VALIDATION_FAILED", "only SELECT is allowed")
    forbidden = (
        exp.Insert,
        exp.Update,
        exp.Delete,
        exp.Drop,
        exp.Create,
        exp.Alter,
    )
    for node in tree.walk():
        if isinstance(node, forbidden):
            raise SqlValidationError("FORBIDDEN", "DML/DDL constructs are not allowed")


def referenced_tables(tree: exp.Expression) -> set[str]:
    names: set[str] = set()
    for t in tree.find_all(exp.Table):
        if t.name:
            names.add(t.name.lower())
    return names


def validate_select(sql: str, allowed_tables: set[str]) -> exp.Expression:
    tree = _parse_single(sql)
    _assert_select_only(tree)
    refs = referenced_tables(tree)
    if not refs:
        raise SqlValidationError("VALIDATION_FAILED", "no tables referenced in SELECT")
    allowed_l = {a.lower() for a in allowed_tables}
    extra = refs - allowed_l
    if extra:
        raise SqlValidationError(
            "SCOPE_VIOLATION",
            f"tables not in allowlist: {sorted(extra)}",
        )
    return tree


def transpile_to_sqlite(sql: str) -> str:
    out = sqlglot.transpile(sql.strip(), read="sqlite", write="sqlite")
    if not out:
        raise SqlValidationError("VALIDATION_FAILED", "could not transpile SQL")
    return out[0]
