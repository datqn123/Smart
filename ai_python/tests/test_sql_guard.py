import pytest
from app.sql.guard import assert_read_only, SqlGuardError


@pytest.mark.parametrize("sql", [
    "SELECT * FROM customers",
    "  select id from orders where total > 10  ",
    "WITH t AS (SELECT 1) SELECT * FROM t",
])
def test_allows_select(sql):  # fact-sql-execute
    assert_read_only(sql)  # khong raise


@pytest.mark.parametrize("sql", [
    "INSERT INTO t VALUES (1)",
    "UPDATE t SET x=1",
    "DELETE FROM t",
    "DROP TABLE t",
    "ALTER TABLE t ADD c int",
    "TRUNCATE t",
    "GRANT ALL ON t TO u",
    "SELECT 1; DROP TABLE t",          # multi-statement injection
    "SELECT * INTO new_t FROM t",      # SELECT INTO ghi du lieu
])
def test_blocks_non_select(sql):  # fact-sql-guard
    with pytest.raises(SqlGuardError):
        assert_read_only(sql)


@pytest.mark.parametrize("sql", [
    # Postgres data-modifying CTE: get_type() == "SELECT" nhung phai bi chan
    # boi token-scan tim DML trong CTE (fact-sql-guard, defense-in-depth).
    "WITH t AS (DELETE FROM x RETURNING *) SELECT * FROM t",
    "WITH t AS (UPDATE x SET a=1 RETURNING *) SELECT * FROM t",
    "WITH t AS (INSERT INTO x VALUES (1) RETURNING *) SELECT * FROM t",
    "SELECT 1 -- c\n; DROP TABLE t",   # comment + multi-statement injection
])
def test_blocks_data_modifying_cte_and_injection(sql):  # fact-sql-guard
    with pytest.raises(SqlGuardError):
        assert_read_only(sql)


def test_allows_select_with_comment():
    assert_read_only("select * from customers /* ok */")  # khong raise
