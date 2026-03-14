"""股票技术面因子数据库工具"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from config import DB_PATH

SCHEMA_PATH = Path(__file__).parent.parent / "schema.sql"

# 提取到独立列的字段
EXTRACT_COLS = [
    "ts_code", "trade_date",
    "close", "close_hfq", "close_qfq", "pct_chg", "vol", "amount",
    "turnover_rate", "pe_ttm", "pb", "total_mv", "circ_mv",
    "macd_dif_qfq", "macd_dea_qfq", "macd_qfq",
    "kdj_k_qfq", "kdj_d_qfq", "kdj_qfq",
    "rsi_qfq_6", "rsi_qfq_12", "rsi_qfq_24",
    "boll_upper_qfq", "boll_mid_qfq", "boll_lower_qfq",
    "ma_qfq_5", "ma_qfq_10", "ma_qfq_20", "ma_qfq_60", "ma_qfq_250",
]


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


def upsert_stk_factor(conn: sqlite3.Connection, rows: list) -> int:
    if not rows:
        return 0

    unique_cols = ["ts_code", "trade_date"]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db_rows = []
    for row in rows:
        db_row = {col: row.get(col) for col in EXTRACT_COLS}
        if not db_row.get("ts_code") or not db_row.get("trade_date"):
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
        f"INSERT INTO stk_factor ({columns_sql}) "
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
