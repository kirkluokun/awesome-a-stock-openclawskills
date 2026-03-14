"""从 Tushare 拉取财务指标数据"""

import sys
from pathlib import Path

from dotenv import load_dotenv
from fetchers._shared.env import load_env_auto

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from analyzers.fina_indicator._shared.db import connect, upsert_fina_indicator, init_table
from fetchers.finance_basic import fetch_fina_indicator, fetch_fina_indicator_vip

load_env_auto(PROJECT_ROOT)


def fetch_and_save(
    ts_code: str = None,
    ann_date: str = None,
    start_date: str = None,
    end_date: str = None,
    period: str = None,
    use_vip: bool = False,
) -> int:
    if use_vip and not period:
        raise ValueError("使用VIP接口时必须提供 period 参数")
    conn = connect()
    try:
        init_table(conn)
        if use_vip:
            df = fetch_fina_indicator_vip(
                ts_code=ts_code,
                period=period,
                ann_date=ann_date,
                start_date=start_date,
                end_date=end_date,
            )
        else:
            df = fetch_fina_indicator(
                ts_code=ts_code,
                ann_date=ann_date,
                start_date=start_date,
                end_date=end_date,
                period=period,
            )
        if df is None or df.empty:
            return 0
        rows = df.to_dict("records")
        return upsert_fina_indicator(conn, rows)
    finally:
        conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="拉取财务指标数据")
    parser.add_argument("--ts-code")
    parser.add_argument("--start-date")
    parser.add_argument("--end-date")
    parser.add_argument("--period")
    parser.add_argument("--vip", action="store_true", help="使用VIP接口")
    args = parser.parse_args()

    if args.vip and not args.period:
        parser.error("使用VIP接口时必须提供 --period 参数")

    count = fetch_and_save(
        ts_code=args.ts_code,
        start_date=args.start_date,
        end_date=args.end_date,
        period=args.period,
        use_vip=args.vip,
    )
    print(f"保存 {count} 条记录")
