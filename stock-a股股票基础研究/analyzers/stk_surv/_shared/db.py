"""机构调研数据库工具"""

import sqlite3
from pathlib import Path

from config import DB_PATH

SCHEMA_PATH = Path(__file__).parent.parent / "schema.sql"


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_tables():
    """初始化调研表"""
    conn = connect()
    try:
        schema = SCHEMA_PATH.read_text(encoding="utf-8")
        conn.executescript(schema)
        conn.commit()
    finally:
        conn.close()


def upsert_event(row: dict) -> int:
    """插入或更新调研事件，返回event_id"""
    conn = connect()
    try:
        sql = """
            INSERT INTO stk_surv_event 
            (ts_code, name, surv_date, rece_place, rece_mode, comp_rece, content)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(ts_code, surv_date) DO UPDATE SET
                name = excluded.name,
                rece_place = excluded.rece_place,
                rece_mode = excluded.rece_mode,
                comp_rece = excluded.comp_rece,
                content = COALESCE(excluded.content, stk_surv_event.content)
        """
        cur = conn.execute(sql, (
            row.get("ts_code"), row.get("name"), row.get("surv_date"),
            row.get("rece_place"), row.get("rece_mode"), row.get("comp_rece"),
            row.get("content")
        ))
        conn.commit()
        
        # 获取event_id
        cur = conn.execute(
            "SELECT id FROM stk_surv_event WHERE ts_code = ? AND surv_date = ?",
            (row.get("ts_code"), row.get("surv_date"))
        )
        return cur.fetchone()["id"]
    finally:
        conn.close()


def upsert_participants(event_id: int, participants: list[dict]) -> int:
    """批量插入参与人员"""
    if not participants:
        return 0
    conn = connect()
    try:
        sql = """
            INSERT INTO stk_surv_participant (event_id, fund_visitors, rece_org, org_type)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(event_id, fund_visitors, rece_org) DO UPDATE SET
                org_type = excluded.org_type
        """
        values = [
            (event_id, p.get("fund_visitors"), p.get("rece_org"), p.get("org_type"))
            for p in participants
        ]
        conn.executemany(sql, values)
        conn.commit()
        return len(participants)
    finally:
        conn.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="机构调研数据库工具")
    parser.add_argument("--init", action="store_true", help="初始化表")
    args = parser.parse_args()
    
    if args.init:
        init_tables()
        print(f"表已初始化: {DB_PATH}")
    else:
        parser.print_help()
