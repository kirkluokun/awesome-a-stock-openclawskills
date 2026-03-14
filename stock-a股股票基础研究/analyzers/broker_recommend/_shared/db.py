"""券商金股数据库工具"""

import sqlite3
from pathlib import Path

from config import DB_PATH

SCHEMA_PATH = Path(__file__).parent.parent / "schema.sql"


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_table():
    """初始化券商金股表"""
    conn = connect()
    try:
        schema = SCHEMA_PATH.read_text(encoding="utf-8")
        conn.executescript(schema)
        conn.commit()
    finally:
        conn.close()


def upsert_recommendations(rows: list[dict]) -> int:
    """批量插入金股数据，返回插入条数"""
    if not rows:
        return 0
    conn = connect()
    try:
        sql = """
            INSERT INTO broker_recommend (month, broker, ts_code, name)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(month, broker, ts_code) DO UPDATE SET
                name = excluded.name
        """
        values = [
            (r.get("month"), r.get("broker"), r.get("ts_code"), r.get("name"))
            for r in rows
        ]
        conn.executemany(sql, values)
        conn.commit()
        return len(rows)
    finally:
        conn.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="券商金股数据库工具")
    parser.add_argument("--init", action="store_true", help="初始化表")
    args = parser.parse_args()
    
    if args.init:
        init_table()
        print(f"表已初始化: {DB_PATH}")
    else:
        parser.print_help()
