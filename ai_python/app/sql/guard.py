from __future__ import annotations
import sqlparse

class SqlGuardError(Exception):
    """SQL khong phai truy van doc -> tu choi thuc thi, tra loi an toan."""

_FORBIDDEN = {"INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE",
              "CREATE", "GRANT", "REVOKE", "MERGE", "REPLACE", "CALL", "EXECUTE"}


def assert_read_only(sql: str) -> None:
    statements = [s for s in sqlparse.parse(sql) if str(s).strip()]
    if len(statements) != 1:
        raise SqlGuardError("Chi cho phep dung 1 cau lenh SELECT")
    stmt = statements[0]
    stmt_type = stmt.get_type()       # 'SELECT' | 'INSERT' | 'UNKNOWN'...
    if stmt_type != "SELECT":
        raise SqlGuardError(f"Cau lenh khong phai SELECT: {stmt_type}")
    upper_tokens = {t.value.upper() for t in stmt.flatten()
                    if t.ttype in (sqlparse.tokens.Keyword,
                                   sqlparse.tokens.Keyword.DDL,
                                   sqlparse.tokens.Keyword.DML)}
    bad = _FORBIDDEN & upper_tokens
    if bad:
        raise SqlGuardError(f"Tu khoa bi cam: {', '.join(sorted(bad))}")
    if "INTO" in upper_tokens:        # SELECT ... INTO ghi bang moi
        raise SqlGuardError("SELECT INTO bi cam (ghi du lieu)")
