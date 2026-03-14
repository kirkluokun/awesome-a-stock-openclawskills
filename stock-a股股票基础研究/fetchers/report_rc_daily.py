#!/usr/bin/env python3
"""
按日期拉取 report_rc 券商盈利预测，支持分页，直接入库
用于每天增量更新
"""

import argparse
import os
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import tushare as ts
from dotenv import load_dotenv
from fetchers._shared.env import load_env_auto


def init_tushare(env_path: Path):
    """初始化 Tushare API"""
    load_dotenv(env_path)
    api_key = os.getenv("TUSHARE_API_KEY")
    if not api_key:
        raise ValueError("未找到 TUSHARE_API_KEY")
    return ts.pro_api(api_key)


def connect_db(db_path: Path, schema_path: Path):
    """连接数据库并初始化表"""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    if schema_path.exists():
        schema = schema_path.read_text(encoding="utf-8")
        conn.executescript(schema)
        conn.commit()
    return conn


def fetch_by_date(pro, date: str, limit: int = 3000):
    """单日全量拉取，自动分页"""
    all_data = []
    offset = 0
    while True:
        df = pro.report_rc(report_date=date, offset=offset, limit=limit)
        if df is None or df.empty:
            break
        all_data.append(df)
        print(f"  {date} offset={offset} 获取 {len(df)} 条")
        if len(df) < limit:
            break
        offset += limit
        time.sleep(0.5)  # 避免频率限制
    
    if all_data:
        return pd.concat(all_data, ignore_index=True)
    return pd.DataFrame()


def fetch_date_range(pro, start_date: str, end_date: str, limit: int = 3000):
    """日期范围拉取，每天分页"""
    start = datetime.strptime(start_date, "%Y%m%d")
    end = datetime.strptime(end_date, "%Y%m%d")
    
    all_data = []
    current = start
    while current <= end:
        date_str = current.strftime("%Y%m%d")
        print(f"拉取 {date_str}...")
        df = fetch_by_date(pro, date_str, limit)
        if not df.empty:
            all_data.append(df)
        current += timedelta(days=1)
        time.sleep(0.5)
    
    if all_data:
        return pd.concat(all_data, ignore_index=True)
    return pd.DataFrame()


def upsert_to_db(conn, df: pd.DataFrame):
    """数据入库（upsert）
    
    表结构: ts_code, report_date, org_name, period, np, eps, quarter, source, 
            payload_json, created_at, updated_at, change_type, change_log
    唯一键: (ts_code, report_date, org_name, period)
    """
    import json
    
    if df.empty:
        return 0
    
    ts_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_count = 0
    update_count = 0
    
    for _, row in df.iterrows():
        ts_code = row.get("ts_code")
        report_date = row.get("report_date")
        org_name = row.get("org_name")
        quarter = row.get("quarter")
        np_val = row.get("np")
        eps_val = row.get("eps")
        
        # period 直接用 quarter（如 2025Q4）
        period = quarter
        
        # 构建 payload_json
        payload = {
            "name": row.get("name"),
            "report_title": row.get("report_title"),
            "report_type": row.get("report_type"),
            "classify": row.get("classify"),
            "author_name": row.get("author_name"),
            "op_rt": row.get("op_rt"),
            "op_pr": row.get("op_pr"),
            "tp": row.get("tp"),
            "pe": row.get("pe"),
            "rd": row.get("rd"),
            "roe": row.get("roe"),
            "ev_ebitda": row.get("ev_ebitda"),
            "rating": row.get("rating"),
            "max_price": row.get("max_price"),
            "min_price": row.get("min_price"),
        }
        # 清理 NaN
        payload = {k: (None if pd.isna(v) else v) for k, v in payload.items()}
        payload_json = json.dumps(payload, ensure_ascii=False)
        
        # 检查是否存在
        cur = conn.execute(
            """SELECT np FROM report_rc 
               WHERE ts_code=? AND report_date=? AND org_name=? AND period=?""",
            (ts_code, report_date, org_name, period)
        )
        existing = cur.fetchone()
        
        if existing:
            # 更新
            conn.execute(
                """UPDATE report_rc SET
                   np=?, eps=?, quarter=?, payload_json=?, updated_at=?
                   WHERE ts_code=? AND report_date=? AND org_name=? AND period=?""",
                (np_val, eps_val, quarter, payload_json, ts_now,
                 ts_code, report_date, org_name, period)
            )
            update_count += 1
        else:
            # 插入
            conn.execute(
                """INSERT INTO report_rc 
                   (ts_code, report_date, org_name, period, np, eps, quarter, 
                    source, payload_json, created_at, updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (ts_code, report_date, org_name, period, np_val, eps_val, quarter,
                 "daily", payload_json, ts_now, ts_now)
            )
            new_count += 1
    
    conn.commit()
    print(f"新增 {new_count} 条，更新 {update_count} 条")
    return new_count


def main():
    from config import DB_PATH

    parser = argparse.ArgumentParser(description="按日期拉取 report_rc（支持分页）")
    parser.add_argument("--date", help="单日拉取 (YYYYMMDD)")
    parser.add_argument("--start-date", help="开始日期 (YYYYMMDD)")
    parser.add_argument("--end-date", help="结束日期 (YYYYMMDD)")
    parser.add_argument("--days", type=int, default=1, help="往前拉取天数（默认1天）")
    parser.add_argument("--limit", type=int, default=3000, help="单次最大条数")
    parser.add_argument("--dry-run", action="store_true", help="只拉取不入库")
    args = parser.parse_args()

    env_path = load_env_auto(Path(__file__).resolve())
    schema_path = Path(__file__).parent / "earnings_pipeline" / "schema.sql"
    db_path = DB_PATH

    pro = init_tushare(env_path)

    # 确定日期范围
    if args.date:
        start_date = args.date
        end_date = args.date
    elif args.start_date and args.end_date:
        start_date = args.start_date
        end_date = args.end_date
    else:
        # 默认：前 N 天到今天
        today = datetime.now()
        end_date = today.strftime("%Y%m%d")
        start_date = (today - timedelta(days=args.days - 1)).strftime("%Y%m%d")

    print(f"日期范围: {start_date} - {end_date}")
    
    df = fetch_date_range(pro, start_date, end_date, args.limit)
    print(f"共获取 {len(df)} 条数据")

    if df.empty:
        print("无数据")
        return

    if args.dry_run:
        print("Dry run 模式，不入库")
        print(df[["ts_code", "name", "report_date", "org_name", "np"]].head(10))
        return

    conn = connect_db(db_path, schema_path)
    new_count = upsert_to_db(conn, df)
    conn.close()
    print(f"新增 {new_count} 条，更新 {len(df) - new_count} 条")


if __name__ == "__main__":
    main()
