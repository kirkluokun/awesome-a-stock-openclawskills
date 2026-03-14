import json
import os
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from threading import Lock

import pandas as pd
import tushare as ts
from dotenv import load_dotenv
from fetchers._shared.env import load_env_auto

# 全局锁，用于 SQLite 写入
_db_lock = Lock()


def now_ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def init_tushare(env_path: Path):
    load_env_auto(env_path)
    api_key = os.getenv("TUSHARE_API_KEY")
    if not api_key:
        raise RuntimeError("未找到 TUSHARE_API_KEY")
    return ts.pro_api(api_key)


def load_codes(csv_path: Path):
    df = pd.read_csv(csv_path, dtype=str)
    if "ts_code" not in df.columns:
        raise ValueError("stock_basic_codes.csv 缺少 ts_code 列")
    return [c for c in df["ts_code"].dropna().astype(str).tolist() if c]


def load_schema(schema_path: Path):
    return schema_path.read_text(encoding="utf-8")


def connect_db(db_path: Path, schema_path: Path):
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    schema = load_schema(schema_path)
    conn.executescript(schema)
    conn.commit()
    return conn


def fetch_report_rc(pro, ts_code: str, start_date: str, end_date: str, limit: int):
    df = pro.report_rc(ts_code=ts_code, start_date=start_date, end_date=end_date, limit=limit)
    return df if df is not None else pd.DataFrame()


def fetch_existing(conn: sqlite3.Connection, row: dict):
    sql = (
        "SELECT * FROM report_rc WHERE ts_code = ? AND report_date = ? AND org_name = ? AND period = ? LIMIT 1"
    )
    values = [row.get("ts_code"), row.get("report_date"), row.get("org_name"), row.get("period")]
    cur = conn.execute(sql, values)
    result = cur.fetchone()
    return dict(result) if result else None


def safe_value(value):
    if pd.isna(value):
        return None
    return value


def build_change_log(existing: dict, new_row: dict):
    if not existing:
        return "new", None
    old = safe_value(existing.get("np"))
    new = safe_value(new_row.get("np"))
    if old is None or new is None:
        return "same", None
    if old == new:
        return "same", None
    return "update", json.dumps({"np": {"old": old, "new": new}}, ensure_ascii=True, sort_keys=True)


def normalize_rows(df: pd.DataFrame):
    rows = []
    ts_now = now_ts()
    for _, row in df.iterrows():
        row_dict = {k: safe_value(v) for k, v in row.to_dict().items()}
        new_row = {
            "ts_code": row_dict.get("ts_code"),
            "report_date": row_dict.get("report_date"),
            "org_name": row_dict.get("org_name"),
            "period": row_dict.get("quarter"),
            "np": row_dict.get("np"),
            "eps": row_dict.get("eps"),
            "quarter": row_dict.get("quarter"),
            "source": "report_rc",
            "payload_json": json.dumps(row_dict, ensure_ascii=True, sort_keys=True),
            "created_at": ts_now,
            "updated_at": ts_now,
        }
        rows.append(new_row)
    return rows


def upsert_rows(conn: sqlite3.Connection, rows: list):
    if not rows:
        return 0
    cols = list(rows[0].keys())
    placeholders = ", ".join(["?"] * len(cols))
    columns_sql = ", ".join(cols)
    conflict_sql = "ts_code, report_date, org_name, period"
    update_cols = [c for c in cols if c not in ["ts_code", "report_date", "org_name", "period", "created_at"]]
    update_sql = ", ".join([f"{c} = excluded.{c}" for c in update_cols])
    sql = (
        f"INSERT INTO report_rc ({columns_sql}) VALUES ({placeholders}) "
        f"ON CONFLICT({conflict_sql}) DO UPDATE SET {update_sql}"
    )
    values = [[row.get(col) for col in cols] for row in rows]
    with _db_lock:
        conn.executemany(sql, values)
        conn.commit()
    return len(rows)


def insert_report_rc(conn: sqlite3.Connection, df: pd.DataFrame):
    rows = normalize_rows(df)
    for row in rows:
        existing = fetch_existing(conn, row)
        change_type, change_log = build_change_log(existing, row)
        row["change_type"] = change_type
        row["change_log"] = change_log
    return upsert_rows(conn, rows)


def delete_code_records(conn: sqlite3.Connection, ts_code: str, start_date: str, end_date: str):
    """删除指定代码在日期范围内的所有记录"""
    sql = "DELETE FROM report_rc WHERE ts_code = ? AND report_date >= ? AND report_date <= ?"
    with _db_lock:
        conn.execute(sql, [ts_code, start_date, end_date])
        conn.commit()


def fetch_code_with_fallback(conn, pro, ts_code: str, start_date: str, mid_date: str, end_date: str, limit: int):
    df = fetch_report_rc(pro, ts_code, start_date, end_date, limit)
    if len(df) < limit:
        # 数据完整，直接入库
        return insert_report_rc(conn, df)
    # 触发 fallback：先删除第一次拉取的不完整数据，再分两段拉
    delete_code_records(conn, ts_code, start_date, end_date)
    df2 = fetch_report_rc(pro, ts_code, mid_date, end_date, limit)
    inserted = insert_report_rc(conn, df2)
    df3 = fetch_report_rc(pro, ts_code, start_date, prev_date(mid_date), limit)
    inserted += insert_report_rc(conn, df3)
    return inserted


def prev_date(date_str: str):
    dt = datetime.strptime(date_str, "%Y%m%d")
    return (dt - pd.Timedelta(days=1)).strftime("%Y%m%d")


def load_checkpoint(path: Path):
    if not path.exists():
        return {"index": 0}
    return json.loads(path.read_text(encoding="utf-8"))


def save_checkpoint(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=True, indent=2), encoding="utf-8")


def run_batch(
    codes: list,
    conn: sqlite3.Connection,
    pro,
    start_date: str,
    mid_date: str,
    end_date: str,
    limit: int,
    batch_size: int,
    checkpoint_path: Path,
    max_workers: int = 10,
):
    checkpoint = load_checkpoint(checkpoint_path)
    start_index = int(checkpoint.get("index", 0))
    end_index = min(start_index + batch_size, len(codes))
    batch_codes = codes[start_index:end_index]

    def process_one(ts_code: str):
        return ts_code, fetch_code_with_fallback(conn, pro, ts_code, start_date, mid_date, end_date, limit)

    processed = start_index
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_one, code): code for code in batch_codes}
        for future in as_completed(futures):
            ts_code = futures[future]
            try:
                future.result()
            except Exception as e:
                print(f"[ERROR] {ts_code}: {e}")
            processed += 1
            checkpoint = {
                "index": processed,
                "total": len(codes),
                "last_ts_code": ts_code,
                "start_date": start_date,
                "end_date": end_date,
                "mid_date": mid_date,
                "updated_at": now_ts(),
            }
            save_checkpoint(checkpoint_path, checkpoint)
    return checkpoint
