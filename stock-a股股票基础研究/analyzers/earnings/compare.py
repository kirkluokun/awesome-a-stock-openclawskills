#!/usr/bin/env python3
"""
对比实际业绩与市场预期，生成告警
"""

import argparse
import json
from datetime import datetime

import pandas as pd

from db import connect, run_migrations, upsert_rows


def now_ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def safe_ratio(actual, expected):
    if expected is None:
        return None
    if expected == 0:
        return None
    return (actual - expected) / abs(expected)


def load_table(conn, sql):
    return pd.read_sql_query(sql, conn)


def load_table_with_columns(conn, table, columns):
    info = pd.read_sql_query(f"PRAGMA table_info({table})", conn)
    available = set(info["name"].tolist())
    selected = [col for col in columns if col in available]
    if not selected:
        return pd.DataFrame(columns=columns)
    sql = f"SELECT {', '.join(selected)} FROM {table}"
    df = pd.read_sql_query(sql, conn)
    for col in columns:
        if col not in df.columns:
            df[col] = None
    return df


def build_expectations(conn, actuals):
    df = load_table(
        conn,
        """
        SELECT ts_code, period, report_date, np
        FROM report_rc
        WHERE np IS NOT NULL
        """
    )
    if df.empty or actuals.empty:
        return pd.DataFrame()

    df["period"] = df["period"].fillna(df["report_date"])
    df = df.dropna(subset=["period", "report_date"])
    df["period"] = df["period"].astype(str).apply(normalize_quarter_label)
    df["report_date"] = df["report_date"].astype(str)

    actuals = actuals.copy()
    actuals["period"] = actuals["period"].astype(str).apply(normalize_quarter_label)
    actuals["ann_date"] = actuals["ann_date"].astype(str)

    merged = actuals.merge(
        df,
        on=["ts_code", "period"],
        how="left"
    )
    merged["report_date_dt"] = pd.to_datetime(merged["report_date"], errors="coerce")
    merged["ann_date_dt"] = pd.to_datetime(merged["ann_date"], errors="coerce")
    merged = merged.dropna(subset=["report_date_dt", "ann_date_dt"])
    merged = merged[merged["report_date_dt"] < merged["ann_date_dt"]]
    merged = merged[merged["report_date_dt"] >= (merged["ann_date_dt"] - pd.Timedelta(days=365))]
    if merged.empty:
        return pd.DataFrame()

    agg = merged.groupby(["ts_code", "period", "ann_date"]).agg(
        expected_min=("np", "min"),
        expected_mean=("np", "mean"),
        expected_median=("np", "median"),
        expected_max=("np", "max"),
        expected_report_date_min=("report_date", "min"),
        expected_report_date_max=("report_date", "max"),
    ).reset_index()
    return agg


def latest_by_group(df, group_cols, order_col):
    if df.empty:
        return df
    df = df.sort_values(order_col, ascending=False)
    return df.groupby(group_cols, as_index=False).first()


def annualize_factor(end_date: str):
    if not end_date:
        return 1.0
    end_date = str(end_date)
    suffix = end_date[-4:]
    if suffix == "0331":
        return 4.0
    if suffix == "0630":
        return 2.0
    if suffix == "0930":
        return 4.0 / 3.0
    return 1.0


def end_date_to_annual_period(end_date: str):
    if not end_date:
        return None
    end_date = str(end_date)
    if len(end_date) < 4:
        return None
    year = end_date[:4]
    if not year.isdigit():
        return None
    return f"{year}Q4"


def normalize_quarter_label(value: str):
    if value is None:
        return value
    value = str(value)
    if "Q" in value:
        year = value[:4]
        quarter = value[-1]
        if year.isdigit() and quarter in {"1", "2", "3", "4"}:
            return f"{year}Q{quarter}"
    if len(value) == 8 and value.isdigit():
        year = value[:4]
        suffix = value[-4:]
        mapping = {"0331": "1", "0630": "2", "0930": "3", "1231": "4"}
        if suffix in mapping:
            return f"{year}Q{mapping[suffix]}"
    return value


