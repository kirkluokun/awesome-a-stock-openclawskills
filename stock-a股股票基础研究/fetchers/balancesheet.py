# fetchers/balancesheet.py
"""从 Tushare 拉取资产负债表数据"""

import os
import sys
import time
from pathlib import Path

import pandas as pd
import tushare as ts
from dotenv import load_dotenv
from fetchers._shared.env import load_env_auto

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from analyzers.balancesheet._shared.db import connect, upsert_balancesheet, init_table
from fetchers.finance_basic import fetch_balancesheet, fetch_balancesheet_vip

load_env_auto(PROJECT_ROOT)

TUSHARE_API_KEY = os.getenv("TUSHARE_API_KEY")


def get_pro():
    """获取 Tushare API 实例"""
    if not TUSHARE_API_KEY:
        raise ValueError("TUSHARE_API_KEY environment variable not set")
    ts.set_token(TUSHARE_API_KEY)
    return ts.pro_api()


def fetch_and_save(
    ts_code: str = None,
    ann_date: str = None,
    start_date: str = None,
    end_date: str = None,
    period: str = None,
    report_type: str = None,
    comp_type: str = None,
    use_vip: bool = False,
) -> int:
    """
    拉取资产负债表数据并保存到数据库
    
    Args:
        ts_code: 股票代码
        ann_date: 公告日期
        start_date: 开始日期
        end_date: 结束日期
        period: 报告期（YYYYMMDD）
        report_type: 报表类型
        comp_type: 公司类型
        use_vip: 是否使用VIP接口（全量拉取）
        
    Returns:
        保存的记录数
    """
    # 确保表已创建
    conn = connect()
    try:
        init_table(conn)
        
        # 调用API
        if use_vip and period:
            df = fetch_balancesheet_vip(
                period=period,
                report_type=report_type,
                comp_type=comp_type
            )
        else:
            df = fetch_balancesheet(
                ts_code=ts_code,
                ann_date=ann_date,
                start_date=start_date,
                end_date=end_date,
                period=period,
                report_type=report_type,
                comp_type=comp_type
            )
        
        if df is None or df.empty:
            return 0
        
        # 转换为字典列表
        rows = df.to_dict('records')
        
        # 入库
        count = upsert_balancesheet(conn, rows)
        return count
        
    except Exception as e:
        print(f"拉取失败: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="拉取资产负债表数据")
    parser.add_argument("--ts-code", help="股票代码")
    parser.add_argument("--start-date", help="开始日期 YYYYMMDD")
    parser.add_argument("--end-date", help="结束日期 YYYYMMDD")
    parser.add_argument("--period", help="报告期 YYYYMMDD")
    parser.add_argument("--report-type", help="报表类型")
    parser.add_argument("--comp-type", help="公司类型")
    parser.add_argument("--vip", action="store_true", help="使用VIP接口")
    
    args = parser.parse_args()
    
    count = fetch_and_save(
        ts_code=args.ts_code,
        start_date=args.start_date,
        end_date=args.end_date,
        period=args.period,
        report_type=args.report_type,
        comp_type=args.comp_type,
        use_vip=args.vip
    )
    
    print(f"保存 {count} 条记录")
