import time
from datetime import datetime, timedelta

from fetch_report_rc import fetch_by_date_range, save_to_csv


def parse_date(value: str) -> datetime:
    return datetime.strptime(value, "%Y%m%d")


def format_date(dt: datetime) -> str:
    return dt.strftime("%Y%m%d")


def fetch_window(start_date: str, end_date: str, limit: int):
    df = fetch_by_date_range(start_date, end_date, limit=limit)
    if not df.empty:
        filename = f"report_rc_{start_date}_{end_date}.csv"
        save_to_csv(df, filename)
    return len(df)


def run_batch(
    start_date: str,
    stop_date: str,
    window_days: int = 3,
    fallback_days: int = 2,
    min_days: int = 1,
    limit: int = 3000,
    sleep_seconds: int = 32,
):
    end_dt = parse_date(start_date)
    stop_dt = parse_date(stop_date)

    while end_dt >= stop_dt:
        start_dt = end_dt - timedelta(days=window_days - 1)
        if start_dt < stop_dt:
            start_dt = stop_dt
        start_str = format_date(start_dt)
        end_str = format_date(end_dt)

        count = fetch_window(start_str, end_str, limit)

        if count >= limit and window_days > fallback_days:
            fallback_start = end_dt - timedelta(days=fallback_days - 1)
            if fallback_start < stop_dt:
                fallback_start = stop_dt
            fallback_start_str = format_date(fallback_start)
            fallback_end_str = end_str
            count = fetch_window(fallback_start_str, fallback_end_str, limit)
            if count >= limit and fallback_days > min_days:
                one_day_start = end_dt
                one_day_end_str = end_str
                one_day_start_str = format_date(one_day_start)
                fetch_window(one_day_start_str, one_day_end_str, limit)
                end_dt = end_dt - timedelta(days=min_days)
            else:
                end_dt = end_dt - timedelta(days=fallback_days)
        else:
            end_dt = start_dt - timedelta(days=1)

        if end_dt >= stop_dt:
            time.sleep(sleep_seconds)
