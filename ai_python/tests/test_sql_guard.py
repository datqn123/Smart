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
