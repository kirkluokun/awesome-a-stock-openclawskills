#!/usr/bin/env python3
"""
数据拉取与入库
"""

import argparse
import json
import os
from datetime import datetime
from pathlib import Path

import pandas as pd
import tushare as ts
from dotenv import load_dotenv

from db import connect, run_migrations, fetch_existing, upsert_rows


def load_env(env_path: str = None):
    """加载 .env"""
    if env_path:
        load_dotenv(env_path)
        return

    for parent in Path(__file__).resolve().parents:
        candidate = parent / ".env"
        if candidate.exists():
            load_dotenv(candidate)
            return


def init_tushare(env_path: str = None):
    """初始化 Tushare"""
    load_env(env_path)
    api_key = os.getenv("TUSHARE_API_KEY")
    if not api_key:
        raise RuntimeError("未找到 TUSHARE_API_KEY")
    return ts.pro_api(api_key)


def now_ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_periods_for_date(date_str: str) -> list:
    """根据日期自动计算需要拉取的 period 列表
    
    规则：
    - 1月1日 - 4月30日：上年Q4(1231) + 当年Q1(0331)
    - 5月1日 - 8月31日：当年Q2(0630)
    - 9月1日 - 10月31日：当年Q3(0930)
    - 11月1日 - 12月31日：当年Q4(1231) 预披露
    """
    dt = datetime.strptime(date_str, "%Y%m%d")
    year = dt.year
    month = dt.month
    
    periods = []
    
    if 1 <= month <= 4:
        # 年报 + Q1 披露季
        periods.append(f"{year - 1}1231")  # 上年年报
        periods.append(f"{year}0331")       # 当年Q1
    elif 5 <= month <= 8:
        # 中报披露季
        periods.append(f"{year}0630")
    elif 9 <= month <= 10:
        # Q3 披露季
        periods.append(f"{year}0930")
    else:  # 11-12月
        # 年报预披露期
        periods.append(f"{year}1231")
    
    return periods


def safe_value(value):
    if pd.isna(value):
        return None
    return value


def to_payload(row: dict):
    return json.dumps(row, ensure_ascii=True, sort_keys=True)


def build_change_log(existing: dict, new_row: dict, fields: list):
    if not existing:
        return "new", None

    changes = {}
    for field in fields:
        old = existing.get(field)
        new = new_row.get(field)
        if old != new:
            changes[field] = {"old": old, "new": new}

    if not changes:
        return "same", None

    return "update", json.dumps(changes, ensure_ascii=True, sort_keys=True)


def normalize_rows(df: pd.DataFrame, base_map: dict, source: str, existing_fetcher=None, change_fields=None):
    rows = []
    ts_now = now_ts()

    for _, row in df.iterrows():
        row_dict = {k: safe_value(v) for k, v in row.to_dict().items()}
        new_row = {col: safe_value(row_dict.get(src)) for col, src in base_map.items()}
        new_row["source"] = source
        new_row["payload_json"] = to_payload(row_dict)
        new_row["updated_at"] = ts_now
        new_row["created_at"] = ts_now

        if existing_fetcher and change_fields:
            existing = existing_fetcher(new_row)
            change_type, change_log = build_change_log(existing, new_row, change_fields)
            new_row["change_type"] = change_type
            new_row["change_log"] = change_log
        rows.append(new_row)

    return rows


def fetch_report_rc_full(pro, report_date: str):
    return pro.report_rc(report_date=report_date)


def fetch_forecast_by_periods(pro, periods: list, use_vip: bool):
    """按 period 列表拉取业绩预告"""
    dfs = []
    for period in periods:
        if use_vip:
            df = pro.forecast_vip(period=period)
        else:
            df = pro.forecast(period=period)
        if df is not None and not df.empty:
            print(f"  forecast period={period}: {len(df)} 条")
            dfs.append(df)
    if not dfs:
        return pd.DataFrame()
    return pd.concat(dfs, ignore_index=True).drop_duplicates()


