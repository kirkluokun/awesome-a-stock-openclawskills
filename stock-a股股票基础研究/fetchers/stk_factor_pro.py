"""从 Tushare 拉取股票技术面因子数据（专业版）"""

import sys
from pathlib import Path

from dotenv import load_dotenv
from fetchers._shared.env import load_env_auto

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

# 加载 .env
load_env_auto(PROJECT_ROOT)

from analyzers.stk_factor._shared.db import connect, upsert_stk_factor, init_table
from fetchers.finance_basic import fetch_stk_factor_pro


def fetch_and_save(
    ts_code: str = None,
    trade_date: str = None,
    start_date: str = None,
    end_date: str = None,
) -> int:
    conn = connect()
    try:
        init_table(conn)
        df = fetch_stk_factor_pro(
            ts_code=ts_code,
            trade_date=trade_date,
            start_date=start_date,
            end_date=end_date,
        )
        if df is None or df.empty:
            return 0
        rows = df.to_dict("records")
        return upsert_stk_factor(conn, rows)
    finally:
        conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="拉取股票技术面因子数据")
    parser.add_argument("--ts-code", help="股票代码")
    parser.add_argument("--trade-date", help="交易日期 YYYYMMDD")
    parser.add_argument("--start-date", help="开始日期 YYYYMMDD")
    parser.add_argument("--end-date", help="结束日期 YYYYMMDD")
    args = parser.parse_args()

    count = fetch_and_save(
        ts_code=args.ts_code,
        trade_date=args.trade_date,
        start_date=args.start_date,
        end_date=args.end_date,
    )
    print(f"保存 {count} 条记录")
