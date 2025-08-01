import psycopg2

BATCH_SIZE = 1000

DEV_PG_CONFIG = {
    "host": "127.0.0.1",
    "port": 5432,
    "user": "postgres",
    "password": "difyai123456",
    "dbname": "brazilian_e_commerce"
}

TEST_PG_CONFIG = {
    "host": "192.168.8.12",
    "port": 5433,
    "user": "postgres",
    "password": "difyai123456",
    "dbname": "brazilian_e_commerce"
}


def get_connection(cfg):
    return psycopg2.connect(
        host=cfg["host"],
        port=cfg["port"],
        user=cfg["user"],
        password=cfg["password"],
        dbname=cfg["dbname"]
    )


def get_all_tables(cursor):
    cursor.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema='public' AND table_type='BASE TABLE';
    """)
    return [row[0] for row in cursor.fetchall()]


def get_column_names(cursor, table):
    cursor.execute(f"""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema='public' AND table_name=%s
        ORDER BY ordinal_position;
    """, (table,))
    return [row[0] for row in cursor.fetchall()]


def migrate_table(src_conn, tgt_conn, table):
    src_cur = src_conn.cursor()
    tgt_cur = tgt_conn.cursor()

    columns = get_column_names(src_cur, table)
    placeholders = ','.join(['%s'] * len(columns))
    insert_sql = f'INSERT INTO "{table}" ({", ".join(columns)}) VALUES ({placeholders})'

    print(f"\n📦 正在迁移表：{table}")

    src_cur.execute(f'SELECT * FROM "{table}"')
    total_inserted = 0

    while True:
        rows = src_cur.fetchmany(BATCH_SIZE)
        if not rows:
            break
        tgt_cur.executemany(insert_sql, rows)
        tgt_conn.commit()
        total_inserted += len(rows)
        print(f"📥 已迁移 {total_inserted} 行", end="\r")

    print(f"✅ 表 {table} 迁移完成，共 {total_inserted} 行")
    src_cur.close()
    tgt_cur.close()


def main():
    src_conn = get_connection(DEV_PG_CONFIG)
    tgt_conn = get_connection(TEST_PG_CONFIG)

    src_cur = src_conn.cursor()
    tables = get_all_tables(src_cur)
    src_cur.close()

    for table in tables:
        migrate_table(src_conn, tgt_conn, table)

    src_conn.close()
    tgt_conn.close()
    print("\n🎉 所有表已成功迁移至测试环境！")


if __name__ == "__main__":
    main()
