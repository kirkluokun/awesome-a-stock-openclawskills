# fetchers/income_vip_batch.py
"""VIP 批量刷新利润表（按季度）"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from fetchers.finance_basic import fetch_income_vip
from analyzers.earnings.db import connect, run_migrations, upsert_rows

DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
PROGRESS_FILE = DATA_DIR / "income_vip_progress.json"
PROGRESS_LOG = DATA_DIR / "income_vip_progress.log"
SAVE_EVERY = 5


def quarter_ends_between(start_date: str, end_date: str) -> list[str]:
    """生成区间内所有季度末（不超过 end_date）"""
    def to_dt(s):
        return datetime.strptime(s, "%Y%m%d")

    def quarter_end(dt):
        if dt.month <= 3:
            return datetime(dt.year, 3, 31)
        if dt.month <= 6:
            return datetime(dt.year, 6, 30)
        if dt.month <= 9:
            return datetime(dt.year, 9, 30)
        return datetime(dt.year, 12, 31)

    start = quarter_end(to_dt(start_date))
    end_dt = to_dt(end_date)
    periods = []
    cur = start
    while cur <= end_dt:
        periods.append(cur.strftime("%Y%m%d"))
        if cur.month == 3:
            cur = datetime(cur.year, 6, 30)
        elif cur.month == 6:
            cur = datetime(cur.year, 9, 30)
        elif cur.month == 9:
            cur = datetime(cur.year, 12, 31)
        else:
            cur = datetime(cur.year + 1, 3, 31)
    return periods


def load_progress() -> set:
    processed = set()
    if PROGRESS_FILE.exists():
        data = json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
        processed.update(data.get("processed", []))
    if PROGRESS_LOG.exists():
        for line in PROGRESS_LOG.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                processed.add(line)
    return processed


def append_progress(period: str):
    with PROGRESS_LOG.open("a", encoding="utf-8") as f:
        f.write(f"{period}\n")


def save_progress(processed: set):
    data = {"processed": list(processed), "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    PROGRESS_FILE.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def normalize_income_rows(df: pd.DataFrame) -> list[dict]:
    if df is None or df.empty:
        return []
    rows = []
    ts_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for _, row in df.iterrows():
        row_dict = row.to_dict()
        new_row = {
            "ts_code": row_dict.get("ts_code"),
            "ann_date": row_dict.get("ann_date"),
            "end_date": row_dict.get("end_date"),
            "n_income": row_dict.get("n_income"),
            "report_type": row_dict.get("report_type"),
            "comp_type": row_dict.get("comp_type"),
            "source": "income",
            "payload_json": json.dumps(row_dict, ensure_ascii=False, default=str),
            "created_at": ts_now,
            "updated_at": ts_now,
            "change_type": None,
            "change_log": None,
        }
        if not new_row["ts_code"] or not new_row["end_date"]:
            continue
        rows.append(new_row)
    return rows


def run_vip(start_date: str, end_date: str, delay: float = 1.0, resume: bool = True):
    periods = quarter_ends_between(start_date, end_date)
    processed = load_progress() if resume else set()
    remaining = [p for p in periods if p not in processed]
    print(f"共 {len(periods)} 个季度，剩余 {len(remaining)} 个待拉取")

    conn = connect()
    run_migrations(conn)
    try:
        for idx, period in enumerate(remaining, 1):
            print(f"[{idx}/{len(remaining)}] 拉取 {period}")
            try:
                df = fetch_income_vip(period=period)
                rows = normalize_income_rows(df)
                count = upsert_rows(conn, "income", rows, ["ts_code", "ann_date", "end_date"])
                print(f"  ✓ 保存 {count} 条")
                processed.add(period)
                append_progress(period)
            except Exception as e:
                print(f"  ✗ 失败：{e}")
            if idx % SAVE_EVERY == 0:
                save_progress(processed)
            time.sleep(delay)
    finally:
        conn.close()

    save_progress(processed)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="VIP 批量刷新利润表")
    parser.add_argument("--start-date", required=True)
    parser.add_argument("--end-date", required=True)
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--no-resume", action="store_true")
    args = parser.parse_args()

    run_vip(args.start_date, args.end_date, args.delay, resume=not args.no_resume)
