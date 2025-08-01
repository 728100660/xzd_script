import sqlite3
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

SQLITE_FILE = "Brazilian_E_Commerce.sqlite"
PG_HOST = "127.0.0.1"
PG_PORT = 5432
PG_USER = "postgres"
PG_PASSWORD = "difyai123456"
PG_DB_NAME = "brazilian_e_commerce"
BATCH_SIZE = 1000  # 每批插入多少行


def create_postgres_database():
    conn = psycopg2.connect(
        dbname='postgres', user=PG_USER, password=PG_PASSWORD,
        host=PG_HOST, port=PG_PORT
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{PG_DB_NAME}';")
    if not cur.fetchone():
        cur.execute(f"CREATE DATABASE {PG_DB_NAME};")
        print(f"✅ 数据库 {PG_DB_NAME} 已创建")
    else:
        print(f"ℹ️ 数据库 {PG_DB_NAME} 已存在")
    cur.close()
    conn.close()


# ---------- 连接 SQLite 和 PostgreSQL ----------
sqlite_conn = sqlite3.connect(SQLITE_FILE)
sqlite_cursor = sqlite_conn.cursor()

create_postgres_database()

pg_conn = psycopg2.connect(
    dbname=PG_DB_NAME, user=PG_USER, password=PG_PASSWORD,
    host=PG_HOST, port=PG_PORT
)
pg_cursor = pg_conn.cursor()

# ---------- 获取 SQLite 所有表 ----------
sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [row[0] for row in sqlite_cursor.fetchall()]

# ---------- 遍历所有表 ----------
for table in tables:
    print(f"\n📦 正在迁移表：{table}")

    # 获取字段信息
    sqlite_cursor.execute(f"PRAGMA table_info({table})")
    columns_info = sqlite_cursor.fetchall()
    col_names = [col[1] for col in columns_info]
    placeholders = ','.join(['%s'] * len(col_names))
    insert_sql = f'INSERT INTO "{table}" ({", ".join(col_names)}) VALUES ({placeholders})'

    # 检查目标表是否存在
    pg_cursor.execute(
        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = %s);",
        (table,)
    )
    exists = pg_cursor.fetchone()[0]
    if not exists:
        print(f"⚠️ PostgreSQL 中未找到表 {table}，请先手动建表。")
        continue

    # 分批读取和写入
    sqlite_cursor.execute(f'SELECT * FROM "{table}"')
    total_inserted = 0
    while True:
        batch = sqlite_cursor.fetchmany(BATCH_SIZE)
        if not batch:
            break
        pg_cursor.executemany(insert_sql, batch)
        pg_conn.commit()
        total_inserted += len(batch)
        print(f"📥 已导入 {total_inserted} 行...", end="\r")

    print(f"✅ 表 {table} 导入完成，共 {total_inserted} 行")

# ---------- 清理资源 ----------
sqlite_cursor.close()
sqlite_conn.close()
pg_cursor.close()
pg_conn.close()

print("\n🎉 所有表已成功迁移到 PostgreSQL！")
