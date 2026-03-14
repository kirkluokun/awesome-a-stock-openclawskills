"""现金流量表数据库工具"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from config import DB_PATH

SCHEMA_PATH = Path(__file__).parent.parent / "schema.sql"


def connect(db_path: Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_table(conn: sqlite3.Connection = None):
    if conn is None:
        conn = connect()
        should_close = True
    else:
        should_close = False
    try:
        schema = SCHEMA_PATH.read_text(encoding="utf-8")
        conn.executescript(schema)
        conn.commit()
    finally:
        if should_close:
            conn.close()


def upsert_cashflow(conn: sqlite3.Connection, rows: list) -> int:
    if not rows:
        return 0

    base_cols = [
        "ts_code", "ann_date", "end_date",
        "n_cashflow_act", "n_cashflow_inv", "n_cashflow_fin",
        "c_cash_equ_beg_period", "c_cash_equ_end_period",
        "c_inf_fr_operate_a", "c_outf_operate_a",
    ]

    unique_cols = ["ts_code", "end_date"]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db_rows = []
    for row in rows:
        db_row = {col: row.get(col) for col in base_cols}
        if not db_row.get("ts_code") or not db_row.get("end_date"):
            continue
        db_row["payload_json"] = json.dumps(row, ensure_ascii=False, default=str)
        db_row["source"] = "tushare"
        db_row["created_at"] = now
        db_row["updated_at"] = now
        db_rows.append(db_row)

    if not db_rows:
        return 0

    all_cols = list(db_rows[0].keys())
    placeholders = ", ".join(["?"] * len(all_cols))
    columns_sql = ", ".join(all_cols)
    conflict_sql = ", ".join(unique_cols)
    update_cols = [c for c in all_cols if c not in unique_cols + ["created_at"]]
    update_sql = ", ".join([f"{c} = excluded.{c}" for c in update_cols])

    sql = (
        f"INSERT INTO cashflow ({columns_sql}) "
        f"VALUES ({placeholders}) "
        f"ON CONFLICT({conflict_sql}) DO UPDATE SET {update_sql}"
    )
    values = [[r.get(col) for col in all_cols] for r in db_rows]

    try:
        conn.executemany(sql, values)
        conn.commit()
        return len(db_rows)
    except Exception:
        conn.rollback()
        raise


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--init", action="store_true", help="初始化表结构")
    args = parser.parse_args()
    if args.init:
        init_table()
        print("表结构初始化完成")