def fetch_express_by_periods(pro, periods: list, use_vip: bool):
    """按 period 列表拉取业绩快报"""
    dfs = []
    for period in periods:
        if use_vip:
            df = pro.express_vip(period=period)
        else:
            df = pro.express(period=period)
        if df is not None and not df.empty:
            print(f"  express period={period}: {len(df)} 条")
            dfs.append(df)
    if not dfs:
        return pd.DataFrame()
    return pd.concat(dfs, ignore_index=True).drop_duplicates()


def fetch_income_by_periods(pro, periods: list, use_vip: bool):
    """按 period 列表拉取正式业绩"""
    dfs = []
    for period in periods:
        if use_vip:
            df = pro.income_vip(period=period)
        else:
            df = pro.income(period=period)
        if df is not None and not df.empty:
            print(f"  income period={period}: {len(df)} 条")
            dfs.append(df)
    if not dfs:
        return pd.DataFrame()
    return pd.concat(dfs, ignore_index=True).drop_duplicates()


def fetch_disclosure_full(pro, date_str: str):
    dfs = []
    for key in ["ann_date", "pre_date", "actual_date"]:
        df = pro.disclosure_date(**{key: date_str})
        if df is not None and not df.empty:
            dfs.append(df)
    if not dfs:
        return pd.DataFrame()
    return pd.concat(dfs, ignore_index=True).drop_duplicates()


