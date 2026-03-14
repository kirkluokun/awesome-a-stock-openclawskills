"""研报数据库工具"""

import sqlite3
from pathlib import Path

from config import DB_PATH

SCHEMA_PATH = Path(__file__).parent.parent / "schema.sql"


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_table():
    """初始化研报表"""
    conn = connect()
    try:
        schema = SCHEMA_PATH.read_text(encoding="utf-8")
        conn.executescript(schema)
        conn.commit()
    finally:
        conn.close()


def upsert_reports(rows: list[dict]) -> int:
    """批量插入研报元数据，返回插入条数"""
    if not rows:
        return 0
    conn = connect()
    try:
        sql = """
            INSERT INTO research_report 
            (trade_date, ts_code, name, title, abstr, report_type, author, inst_csname, ind_name, url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET
                trade_date = excluded.trade_date,
                ts_code = excluded.ts_code,
                name = excluded.name,
                title = excluded.title,
                abstr = excluded.abstr,
                report_type = excluded.report_type,
                author = excluded.author,
                inst_csname = excluded.inst_csname,
                ind_name = excluded.ind_name
        """
        values = [
            (r.get("trade_date"), r.get("ts_code"), r.get("name"), r.get("title"),
             r.get("abstr"), r.get("report_type"), r.get("author"), 
             r.get("inst_csname"), r.get("ind_name"), r.get("url"))
            for r in rows
        ]
        conn.executemany(sql, values)
        conn.commit()
        return len(rows)
    finally:
        conn.close()


def update_local_path(report_id: int, local_path: str):
    """更新本地路径"""
    conn = connect()
    try:
        conn.execute(
            "UPDATE research_report SET local_path = ? WHERE id = ?",
            (local_path, report_id)
        )
        conn.commit()
    finally:
        conn.close()


def update_parsed_at(report_id: int, parsed_at: str):
    """更新解析时间"""
    conn = connect()
    try:
        conn.execute(
            "UPDATE research_report SET parsed_at = ? WHERE id = ?",
            (parsed_at, report_id)
        )
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="研报数据库工具")
    parser.add_argument("--init", action="store_true", help="初始化表")
    args = parser.parse_args()

    if args.init:
        init_table()
        print(f"表已初始化: {DB_PATH}")
    else:
        parser.print_help()
