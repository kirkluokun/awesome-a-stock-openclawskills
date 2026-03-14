"""从 Tushare 拉取主营业务构成数据"""

import sys
from pathlib import Path

from dotenv import load_dotenv
from fetchers._shared.env import load_env_auto

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from analyzers.fina_mainbz._shared.db import connect, upsert_fina_mainbz, init_table

# 先加载 .env（finance_basic.py 模块级会用到 TUSHARE_API_KEY）
load_env_auto(PROJECT_ROOT)

from fetchers.finance_basic import fetch_fina_mainbz, fetch_fina_mainbz_vip


def fetch_and_save(
    ts_code: str = None,
    period: str = None,
    type_: str = None,
    start_date: str = None,
    end_date: str = None,
    use_vip: bool = False,
) -> int:
    if use_vip and not period:
        raise ValueError("使用VIP接口时必须提供 period 参数")
    conn = connect()
    try:
        init_table(conn)
        if use_vip:
            df = fetch_fina_mainbz_vip(
                ts_code=ts_code,
                period=period,
                type_=type_,
                start_date=start_date,
                end_date=end_date,
            )
        else:
            if not ts_code:
                raise ValueError("普通接口必须提供 ts_code 参数")
            df = fetch_fina_mainbz(
                ts_code=ts_code,
                period=period,
                type_=type_,
                start_date=start_date,
                end_date=end_date,
            )
        if df is None or df.empty:
            return 0
        rows = df.to_dict("records")
        return upsert_fina_mainbz(conn, rows)
    finally:
        conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="拉取主营业务构成数据")
    parser.add_argument("--ts-code", help="股票代码（普通接口必填）")
    parser.add_argument("--period", help="报告期 YYYYMMDD")
    parser.add_argument("--type", dest="type_", choices=["P", "D", "I"], help="类型：P按产品 D按地区 I按行业")
    parser.add_argument("--start-date", help="报告期开始日期")
    parser.add_argument("--end-date", help="报告期结束日期")
    parser.add_argument("--vip", action="store_true", help="使用VIP接口（全量拉取，需5000积分）")
    args = parser.parse_args()

    if args.vip and not args.period:
        parser.error("使用VIP接口时必须提供 --period 参数")
    if not args.vip and not args.ts_code:
        parser.error("普通接口必须提供 --ts-code 参数")

    count = fetch_and_save(
        ts_code=args.ts_code,
        period=args.period,
        type_=args.type_,
        start_date=args.start_date,
        end_date=args.end_date,
        use_vip=args.vip,
    )
    print(f"保存 {count} 条记录")
