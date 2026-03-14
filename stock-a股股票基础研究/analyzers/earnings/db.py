#!/usr/bin/env python3
"""
SQLite 工具函数
"""

import argparse
import sqlite3
from pathlib import Path

from config import DB_PATH

SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def connect(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """连接数据库"""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def run_migrations(conn: sqlite3.Connection):
    """执行建表脚本"""
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    conn.executescript(schema)
    conn.commit()


def fetch_existing(conn: sqlite3.Connection, table: str, unique_cols: list, row: dict):
    """查询已存在记录"""
    where = " AND ".join([f"{col} = ?" for col in unique_cols])
    sql = f"SELECT * FROM {table} WHERE {where} LIMIT 1"
    values = [row.get(col) for col in unique_cols]
    cur = conn.execute(sql, values)
    result = cur.fetchone()
    return dict(result) if result else None


def upsert_rows(conn: sqlite3.Connection, table: str, rows: list, unique_cols: list, preserve_on_update: list = None) -> int:
    """批量 upsert
    
    Args:
        preserve_on_update: 这些字段在更新时保留原值（仅 INSERT 时写入）
    """
    if not rows:
        return 0

    preserve_on_update = preserve_on_update or []

    all_cols = []
    for row in rows:
        for key in row.keys():
            if key not in all_cols:
                all_cols.append(key)

    placeholders = ", ".join(["?"] * len(all_cols))
    columns_sql = ", ".join(all_cols)
    conflict_sql = ", ".join(unique_cols)
    update_cols = [c for c in all_cols if c not in unique_cols]
    
    # preserve_on_update 的字段保留原值，其他字段用新值覆盖
    update_parts = []
    for c in update_cols:
        if c in preserve_on_update:
            update_parts.append(f"{c} = COALESCE({table}.{c}, excluded.{c})")
        else:
            update_parts.append(f"{c} = excluded.{c}")
    update_sql = ", ".join(update_parts)

    sql = (
        f"INSERT INTO {table} ({columns_sql}) "
        f"VALUES ({placeholders}) "
        f"ON CONFLICT({conflict_sql}) DO UPDATE SET {update_sql}"
    )

    values = []
    for row in rows:
        values.append([row.get(col) for col in all_cols])

    conn.executemany(sql, values)
    conn.commit()
    return len(rows)


def init_db():
    """初始化数据库"""
    conn = connect()
    run_migrations(conn)
    conn.close()


def main():
    parser = argparse.ArgumentParser(description="初始化数据库")
    parser.add_argument("--init", action="store_true", help="创建数据库与表")
    args = parser.parse_args()

    if args.init:
        init_db()
        print(f"数据库已初始化: {DB_PATH}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