def main():
    parser = argparse.ArgumentParser(description="数据拉取与入库")
    parser.add_argument("--date", help="日期 (YYYYMMDD)，默认今天")
    parser.add_argument("--dry-run", action="store_true", help="只统计不入库")
    parser.add_argument("--no-vip", action="store_true", help="不使用 VIP 接口")
    parser.add_argument("--env-path", help="指定 .env 路径")
    parser.add_argument("--report-rc-file", help="使用本地 report_rc CSV 文件进行模拟")
    parser.add_argument("--forecast-file", help="使用本地 forecast CSV 文件进行模拟")
    parser.add_argument("--express-file", help="使用本地 express CSV 文件进行模拟")
    parser.add_argument("--income-file", help="使用本地 income CSV 文件进行模拟")
    parser.add_argument("--disclosure-file", help="使用本地 disclosure_date CSV 文件进行模拟")
    parser.add_argument("--only-report-rc", action="store_true", help="只处理 report_rc")
    args = parser.parse_args()

    date_str = args.date or datetime.now().strftime("%Y%m%d")
    use_vip = not args.no_vip
    
    # 根据日期自动计算需要拉取的 period
    periods = get_periods_for_date(date_str)
    print(f"日期: {date_str}")
    print(f"自动 period: {periods}")

    need_api = True
    if args.only_report_rc and args.report_rc_file:
        need_api = False
    if args.report_rc_file and args.forecast_file and args.express_file and args.income_file and args.disclosure_file:
        need_api = False

    pro = None if not need_api else init_tushare(args.env_path)
    conn = connect()
    run_migrations(conn)

    def existing_fetcher_factory(table, unique_cols):
        def _fetch(row):
            return fetch_existing(conn, table, unique_cols, row)
        return _fetch

    counts = {}

    # report_rc
    if args.report_rc_file:
        df_report = pd.read_csv(args.report_rc_file)
        if "report_date" in df_report.columns:
            df_report = df_report[df_report["report_date"].astype(str) == date_str]
    else:
        df_report = fetch_report_rc_full(pro, date_str)
    report_base = {
        "ts_code": "ts_code",
        "report_date": "report_date",
        "org_name": "org_name",
        "period": "quarter",
        "np": "np",
        "eps": "eps",
        "quarter": "quarter",
    }
    report_rows = normalize_rows(
        df_report,
        report_base,
        "report_rc",
        existing_fetcher_factory("report_rc", ["ts_code", "report_date", "org_name", "period"]),
        ["np"]
    )
    counts["report_rc"] = len(report_rows)
    if not args.dry_run and report_rows:
        upsert_rows(conn, "report_rc", report_rows, ["ts_code", "report_date", "org_name", "period"])

    if args.only_report_rc:
        df_forecast = pd.DataFrame()
    elif args.forecast_file:
        df_forecast = pd.read_csv(args.forecast_file)
        if "ann_date" in df_forecast.columns:
            df_forecast = df_forecast[df_forecast["ann_date"].astype(str) == date_str]
    else:
        print("拉取 forecast...")
        df_forecast = fetch_forecast_by_periods(pro, periods, use_vip)
    forecast_base = {
        "ts_code": "ts_code",
        "ann_date": "ann_date",
        "end_date": "end_date",
        "net_profit_min": "net_profit_min",
        "net_profit_max": "net_profit_max",
        "type": "type",
    }
    forecast_rows = normalize_rows(
        df_forecast,
        forecast_base,
        "forecast",
        existing_fetcher_factory("forecast", ["ts_code", "ann_date", "end_date"]),
        ["net_profit_min", "net_profit_max"]
    )
    counts["forecast"] = len(forecast_rows)
    if not args.dry_run and forecast_rows:
        upsert_rows(conn, "forecast", forecast_rows, ["ts_code", "ann_date", "end_date"])

    if args.only_report_rc:
        df_express = pd.DataFrame()
    elif args.express_file:
        df_express = pd.read_csv(args.express_file)
        if "ann_date" in df_express.columns:
            df_express = df_express[df_express["ann_date"].astype(str) == date_str]
    else:
        print("拉取 express...")
        df_express = fetch_express_by_periods(pro, periods, use_vip)
    express_base = {
        "ts_code": "ts_code",
        "ann_date": "ann_date",
        "end_date": "end_date",
        "n_income": "n_income",
    }
    express_rows = normalize_rows(
        df_express,
        express_base,
        "express",
        existing_fetcher_factory("express", ["ts_code", "ann_date", "end_date"]),
        ["n_income"]
    )
    counts["express"] = len(express_rows)
    if not args.dry_run and express_rows:
        upsert_rows(conn, "express", express_rows, ["ts_code", "ann_date", "end_date"])

    if args.only_report_rc:
        df_income = pd.DataFrame()
    elif args.income_file:
        df_income = pd.read_csv(args.income_file)
        if "ann_date" in df_income.columns:
            df_income = df_income[df_income["ann_date"].astype(str) == date_str]
    else:
        print("拉取 income...")
        df_income = fetch_income_by_periods(pro, periods, use_vip)
    income_base = {
        "ts_code": "ts_code",
        "ann_date": "ann_date",
        "end_date": "end_date",
        "n_income": "n_income",
        "report_type": "report_type",
        "comp_type": "comp_type",
    }
    income_rows = normalize_rows(
        df_income,
        income_base,
        "income",
        existing_fetcher_factory("income", ["ts_code", "ann_date", "end_date"]),
        ["n_income"]
    )
    counts["income"] = len(income_rows)
    if not args.dry_run and income_rows:
        upsert_rows(conn, "income", income_rows, ["ts_code", "ann_date", "end_date"])

    if args.only_report_rc:
        df_disclosure = pd.DataFrame()
    elif args.disclosure_file:
        df_disclosure = pd.read_csv(args.disclosure_file)
        date_cols = [c for c in ["ann_date", "pre_date", "actual_date"] if c in df_disclosure.columns]
        if date_cols:
            mask = False
            for col in date_cols:
                mask = mask | (df_disclosure[col].astype(str) == date_str)
            df_disclosure = df_disclosure[mask]
    else:
        df_disclosure = fetch_disclosure_full(pro, date_str)
    disclosure_base = {
        "ts_code": "ts_code",
        "end_date": "end_date",
        "pre_date": "pre_date",
        "ann_date": "ann_date",
        "actual_date": "actual_date",
    }
    disclosure_rows = normalize_rows(
        df_disclosure,
        disclosure_base,
        "disclosure_date",
        existing_fetcher_factory("disclosure_date", ["ts_code", "end_date"]),
        ["pre_date", "ann_date", "actual_date"]
    )
    counts["disclosure_date"] = len(disclosure_rows)
    if not args.dry_run and disclosure_rows:
        upsert_rows(conn, "disclosure_date", disclosure_rows, ["ts_code", "end_date"])

    conn.close()

    print(f"日期: {date_str}")
    print(f"使用VIP: {use_vip}")
    for key, value in counts.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
