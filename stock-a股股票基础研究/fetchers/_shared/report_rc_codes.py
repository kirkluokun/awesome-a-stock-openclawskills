import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd


def load_codes(csv_path: Path):
    df = pd.read_csv(csv_path, dtype=str)
    if "ts_code" not in df.columns:
        raise ValueError("stock_basic_codes.csv 缺少 ts_code 列")
    return [c for c in df["ts_code"].dropna().astype(str).tolist() if c]


def fetch_range(pro, ts_code: str, start_date: str, end_date: str, limit: int):
    df = pro.report_rc(ts_code=ts_code, start_date=start_date, end_date=end_date, limit=limit)
    return df if df is not None else pd.DataFrame()


def save_csv(df: pd.DataFrame, output_dir: Path, ts_code: str, start_date: str, end_date: str):
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"report_rc_{ts_code}_{start_date}_{end_date}.csv"
    filepath = output_dir / filename
    df.to_csv(filepath, index=False, encoding="utf-8-sig")
    return filepath


def fetch_code_ranges(pro, ts_code: str, start_date: str, end_date: str, limit: int, output_dir: Path):
    df = fetch_range(pro, ts_code, start_date, end_date, limit)
    if not df.empty:
        save_csv(df, output_dir, ts_code, start_date, end_date)
    if len(df) >= limit:
        return False
    return True


def fetch_code_with_fallback(pro, ts_code: str, start_date: str, mid_date: str, end_date: str, limit: int, output_dir: Path):
    ok = fetch_code_ranges(pro, ts_code, start_date, end_date, limit, output_dir)
    if ok:
        return
    fetch_code_ranges(pro, ts_code, mid_date, end_date, limit, output_dir)
    fetch_code_ranges(pro, ts_code, start_date, prev_date(mid_date), limit, output_dir)


def prev_date(date_str: str):
    dt = datetime.strptime(date_str, "%Y%m%d")
    return (dt - timedelta(days=1)).strftime("%Y%m%d")


def run_batch(
    pro,
    codes: list,
    start_date: str,
    mid_date: str,
    end_date: str,
    limit: int,
    output_dir: Path,
    max_workers: int = 10,
    sleep_seconds: int = 0,
):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for ts_code in codes:
            futures.append(
                executor.submit(fetch_code_with_fallback, pro, ts_code, start_date, mid_date, end_date, limit, output_dir)
            )
            if sleep_seconds:
                time.sleep(sleep_seconds)
        for future in as_completed(futures):
            future.result()
