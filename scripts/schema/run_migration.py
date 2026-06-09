"""Run schema enrichment SQL scripts against the target Postgres."""
import psycopg2

SCRIPTS = [
    "create_relationship_registry.sql",
    "seed_column_descriptions.sql",
    "seed_relationship_descriptions.sql",
]

conn = psycopg2.connect("postgresql://smart_erp:smart_erp@127.0.0.1:5432/smart_erp")
cur = conn.cursor()

for fname in SCRIPTS:
    path = __file__.rsplit("\\", 1)[0] + "\\" + fname
    sql = open(path, encoding="utf-8").read()
    cur.execute(sql)
    conn.commit()
    print(f"OK  {fname}")

cur.execute("SELECT count(*) FROM ai_relationship_description")
cnt = cur.fetchone()[0]
print(f"OK  ai_relationship_description has {cnt} rows")

cur.execute(
    "SELECT count(*) FROM ai_column_description "
    "WHERE position('KHONG' in description) > 0"
)
scnt = cur.fetchone()[0]
print(f"OK  ai_column_description has {scnt} rows with KHONG rule")

cur.close()
conn.close()
print("Done")