def build_actuals(conn):
    # forecast: use avg(net_profit_min, net_profit_max)
    forecast = load_table_with_columns(
        conn,
        "forecast",
        ["ts_code", "end_date", "ann_date", "net_profit_min", "net_profit_max", "change_reason", "updated_at"]
    )
    if not forecast.empty:
        forecast["actual_value"] = (
            forecast["net_profit_min"].fillna(0) + forecast["net_profit_max"].fillna(0)
        ) / 2
        forecast = latest_by_group(forecast, ["ts_code", "end_date"], "updated_at")
        forecast["source"] = "forecast"
        forecast["reason_hint"] = forecast["change_reason"]

    # express: n_income（原单位：元，转换为万元）
    express = load_table_with_columns(
        conn,
        "express",
        ["ts_code", "end_date", "ann_date", "n_income", "perf_summary", "updated_at"]
    )
    if not express.empty:
        express = latest_by_group(express, ["ts_code", "end_date"], "updated_at")
        express["actual_value"] = express["n_income"] / 10000  # 元 → 万元
        express["source"] = "express"
        express["reason_hint"] = express["perf_summary"]

    # income: n_income（原单位：元，转换为万元）
    income = load_table_with_columns(
        conn,
        "income",
        ["ts_code", "end_date", "ann_date", "f_ann_date", "n_income", "updated_at"]
    )
    if not income.empty:
        income = latest_by_group(income, ["ts_code", "end_date"], "updated_at")
        income["actual_value"] = income["n_income"] / 10000  # 元 → 万元
        income["source"] = "income"
        income["ann_date"] = income["f_ann_date"].fillna(income["ann_date"])
        income["reason_hint"] = None

    # priority: forecast > express > income
    frames = []
    if not forecast.empty:
        frames.append(forecast[["ts_code", "end_date", "ann_date", "actual_value", "source", "reason_hint"]])
    if not express.empty:
        frames.append(express[["ts_code", "end_date", "ann_date", "actual_value", "source", "reason_hint"]])
    if not income.empty:
        frames.append(income[["ts_code", "end_date", "ann_date", "actual_value", "source", "reason_hint"]])

    if not frames:
        return pd.DataFrame()

    combined = pd.concat(frames, ignore_index=True)
    priority = {"forecast": 1, "express": 2, "income": 3}
    combined["priority"] = combined["source"].map(priority)
    combined = combined.sort_values("priority")
    combined = combined.groupby(["ts_code", "end_date"], as_index=False).first()
    combined["annualize_factor"] = combined["end_date"].apply(annualize_factor)
    combined["actual_annualized"] = combined["actual_value"] * combined["annualize_factor"]
    combined["period"] = combined["end_date"].apply(end_date_to_annual_period)
    return combined.drop(columns=["priority"])


def build_alerts(expectations, actuals):
    if expectations.empty or actuals.empty:
        return pd.DataFrame()

    merged = actuals.merge(expectations, on=["ts_code", "period", "ann_date"], how="left")
    merged = merged.dropna(subset=["expected_max", "actual_annualized"])

    # 超预期：actual > expected_max
    above = merged[merged["actual_annualized"] > merged["expected_max"]].copy()
    if not above.empty:
        above["alert_type"] = "above"

    # 低于预期：actual < expected_mean
    below = merged[merged["actual_annualized"] < merged["expected_mean"]].copy()
    if not below.empty:
        below["alert_type"] = "below"

    # 符合预期：expected_mean <= actual <= expected_max
    inline = merged[
        (merged["actual_annualized"] >= merged["expected_mean"]) &
        (merged["actual_annualized"] <= merged["expected_max"])
    ].copy()
    if not inline.empty:
        inline["alert_type"] = "inline"

    frames = [df for df in [above, below, inline] if not df.empty]
    alerts = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    if alerts.empty:
        return alerts

    alerts["delta_mean"] = alerts.apply(
        lambda r: safe_ratio(r["actual_annualized"], r["expected_mean"]), axis=1
    )
    alerts["delta_median"] = alerts.apply(
        lambda r: safe_ratio(r["actual_annualized"], r["expected_median"]), axis=1
    )
    alerts["delta_max"] = alerts.apply(
        lambda r: safe_ratio(r["actual_annualized"], r["expected_max"]), axis=1
    )
    return alerts


def main():
    parser = argparse.ArgumentParser(description="对比并生成告警")
    parser.add_argument("--dry-run", action="store_true", help="只统计不入库")
    args = parser.parse_args()

    conn = connect()
    run_migrations(conn)

    actuals = build_actuals(conn)
    expectations = build_expectations(conn, actuals)
    alerts = build_alerts(expectations, actuals)

    if not alerts.empty and not args.dry_run:
        rows = []
        ts_now = now_ts()
        for _, row in alerts.iterrows():
            payload = {
                "alert_type": row.get("alert_type"),  # above/below/inline
                "expected_min": row.get("expected_min"),
                "expected_mean": row.get("expected_mean"),
                "expected_median": row.get("expected_median"),
                "expected_max": row.get("expected_max"),
                "expected_report_date_min": row.get("expected_report_date_min"),
                "expected_report_date_max": row.get("expected_report_date_max"),
                "ann_date": row.get("ann_date"),
                "period": row.get("period"),
                "delta_mean": row.get("delta_mean"),
                "delta_median": row.get("delta_median"),
                "delta_max": row.get("delta_max"),
                "actual_original": row.get("actual_value"),
                "annualize_factor": row.get("annualize_factor"),
                "reason_hint": row.get("reason_hint"),
            }
            rows.append(
                {
                    "ts_code": row["ts_code"],
                    "end_date": row["end_date"],
                    "actual_value": row["actual_annualized"],
                    "expected_mean": row.get("expected_mean"),
                    "expected_median": row.get("expected_median"),
                    "expected_max": row.get("expected_max"),
                    "delta_mean": row.get("delta_mean"),
                    "delta_median": row.get("delta_median"),
                    "delta_max": row.get("delta_max"),
                    "source": row["source"],
                    "created_at": ts_now,
                    "payload_json": json.dumps(payload, ensure_ascii=True, sort_keys=True),
                }
            )
        upsert_rows(conn, "alerts", rows, ["ts_code", "end_date", "source", "actual_value"], preserve_on_update=["created_at"])

    conn.close()

    print(f"expectations: {len(expectations)}")
    print(f"actuals: {len(actuals)}")
    print(f"alerts: {len(alerts)}")


if __name__ == "__main__":
    main()
